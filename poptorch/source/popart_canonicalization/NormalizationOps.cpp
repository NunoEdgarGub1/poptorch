// Copyright (c) 2020 Graphcore Ltd. All rights reserved.
#include "PopartCanonicalizationUtils.hpp"

#include "poptorch/OpBuilder.hpp"
#include "poptorch_logging/Error.hpp"

namespace poptorch {
namespace {

// Ensures running_mean and running_var tensors by creating constants if they
// are not set (None) The running_mean and running_var may be none e.g. if
// track_running_stats is set to False for the relevant PyTorch BatchNorm layer.
// To satisfy popart/onnx, create a zero input for running_mean and all ones for
// running_var
void maybeInitializeRunningParamConstants(
    torch::jit::Graph *graph, const c10::ScalarType input_type,
    torch::jit::Value **running_mean, torch::jit::Value **running_var,
    const std::vector<std::int64_t> &new_shape) {

  std::vector<int64_t> running_shape{new_shape[1]};

  if (!isNone(*running_mean)) {
      ERROR_ON(isNone(*running_var));
    return;
  }

  ERROR_ON(!isNone(*running_var));

  switch (input_type) {
  case c10::ScalarType::Int: {
    *running_mean = createConstantInt(graph, {0}, running_shape)->output();
    *running_var = createConstantInt(graph, {1}, running_shape)->output();
    break;
  }
  case c10::ScalarType::Float: {
    *running_mean = createConstantFloat(graph, {0.0}, running_shape)->output();
    *running_var = createConstantFloat(graph, {1.0}, running_shape)->output();
    break;
  }
  case c10::ScalarType::Half: {
    *running_mean =
        createConstantFloat16(graph, {0.0}, running_shape)->output();
    *running_var = createConstantFloat16(graph, {1.0}, running_shape)->output();
    break;
  }
  default: {
    ERROR("Batch norm input"
          << " of type " << c10::toString(input_type) << " not supported");
  }
  }
}

torch::jit::Node *batchNormHandler(torch::jit::Graph *graph,
                                   torch::jit::Node *node) {
  torch::jit::Node *new_node;
  // aten::batch_norm(Tensor input, Tensor? weight, Tensor? bias, Tensor?
  // running_mean, Tensor?  , bool training, float momentum, float
  // eps, bool cudnn_enabled) -> Tensor

  // Pytorch supports BatchNorm1D/2D/3D. PopART only supports 2D so we need
  // to reshape input into a 4D tensor.

  // Keep track of the original shape so we can convert back if we are
  // running BatchNorm1D or 3D.
  std::vector<std::int64_t> original_shape = shapeFromTensor(node->input(0));

  // New 4D shape to perform the operation with.
  std::vector<std::int64_t> new_shape = original_shape;

  // Turn the shape into a 4D tensor.
  if (original_shape.size() == 2) {
    // Add two singletons to pad to 4D.
    new_shape.push_back(1);
    new_shape.push_back(1);
  } else if (original_shape.size() == 3) {
    // Add one singleton to get to 4D.
    new_shape.push_back(1);
  } else if (original_shape.size() == 5) {
    // Flatten last two dimensions to reduce to 4.
    new_shape[3] *= new_shape[4];
    new_shape.pop_back();
  }

  // Input is value at 0th position.
  torch::jit::Value *input = node->input(0);

  // Reshape to 4D if needed.
  if (original_shape.size() != 4) {
    torch::jit::Node *reshape_in = createReshape(graph, input, new_shape);
    input = reshape_in->output();
  }

  torch::jit::Value *weight = node->input(1);
  torch::jit::Value *bias = node->input(2);

  // In the PyTorch source code at the time of writing, weight and bias are
  // always set despite being optional in at aten::batch_norm
  ERROR_ON(weight->type()->cast<c10::TensorType>() == nullptr);
  ERROR_ON(bias->type()->cast<c10::TensorType>() == nullptr);

  torch::jit::Value *running_mean = node->input(3);
  torch::jit::Value *running_var = node->input(4);

  // Use initialised constants if running_mean and running_var are none
  maybeInitializeRunningParamConstants(
      graph, *input->type()->expect<c10::TensorType>()->scalarType(),
      &running_mean, &running_var, new_shape);

  std::vector<torch::jit::Value *> input_tensors{input, weight, bias,
                                                 running_mean, running_var};

  float momentum = constantToFloat(node->input(6)->node());
  float epsilon = constantToFloat(node->input(7)->node());

  new_node = poptorch::createBatchnormalization(graph, input_tensors, 1,
                                                epsilon, momentum);

  // If we reshaped, reshape back.
  if (original_shape.size() != 4) {
    // Add the batch norm.

    // This is now the new node.
    new_node = createReshape(graph, new_node->output(), original_shape);
  }

  return new_node;
}

torch::jit::Node *layerNormHandler(torch::jit::Graph *graph,
                                   torch::jit::Node *node) {
  // aten::layer_norm(Tensor input,int[] normalized_shape, Tensor? weight,
  //                Tensor? bias, float eps, bool cudnn_enable) -> Tensor

  // Tensor to normalise.
  torch::jit::Value *input = node->input(0);

  // Bias to add
  torch::jit::Value *gamma = node->input(2);

  // Weight to multiply.
  torch::jit::Value *beta = node->input(3);

  const float epsilon = constantToFloat(node->input(4)->node());

  // Pytorch normalizes across arbitrary number of dimensions from the end.
  // We flatten into a [M, N] array and normalize the N.

  std::vector<std::int64_t> output_shape = shapeFromTensor(node->output());
  std::vector<std::int64_t> normalized_shape =
      constantToLongVec(node->input(1)->node());
  std::vector<std::int64_t> input_shape = shapeFromTensor(input);
  const std::int64_t axis = input_shape.size() - normalized_shape.size();

  // Flatten into [M, N]
  torch::jit::Node *flatten = createFlattenTypedOutput(graph, {input}, axis);

  // Normalize.
  torch::jit::Node *normalize = createGroupnormalization(
      graph, {flatten->output(), gamma, beta}, 1, epsilon);

  // Perform the reshape.
  return createReshape(graph, normalize->output(), output_shape);
}
} // namespace

// clang-format off
static bool handlers = registerHandlers(
    c10::aten::batch_norm, batchNormHandler,
    c10::aten::layer_norm, layerNormHandler);
// clang-format on

} // namespace poptorch
