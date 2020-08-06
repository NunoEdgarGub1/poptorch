// Copyright (c) 2020 Graphcore Ltd. All rights reserved.
#include "PopartCanonicalizationUtils.hpp"

#include <functional>
#include <numeric>
#include <string>
#include <unordered_map>

#include "../PoptorchSymbols.hpp"
#include "poptorch/OpBuilder.hpp"
#include "poptorch_logging/Error.hpp"
#include "poptorch_logging/Logging.hpp"

namespace poptorch {

namespace {

const c10::Symbol delete_node_attr =
    c10::Symbol::fromQualString("attr::delete_node");

// This avoids the static initialisation order fiasco,
std::unordered_map<c10::Symbol, SymbolHandler> &symbolHandlers() {
  static std::unordered_map<c10::Symbol, SymbolHandler> symbol_handlers;
  return symbol_handlers;
}

/*
 * Helper structs to help deduce the attribute types.
 */

template <typename T> struct Handle {
  template <std::enable_if_t<std::is_integral<T>::value, int> = 0>
  std::optional<T> operator()(const c10::Symbol &sym, torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::i) {
      return node->i(sym);
    }
    if (node->kindOf(sym) == torch::jit::AttributeKind::t) {
      // Sometimes a single long constant is encoded as an at::Tensor.
      const at::Tensor &tensor = node->t(sym);

      if (tensor.sizes().empty()) {
        // Cast tensor to correct value.
        T value = *static_cast<T *>(tensor.data_ptr());
        return value;
      }
    }

    return std::nullopt;
  }
};

template <> struct Handle<float> {
  std::optional<float> operator()(const c10::Symbol &sym,
                                  torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::f) {
      return node->f(sym);
    }
    if (node->kindOf(sym) == torch::jit::AttributeKind::t) {
      const at::Tensor &value = node->t(sym);
      return *value.data_ptr<float>();
    }
    return std::nullopt;
  }
};

template <> struct Handle<double> {
  std::optional<float> operator()(const c10::Symbol &sym,
                                  torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::f) {
      return node->f(sym);
    }
    if (node->kindOf(sym) == torch::jit::AttributeKind::t) {
      const at::Tensor &value = node->t(sym);
      return *value.data_ptr<double>();
    }
    return std::nullopt;
  }
};

template <> struct Handle<std::vector<std::int64_t>> {
  std::optional<std::vector<std::int64_t>> operator()(const c10::Symbol &sym,
                                                      torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::is) {
      return node->is(sym);
    }
    return std::nullopt;
  }
};

template <> struct Handle<std::vector<double>> {
  std::optional<std::vector<double>> operator()(const c10::Symbol &sym,
                                                torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::fs) {
      return node->fs(sym);
    }
    return std::nullopt;
  }
};

template <> struct Handle<std::string> {
  std::optional<std::string> operator()(const c10::Symbol &sym,
                                        torch::jit::Node *node) {
    if (node->kindOf(sym) == torch::jit::AttributeKind::s) {
      return node->s(sym);
    }

    return std::nullopt;
  }
};

// Return true if we know how to fold a given compile time constant operation.
// Only allow const folding for scalar poptorch::int_constant nodes
bool canBeConstFolded(torch::jit::Node *node) {
  if (node->kind() != symbols::poptorch::int_constant ||
      !node->hasAttribute(c10::attr::shape) ||
      !node->hasAttribute(c10::attr::data)) {
    return false;
  }
  // Use the shape to determine the total number of elements
  const std::vector<int64_t> &shape = node->is(c10::attr::shape);
  int64_t numel = std::accumulate(shape.begin(), shape.end(), 1,
                                  std::multiplies<int64_t>());

  return numel == 1;
}

template <typename T> T foldConstant(torch::jit::Node *node) {
  auto data_sym = c10::attr::data;
  ERROR_ON_MSG(!node->hasAttribute(data_sym),
               "Internal Compiler Error: Node must have data attribute");

  const std::vector<int64_t> &value = node->is(data_sym);
  ERROR_ON_MSG(value.size() != 1,
               "Internal Compiler Error: Node value must be a scalar");
  return value[0];
}

} // namespace

bool registerHandler(c10::Symbol symbol, const SymbolHandler &handler) {
  logging::trace("Registering handler for symbol {}", symbol.toDisplayString());
  bool new_handler = symbolHandlers().emplace(symbol, handler).second;
  ERROR_ON_MSG(!new_handler, "Symbol " << symbol.toDisplayString()
                                       << " already has a handler registered");
  return new_handler;
}

// Return a pointer to a handler if one is registered for this kind of node or
// an empty std::function otherwise.
SymbolHandler getHandler(torch::jit::Node *node) {
  auto it = symbolHandlers().find(node->kind());
  if (it != symbolHandlers().end()) {
    return it->second;
  }
  return {};
}

std::vector<torch::jit::Value *> handleTensorList(torch::jit::Node *node) {
  std::vector<torch::jit::Value *> result;
  // Just convert the node->inputs array ref to vector and return it.
  for (torch::jit::Value *value : node->inputs()) {
    result.push_back(value);
  }
  return result;
}

// Convert that IR type into a C++ vector of ints.
std::vector<std::int64_t> shapeFromTensor(torch::jit::Value *value) {
  // Extract the type from the pytorch IR.
  c10::TensorTypePtr as_tensor = value->type()->expect<c10::TensorType>();
  c10::VaryingShape dims = as_tensor->sizes();

  // Convert that IR type into a C++ vector of ints.
  std::vector<std::int64_t> shape;
  for (auto optional_int : *dims.sizes()) {
    shape.push_back(*optional_int);
  }
  return shape;
}

// Add a vector of ints to the IR as a constant.
torch::jit::Value *
intVectorToIrConstant(torch::jit::Graph *graph,
                      const std::vector<std::int64_t> &shape) {
  const std::vector<std::int64_t> dimensions = {
      static_cast<std::int64_t>(shape.size())};
  return createConstantInt(graph, shape, dimensions)->output();
}

// Get the shape of a tensor and add it to the graph as a constant value.
torch::jit::Value *shapeFromTensorAsIR(torch::jit::Graph *graph,
                                       torch::jit::Value *value) {
  // Extract the type from the pytorch IR.
  std::vector<std::int64_t> shape = shapeFromTensor(value);
  return intVectorToIrConstant(graph, shape);
}

// Get the scalar type of a given tensor.
at::ScalarType getNodeScalarType(torch::jit::Value *tensor) {
  // The returned value must be a tensor.
  c10::TensorTypePtr return_tensor = tensor->type()->expect<c10::TensorType>();

  // Deduce the type from the scalar type on the return.
  return *return_tensor->scalarType();
}

template <typename T> std::vector<T> handleList(torch::jit::Node *node) {
  if (node->kind() == c10::prim::ListConstruct) {
    return handleListConstruct<T>(node);
  }
  if (node->kind() == c10::prim::Constant) {
    auto sym = c10::attr::value;

    ERROR_ON_MSG(!node->hasAttribute(sym), "Node must have value attribute");

    return *Handle<std::vector<T>>{}(sym, node);
  }
  std::cerr << "Unhandled list input node:\n";
  node->dump();
  ERROR("List inputs must be of type prim::ListConstruct");
}

template <typename T>
std::vector<T> handleListConstruct(torch::jit::Node *node) {
  ERROR_ON(node->kind() != c10::prim::ListConstruct);

  std::vector<T> result;

  for (torch::jit::Value *value : node->inputs()) {
    std::optional<T> val = handleConstant<T>(value->node());
    if (val) {
      result.push_back(*val);
    }
  }

  return result;
}

template <typename T> std::optional<T> handleConstant(torch::jit::Node *node) {
  // Lists should be explicitly handled in handle list construct.
  if (node->kind() == c10::prim::ListConstruct) {
    return std::nullopt;
  }

  if (node->kind() != c10::prim::Constant && canBeConstFolded(node)) {
    if constexpr (std::is_integral<T>::value) { // NOLINT
      return foldConstant<T>(node);
    }
  }

  if (node->kind() != c10::prim::Constant) {
    return std::nullopt;
  }

  auto sym = c10::attr::value;

  if (!node->hasAttribute(sym)) {
    return std::nullopt;
  }

  return Handle<T>{}(sym, node);
}

bool isNone(torch::jit::Node *node) {
  if (node->kind() != c10::prim::Constant) {
    return false;
  }

  auto sym = c10::attr::value;
  return !node->hasAttribute(sym);
}

std::int64_t handleDimensionParam(torch::jit::Node *node, int index) {
  // Extract the dim.
  std::int64_t dim = *handleConstant<std::int64_t>(node->input(index)->node());

  // Get the tensor type. Deduce on the first parameter.
  c10::TensorTypePtr as_tensor =
      node->input(0)->type()->expect<c10::TensorType>();
  c10::VaryingShape dims = as_tensor->sizes();

  // If dim is less than zero subtract it to get the actual dimension.
  if (dim < 0) {
    dim = *dims.size() + dim;
  }

  // Return the dim.
  return dim;
}

torch::jit::Node *createIRConstant(torch::jit::Graph *graph,
                                   torch::jit::Value *value) {
  // Get the scalar type of the result.
  c10::FloatTypePtr as_float = value->type()->cast<c10::FloatType>();
  c10::IntTypePtr as_int = value->type()->cast<c10::IntType>();
  if (as_int) {
    return createConstantInt(
        graph, {*handleConstant<std::int64_t>(value->node())}, {1});
  }
  if (as_float) {
    return createConstantFloat(graph, {*handleConstant<float>(value->node())},
                               {1});
  }

  // If this is still a constant.
  if (value->node()->kind() == c10::prim::Constant) {
    // Scalar doubles and longs are tensors somehow.
    at::Tensor tensor = value->node()->t(c10::attr::value);

    // Create the dimensions.
    std::vector<std::int64_t> dimensions{};
    for (auto dim : tensor.sizes()) {
      dimensions.push_back(dim);
    }

    c10::ScalarType type = tensor.scalar_type();

    // Convert the tensor if it isn't already in one of these types. The
    // double/long constraint comes from the IR attribute needing to be double
    // or long.
    if (type == at::ScalarType::Float) {
      tensor = tensor.to(at::ScalarType::Double);
    } else if (type == at::ScalarType::Int) {
      tensor = tensor.to(at::ScalarType::Long);
    }

    type = tensor.scalar_type();
    // Add the actual constant.
    if (type == at::ScalarType::Long) {
      std::vector<std::int64_t> data;
      data.resize(tensor.numel());
      const std::int64_t *the_data = tensor.data_ptr<int64_t>();

      std::memcpy(data.data(), the_data, tensor.nbytes());

      return createConstantInt(graph, data, dimensions);
    }
    if (type == at::ScalarType::Double) {
      std::vector<double> data;
      data.resize(tensor.numel());

      const double *the_data = tensor.data_ptr<double>();

      std::memcpy(data.data(), the_data, tensor.nbytes());

      return createConstantFloat(graph, data, dimensions);
    }
    ERROR("Internal error: Constant type not supported "
          << tensor.scalar_type());
  }

  // Legal to return null means |value| was not a constant.
  return nullptr;
}

torch::jit::Value *handleParamOrConstantNoCast(torch::jit::Graph *graph,
                                               torch::jit::Value *operand) {
  torch::jit::Value *value_to_return = operand;
  torch::jit::Node *constant = createIRConstant(graph, operand);

  if (constant) {
    value_to_return = constant->output();
  }

  return value_to_return;
}

std::int32_t convertReduceToPopart(std::int32_t pytorchReduce) {
  // Popart:
  // Sum = 0, Mean =1, NoReduction = 2
  // Pytorch
  // Sum = 2, Mean =1, NoReduction = 0
  if (pytorchReduce == 0) {
    return 2;
  }
  if (pytorchReduce == 1) {
    return 1;
  }
  if (pytorchReduce == 2) {
    return 0;
  }

  ERROR("Unsupported pytorch reduce");
}

void markNodeForDeletion(torch::jit::Node *node) {
  node->i_(delete_node_attr, 1);
}

bool isMarkedForDeletion(torch::jit::Node *node) {
  return node->hasAttribute(delete_node_attr) && node->i(delete_node_attr) > 0;
}

void replaceOutputUse(torch::jit::Value *old_val, torch::jit::Value *new_val) {
  // Take the type of the old value.
  new_val->setType(old_val->type());

  // Replace the old value with the new one.
  old_val->replaceAllUsesWith(new_val);
}

void replaceOutputUse(torch::jit::Node *oldNode, torch::jit::Node *new_node,
                      std::uint64_t outputIdx) {
  torch::jit::Value *new_val = new_node->output(outputIdx);
  torch::jit::Value *old_val = oldNode->output(outputIdx);
  replaceOutputUse(old_val, new_val);
}

template std::vector<int> handleListConstruct(torch::jit::Node *node);
template std::vector<std::int64_t> handleList(torch::jit::Node *node);
template std::optional<float> handleConstant(torch::jit::Node *);
template std::optional<int> handleConstant(torch::jit::Node *);
template std::optional<bool> handleConstant(torch::jit::Node *);
template std::optional<std::string> handleConstant(torch::jit::Node *);

} // namespace poptorch
