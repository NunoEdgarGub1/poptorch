#include <poptorch/ShapeInference.hpp>

namespace poptorch {

using InferenceFunction = std::function<void(torch::jit::Node *)>;

class InferenceFunctions {
public:
  InferenceFunctions(const InferenceFunctions &) = delete;
  InferenceFunctions &operator=(const InferenceFunctions &) = delete;

  static void registerFunction(const std::vector<std::string> &kinds,
                               InferenceFunction func) {
    for (auto &kind : kinds) {
      registerFunction(kind, func);
    }
  }

  static void registerFunction(const std::string &kind,
                               InferenceFunction func) {
    instance().inferenceFunctions.insert({kind, func});
  }

  static void tryInferShapeFor(torch::jit::Node *node) {
    std::string kind = node->kind().toDisplayString();
    auto found = instance().inferenceFunctions.find(kind);
    if (found != instance().inferenceFunctions.end()) {
      auto inferenceFunc = found->second;
      inferenceFunc(node);
    } else {
      std::cerr << "Dont know how to infer shape for node of kind '" << kind
                << "'\n";
    }
  }

private:
  InferenceFunctions() {}

  // `instance` is not static member of the class as the initialization of
  // globals is undefined. Accessing `instance` through a method forces it to be
  // constructed before use.
  // https://stackoverflow.com/questions/3746238/c-global-initialization-order-ignores-dependencies/3746249#3746249
  static InferenceFunctions &instance() {
    static InferenceFunctions instance;
    return instance;
  }

  std::unordered_map<std::string, InferenceFunction> inferenceFunctions;
};

struct RegisterInferenceFunction {
  RegisterInferenceFunction(const std::vector<std::string> &kinds,
                            InferenceFunction func) {
    InferenceFunctions::registerFunction(kinds, func);
  }

  RegisterInferenceFunction(const std::string &kind, InferenceFunction func) {
    InferenceFunctions::registerFunction(kind, func);
  }
};

void outputTypeMatchesInputType(torch::jit::Node *node) {
  auto inputType = node->input(0)->type()->cast<torch::jit::TensorType>();
  if (!inputType->isComplete()) {
    std::cerr << "Cannot infer shape, input shape is not complete!\n";
    return;
  }

  node->output()->setType(inputType);
}

// aten::conv2d(Tensor input, Tensor weight, Tensor? bias, int[] stride, int[]
// padding, int[] dilation, int groups) -> Tensor",
void inferShapeConv2d(torch::jit::Node *node) {
  auto inputType = node->input(0)->type()->cast<torch::jit::TensorType>();
  if (!inputType->isComplete()) {
    std::cerr << "Cannot infer shape, input shape is not complete!\n";
    return;
  }

  auto weightType = node->input(1)->type()->cast<torch::jit::TensorType>();
  if (!weightType->isComplete()) {
    std::cerr << "Cannot infer shape, weight shape is not complete!\n";
    return;
  }

  int strideInputIndex = 3;
  int paddingInputIndex = 4;
  int dilationInputIndex = 5;

  if (node->input(strideInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get stride\n";
    return;
  }
  auto strideData = node->input(strideInputIndex)
                        ->node()
                        ->is(c10::Symbol::fromQualString("attr::value"));

  if (node->input(paddingInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get padding\n";
    return;
  }
  auto paddingData = node->input(paddingInputIndex)
                         ->node()
                         ->is(c10::Symbol::fromQualString("attr::value"));

  if (node->input(dilationInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get dilation\n";
    return;
  }
  auto dilationData = node->input(dilationInputIndex)
                          ->node()
                          ->is(c10::Symbol::fromQualString("attr::value"));

  auto inputShape = *inputType->sizes().concrete_sizes();
  auto weightShape = *weightType->sizes().concrete_sizes();

  auto batchSize = inputShape[0];
  auto outChans = weightShape[0];
  std::vector<int64_t> kernelShape;
  for (int i = 0; i < 2; i++) {
    kernelShape.push_back(weightShape[2 + i]);
  }

  auto calculate_dim = [](int64_t i, int64_t k, int64_t s, int64_t p,
                          int64_t d) {
    auto x = i + 2 * p - d * (k - 1) - 1;
    return (x / s) + 1;
  };

  std::vector<int64_t> outShape{batchSize, outChans};

  for (int i = 0; i < 2; i++) {
    auto x = calculate_dim(inputShape[2 + i], kernelShape[i], strideData[i],
                           paddingData[i], dilationData[i]);
    outShape.push_back(x);
  }

  auto outputType = inputType->withSizes(outShape);
  node->output()->setType(outputType);
}

// "aten::max_pool2d(Tensor self, int[] kernel_size, int[] stride, int[]
// padding, int[] dilation, bool ceil_mode) -> Tensor",
void inferShapeMaxPool2d(torch::jit::Node *node) {
  auto inputType = node->input(0)->type()->cast<torch::jit::TensorType>();
  if (!inputType->isComplete()) {
    std::cerr << "Cannot infer shape, input shape is not complete!\n";
    return;
  }

  auto inputShape = *inputType->sizes().concrete_sizes();
  auto N = inputShape[0];
  auto C = inputShape[1];

  int kernelInputIndex = 1;
  int strideInputIndex = 2;
  int paddingInputIndex = 3;
  int dilationInputIndex = 4;

  if (node->input(kernelInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get kernel\n";
    return;
  }
  auto kernelData = node->input(kernelInputIndex)
                        ->node()
                        ->is(c10::Symbol::fromQualString("attr::value"));

  if (node->input(strideInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get stride\n";
    return;
  }
  auto strideData = node->input(strideInputIndex)
                        ->node()
                        ->is(c10::Symbol::fromQualString("attr::value"));

  if (node->input(paddingInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get padding\n";
    return;
  }
  auto paddingData = node->input(paddingInputIndex)
                         ->node()
                         ->is(c10::Symbol::fromQualString("attr::value"));

  if (node->input(dilationInputIndex)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get dilation\n";
    return;
  }
  auto dilationData = node->input(dilationInputIndex)
                          ->node()
                          ->is(c10::Symbol::fromQualString("attr::value"));

  std::vector<int64_t> outShape{N, C};

  for (int i = 0; i < 2; i++) {
    auto stride = strideData[i];
    auto padding = paddingData[i];
    auto kernel = kernelData[i];
    auto dilation = dilationData[i];
    auto dim = inputShape[2 + i];
    auto x = dim + 2 * padding - dilation * (kernel - 1) - 1;
    auto y = (x / stride) + 1;
    outShape.push_back(y);
  }

  auto outputType = inputType->withSizes(outShape);
  node->output()->setType(outputType);
}

void inferShapeView(torch::jit::Node *node) {
  auto inputType = node->input(0)->type()->cast<torch::jit::TensorType>();
  if (!inputType->isComplete()) {
    std::cerr << "Cannot infer shape, input shape is not complete!\n";
    return;
  }

  auto inputShape = *inputType->sizes().concrete_sizes();

  if (node->input(1)->node()->kind() != c10::prim::Constant) {
    std::cerr << "Cannot infer shape, unable to get data for shape input\n";
    return;
  }
  auto shapeData =
      node->input(1)->node()->is(c10::Symbol::fromQualString("attr::value"));

  auto getNumberElements = [](auto shape) {
    int64_t numberElements = 1;
    for (auto dim : shape) {
      if (dim != -1) {
        numberElements *= dim;
      }
    }
    return numberElements;
  };

  int unknownDimensions = 0;
  for (auto dim : shapeData) {
    if (dim == -1) {
      unknownDimensions += 1;
    }
  }

  if (unknownDimensions == 0) {
    if (getNumberElements(shapeData) != getNumberElements(inputShape)) {
      std::cerr << "Error: New shape has a different number of elements to old "
                   "shape.\n";
      return;
    }
    auto outputType = inputType->withSizes(shapeData);
    node->output()->setType(outputType);
  } else if (unknownDimensions == 1) {
    auto oldNumberElements = getNumberElements(inputShape);
    auto newNumberElements = getNumberElements(shapeData);
    std::vector<int64_t> outputShape;
    for (auto dim : shapeData) {
      if (dim == -1) {
        outputShape.push_back(oldNumberElements / newNumberElements);
      } else {
        outputShape.push_back(dim);
      }
    }
    auto outputType = inputType->withSizes(outputShape);
    node->output()->setType(outputType);
  } else {
    std::cerr << "Too many unknown dimensions (" << unknownDimensions
              << ") in shape data (" << shapeData << ")\n";
  }
}

void inferShapeAddmm(torch::jit::Node *node) {
  auto mat1Type = node->input(1)->type()->cast<torch::jit::TensorType>();
  if (!mat1Type->isComplete()) {
    std::cerr << "Cannot infer shape, mat1 shape is not complete!\n";
    return;
  }

  auto mat1Shape = *mat1Type->sizes().concrete_sizes();

  auto mat2Type = node->input(2)->type()->cast<torch::jit::TensorType>();
  if (!mat2Type->isComplete()) {
    std::cerr << "Cannot infer shape, mat2 shape is not complete!\n";
    return;
  }

  auto mat2Shape = *mat2Type->sizes().concrete_sizes();

  auto N = mat1Shape[0];
  auto P = mat2Shape[1];

  std::vector<int64_t> outShape{N, P};
  auto outputType = mat1Type->withSizes(outShape);
  node->output()->setType(outputType);
}

void inferShapeTranspose(torch::jit::Node *node) {
  auto inputType = node->input(0)->type()->cast<torch::jit::TensorType>();
  if (!inputType->isComplete()) {
    std::cerr << "Cannot infer shape, input shape is not complete!\n";
    return;
  }

  auto inputShape = *inputType->sizes().concrete_sizes();
  if (inputShape.size() != 2) {
    std::cerr << "Transpose inference only handles inputs with rank 2.\n";
  }

  std::vector<int64_t> outShape{inputShape[1], inputShape[0]};
  auto outputType = inputType->withSizes(outShape);
  node->output()->setType(outputType);
}

void propagateInputShapes(torch::jit::Block *block) {
  for (auto node : block->nodes()) {
    for (auto b : node->blocks()) {
      propagateInputShapes(b);
    }

    InferenceFunctions::tryInferShapeFor(node);
  }
}

void propagateInputShapes(torch::jit::Graph *graph) {
  propagateInputShapes(graph->block());
}

namespace {
RegisterInferenceFunction outputMatchesInput({"aten::batch_norm", "aten::relu",
                                              "aten::relu_", "aten::softmax",
                                              "aten::unchecked_cast"},
                                             outputTypeMatchesInputType);
RegisterInferenceFunction conv2d("aten::conv2d", inferShapeConv2d);
RegisterInferenceFunction maxpool2d("aten::max_pool2d", inferShapeMaxPool2d);
RegisterInferenceFunction view("aten::view", inferShapeView);
RegisterInferenceFunction addmm("aten::addmm", inferShapeAddmm);
RegisterInferenceFunction transpose("aten::t", inferShapeTranspose);
} // namespace

} // namespace poptorch
