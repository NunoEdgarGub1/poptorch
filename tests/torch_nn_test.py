# Copyright (c) 2020 Graphcore Ltd. All rights reserved.

import os
import sys
import torch
from torch.testing._internal.jit_metaprogramming_utils import get_all_nn_module_tests, get_nn_mod_test_name, get_nn_module_name_from_kwargs
import pytest
import poptorch

# Importing jit_metaprogramming_utils changes the default type to
# double set it back to float.
torch.set_default_dtype(torch.float32)

# yapf: disable
# pylint: disable=line-too-long
EXPECTED_FAILURES = {
    "test_nn_LayerNorm_1d_empty_elementwise_affine": "Floating point exception", # TODO(T26648) Popart bug

    "test_nn_BatchNorm3d_not_affine": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.onnx.BatchNormalization:9, inputs=[Reshape:0], outputs=[]), but input is not optional", # TODO(T26651) Popart feature request

    # TODO(T26652): Popart feature request
    "test_nn_LayerNorm_3d_no_elementwise_affine": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",
    "test_nn_LayerNorm_1d_no_elementwise_affine": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",
    "test_nn_GroupNorm_1d_no_affine_IN": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",
    "test_nn_GroupNorm_1d_no_affine_LN": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",
    "test_nn_GroupNorm_2d_no_affine_IN": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",
    "test_nn_GroupNorm_2d_no_affine_LN": "Weights & bias are mandatory in Popart: No input found for input 1 of Op(ai.graphcore.GroupNormalization:1, inputs=[Flatten:0], outputs=[]), but input is not optional",

    "test_nn_MultiheadAttention": "Cannot force a non-constant node to a long", # TODO(T26654) Poptorch feature: support non-constant start/end in sliceHandler

    "test_nn_interpolate_nearest_1d": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_1d_zero_dim": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_tuple_1d": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_2d_launch_configs": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_2d": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_tuple_2d": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_2d_zero_dim": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_3d": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_3d_zero_dim": "Cannot force a non-constant node to a float",
    "test_nn_interpolate_nearest_tuple_3d": "Cannot force a non-constant node to a float",

    "test_nn_Softshrink_lambda": "LowerToPopart no registered op",
    "test_nn_LeakyReLU": "LowerToPopart no registered op",

    "test_nn_PReLU_1d": "Broadcasting failed",
    "test_nn_PReLU_2d": "Broadcasting failed",
    "test_nn_PReLU_3d": "Broadcasting failed",
    "test_nn_CrossMapLRN2d": "Broadcasting failed",
    "test_nn_PReLU_1d_multiparam": "Broadcasting failed",
    "test_nn_PReLU_2d_multiparam": "Broadcasting failed",
    "test_nn_Hardshrink": "Broadcasting failed",
    "test_nn_Softmax": "Broadcasting failed",
    "test_nn_Flatten": "Broadcasting failed",
    "test_nn_PReLU_3d_multiparam": "Broadcasting failed",

    "test_nn_BatchNorm1d_affine_simple_average": "Failing Cast",
    "test_nn_BatchNorm1d_not_tracking_stats": "Failing Cast",
    "test_nn_BatchNorm1d_3d_input_not_affine": "Failing Cast",
    "test_nn_BatchNorm2d_momentum": "Failing Cast",
    "test_nn_BatchNorm2d_not_tracking_stats": "Failing Cast",
    "test_nn_BatchNorm3d_momentum": "Failing Cast",
    "test_nn_BatchNorm3d_not_tracking_stats": "Failing Cast",
    "test_nn_BatchNorm1d_3d_input": "Failing Cast",
    "test_nn_BatchNorm1d_not_affine": "Failing Cast",
    "test_nn_BatchNorm2d_2d_simple_average": "Failing Cast",
    "test_nn_BatchNorm2d_not_affine": "Failing Cast",
    "test_nn_BatchNorm1d_affine": "Failing Cast",
    "test_nn_BatchNorm2d": "Failing Cast",

    "test_nn_GroupNorm_1d_affine": "Invalid number of channels",
    "test_nn_Conv1d_zero_batch": "StepIO did not provide input data for tensor input",
    "test_nn_Conv2d_zero_batch": "StepIO did not provide input data for tensor input",
    "test_nn_Conv3d_zero_batch": "StepIO did not provide input data for tensor input",
    "test_nn_ConvTranspose1d_dilated": "Popart exception format",
    "test_nn_ConvTranspose2d_dilated": "Popart exception format",
    "test_nn_ConvTranspose3d_dilated": "Popart exception format",
    "test_nn_MaxPool2d_3d_input": "Invalid length of strides vector",
    "test_nn_LPPool2d_norm": "Invalid length of padding vector",

    "test_nn_AdaptiveMaxPool2d_single": "std::vector out of bounds access",
    "test_nn_AdaptiveMaxPool2d_tuple": "std::vector out of bounds access",
    "test_nn_AdaptiveMaxPool2d_tuple_none": "std::vector out of bounds access",
    "test_nn_AdaptiveAvgPool2d_single": "std::vector out of bounds access",
    "test_nn_AdaptiveAvgPool2d_single_1x1output": "std::vector out of bounds access",
    "test_nn_AdaptiveAvgPool2d_tuple": "std::vector out of bounds access",
    "test_nn_AdaptiveAvgPool2d_tuple_none": "std::vector out of bounds access",

    "test_nn_Conv3d_circular_stride2_pad2": "hangs ? really slow ?",
    "test_nn_Padding122112_3dcircular": "hangs ? really slow ?",
    "test_nn_Padding322112_3dcircular": "hangs ? really slow ?",
    "test_nn_Padding332122_3dcircular": "hangs ? really slow ?",


    "test_nn_softmax_spatial_dtype": "AssertionError: With rtol=0.0001 and atol=1e-05, found 64 element(s) (out of 64) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.662305723875761 (0.706894040107727 vs. 0.04458831623196602), which occurred at index (0, 1, 2, 3).",
    "test_nn_Softmin_multidim": "AssertionError: With rtol=0.0001 and atol=1e-05, found 300 element(s) (out of 300) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.528009258210659 (0.5376919507980347 vs. 0.009682692587375641), which occurred at index (0, 1, 4, 6).",

    "test_nn_GroupNorm_2d_affine": "AssertionError: With rtol=0.0001 and atol=1e-05, found 144 element(s) (out of 144) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 1.3549566268920898 (2.1383447647094727 vs. 0.7833881378173828), which occurred at index (2, 2, 1, 1).",
    "test_nn_AvgPool1d_stride_pad": "AssertionError: With rtol=0.0001 and atol=1e-05, found 12 element(s) (out of 24) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.39088454842567444 (0.39088454842567444 vs. 0.7817690968513489), which occurred at index (0, 2, 3).",
    "test_nn_AvgPool2d_stride_pad": "AssertionError: With rtol=0.0001 and atol=1e-05, found 72 element(s) (out of 96) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.7429442256689072 (0.24764807522296906 vs. 0.9905923008918762), which occurred at index (0, 1, 0, 0).",
    "test_nn_AvgPool2d_divisor": "AssertionError: With rtol=0.0001 and atol=1e-05, found 54 element(s) (out of 54) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 2.755292057991028 (3.673722743988037 vs. 0.9184306859970093), which occurred at index (1, 2, 2, 2).",
    "test_nn_AvgPool2d_divisor_stride": "AssertionError: With rtol=0.0001 and atol=1e-05, found 54 element(s) (out of 54) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 2.236291766166687 (2.981722354888916 vs. 0.745430588722229), which occurred at index (0, 1, 2, 2).",
    "test_nn_AvgPool2d_divisor_stride_pad": "AssertionError: With rtol=0.0001 and atol=1e-05, found 72 element(s) (out of 96) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 2.427279531955719 (3.236372709274292 vs. 0.809093177318573), which occurred at index (0, 0, 1, 2).",
    "test_nn_AvgPool3d_stride_pad": "AssertionError: With rtol=0.0001 and atol=1e-05, found 114 element(s) (out of 162) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.6763140857219696 (0.22543802857398987 vs. 0.9017521142959595), which occurred at index (0, 2, 2, 0, 0).",
    "test_nn_AvgPool3d_stride_pad_gpu_fixedkw_output": "AssertionError: With rtol=0.0001 and atol=1e-05, found 66 element(s) (out of 72) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.3809252828359604 (0.22855515778064728 vs. 0.6094804406166077), which occurred at index (1, 1, 0, 0, 1).",
    "test_nn_AvgPool3d_stride_pad_gpu_general_output": "AssertionError: With rtol=0.0001 and atol=1e-05, found 264 element(s) (out of 270) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.4184434115886688 (0.16373875737190247 vs. 0.5821821689605713), which occurred at index (0, 2, 2, 0, 4).",
    "test_nn_AvgPool3d_stride_pad_gpu_input_nooverlap": "AssertionError: With rtol=0.0001 and atol=1e-05, found 156 element(s) (out of 162) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.8563244119286537 (0.12233205884695053 vs. 0.9786564707756042), which occurred at index (0, 0, 2, 2, 0).",
    "test_nn_AvgPool3d_divisor": "AssertionError: With rtol=0.0001 and atol=1e-05, found 48 element(s) (out of 48) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 5.214784324169159 (5.959753513336182 vs. 0.7449691891670227), which occurred at index (0, 2, 0, 0, 0).",
    "test_nn_AvgPool3d_divisor_stride": "AssertionError: With rtol=0.0001 and atol=1e-05, found 48 element(s) (out of 48) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 4.80545711517334 (5.491950988769531 vs. 0.6864938735961914), which occurred at index (1, 1, 1, 1, 0).",
    "test_nn_AvgPool3d_divisor_stride_pad": "AssertionError: With rtol=0.0001 and atol=1e-05, found 156 element(s) (out of 162) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 4.580634713172913 (5.235011100769043 vs. 0.6543763875961304), which occurred at index (1, 2, 1, 1, 1).",
    "test_nn_AvgPool3d_divisor_stride_pad_gpu_fixedkw_output": "AssertionError: With rtol=0.0001 and atol=1e-05, found 72 element(s) (out of 72) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 33.63082355260849 (34.16464614868164 vs. 0.5338225960731506), which occurred at index (1, 1, 1, 1, 1).",
    "test_nn_AvgPool3d_divisor_stride_pad_gpu_general_output": "AssertionError: With rtol=0.0001 and atol=1e-05, found 270 element(s) (out of 270) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 32.37348711490631 (32.887351989746094 vs. 0.5138648748397827), which occurred at index (1, 1, 1, 1, 2).",
    "test_nn_AvgPool3d_divisor_stride1_pad0_gpu_input": "AssertionError: With rtol=0.0001 and atol=1e-05, found 48 element(s) (out of 48) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 15.688140630722046 (16.29153060913086 vs. 0.6033899784088135), which occurred at index (0, 2, 0, 0, 0).",
    "test_nn_AvgPool3d_divisor_stride_pad_gpu_input_nooverlap": "AssertionError: With rtol=0.0001 and atol=1e-05, found 114 element(s) (out of 162) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 5.383516907691956 (6.152590751647949 vs. 0.7690738439559937), which occurred at index (0, 2, 1, 1, 1).",
    "test_nn_GELU": "AssertionError: With rtol=0.0001 and atol=1e-05, found 7 element(s) (out of 30) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.00013697147369384766 (0.7933593392372131 vs. 0.7932223677635193), which occurred at index (0, 1, 3).",
    "test_nn_softmax_spatial_special": "AssertionError: With rtol=0.0001 and atol=1e-05, found 1024 element(s) (out of 1024) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.009421411203220487 (0.012496765702962875 vs. 0.0030753544997423887), which occurred at index (0, 114, 0, 0).",
    "test_nn_softmax_spatial": "AssertionError: With rtol=0.0001 and atol=1e-05, found 64 element(s) (out of 64) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.6575267650187016 (0.7020591497421265 vs. 0.04453238472342491), which occurred at index (1, 0, 1, 0).",
    "test_nn_softmax_functional_dim0": "AssertionError: With rtol=0.0001 and atol=1e-05, found 120 element(s) (out of 120) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.7021725764498115 (0.7146565914154053 vs. 0.012484014965593815), which occurred at index (0, 1, 2, 1).",
    "test_nn_log_softmax_spatial_special": "AssertionError: With rtol=0.0001 and atol=1e-05, found 1024 element(s) (out of 1024) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 1.4219598770141602 (-4.52596378326416 vs. -5.94792366027832), which occurred at index (0, 127, 1, 0).",
    "test_nn_log_softmax_spatial": "AssertionError: With rtol=0.0001 and atol=1e-05, found 64 element(s) (out of 64) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 3.2339431643486023 (-0.6880427002906799 vs. -3.9219858646392822), which occurred at index (1, 0, 2, 0).",
    "test_nn_log_softmax_dim0": "AssertionError: With rtol=0.0001 and atol=1e-05, found 120 element(s) (out of 120) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 4.541183948516846 (-0.645355224609375 vs. -5.186539173126221), which occurred at index (0, 0, 2, 0).",
    "test_nn_Softmax2d": "AssertionError: With rtol=0.0001 and atol=1e-05, found 600 element(s) (out of 600) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 0.5474691272247583 (0.5498999953269958 vs. 0.002430868102237582), which occurred at index (0, 1, 6, 13).",
    "test_nn_LogSoftmax_multiparam": "AssertionError: With rtol=0.0001 and atol=1e-05, found 600 element(s) (out of 600) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 5.692737579345703 (-1.065810203552246 vs. -6.758547782897949), which occurred at index (0, 2, 7, 2).",


    "test_nn_LPPool1d_norm": "Output dimensions mismatch: assert torch.Size([1, 3, 3]) == torch.Size([1, 3, 6])",
    "test_nn_ConvTranspose1d": "Output dimensions mismatch: assert torch.Size([1, 4, 20]) == torch.Size([1, 4, 19])",
    "test_nn_ConvTranspose1d_no_bias": "Output dimensions mismatch: assert torch.Size([1, 4, 12]) == torch.Size([1, 4, 11])",
    "test_nn_ConvTranspose1d_groups": "Output dimensions mismatch: assert torch.Size([2, 6, 20]) == torch.Size([2, 6, 19])",
    "test_nn_ConvTranspose2d": "Output dimensions mismatch: assert torch.Size([1, 4, 20, 12]) == torch.Size([1, 4, 19, 11])",
    "test_nn_ConvTranspose2d_no_bias": "Output dimensions mismatch: assert torch.Size([1, 4, 12, 20]) == torch.Size([1, 4, 11, 19])",

    "test_nn_BCELoss_weights_no_reduce": "RuntimeError: expected int at position 0, but got: Tensor",
    "test_nn_Bilinear": "TypeError: bilinear(): argument 'input2' (position 2) must be Tensor, not tuple",
    "test_nn_Embedding": "RuntimeError: Expected tensor for argument #1 'indices' to have scalar type Long; but got torch.FloatTensor instead (while checking arguments for embedding)",

    "test_nn_BatchNorm2d_zero_batch": "ERROR in NormalizationOps.cpp:98: weight->type()->cast<c10::TensorType>() == nullptr Context: PopartCanonicalization processing %10 : Float(0:20, 5:4, 2:2, 2:1) = aten::batch_norm(%input, %4, %5, %11, %12, %13, %14, %15, %16)",
    "test_nn_BatchNorm1d_zero_batch": "RuntimeError: ERROR in NormalizationOps.cpp:98: weight->type()->cast<c10::TensorType>() == nullptr Context: PopartCanonicalization processing %10 : Float(0:45, 5:9, 9:1) = aten::batch_norm(%input, %4, %5, %11, %12, %13, %14, %15, %16)",
    "test_nn_BatchNorm3d_zero_batch": "RuntimeError: ERROR in NormalizationOps.cpp:98: weight->type()->cast<c10::TensorType>() == nullptr Context: PopartCanonicalization processing %10 : Float(0:40, 5:8, 2:4, 2:2, 2:1) = aten::batch_norm(%input, %4, %5, %11, %12, %13, %14, %15, %16)",

    "test_nn_BCELoss_weights_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_BCEWithLogitsLoss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_KLDivLoss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_KLDivLoss_no_reduce_scalar_log_target": "IndexError: tuple index out of range",
    "test_nn_L1Loss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_MSELoss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_SmoothL1Loss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_MultiLabelMarginLoss_0d_no_reduce": "IndexError: tuple index out of range",
    "test_nn_BCELoss_no_reduce_scalar": "IndexError: tuple index out of range",
    "test_nn_softmax_functional_scalar": "IndexError: tuple index out of range",
    "test_nn_SELU_scalar": "IndexError: tuple index out of range",
    "test_nn_CELU_scalar": "IndexError: tuple index out of range",
    "test_nn_GELU_scalar": "IndexError: tuple index out of range",
    "test_nn_log_softmax_scalar": "IndexError: tuple index out of range",
    "test_nn_Threshold_threshold_value_scalar": "IndexError: tuple index out of range",
    "test_nn_ReLU_scalar": "IndexError: tuple index out of range",
    "test_nn_ReLU6_scalar": "IndexError: tuple index out of range",
    "test_nn_RReLU_with_up_down_scalar": "IndexError: tuple index out of range",
    "test_nn_Hardtanh_scalar": "IndexError: tuple index out of range",
    "test_nn_Sigmoid_scalar": "IndexError: tuple index out of range",
    "test_nn_Tanh_scalar": "IndexError: tuple index out of range",
    "test_nn_Softmax_scalar": "IndexError: tuple index out of range",
    "test_nn_LogSoftmax_multiparam_scalar": "IndexError: tuple index out of range",
    "test_nn_ELU_scalar": "IndexError: tuple index out of range",
    "test_nn_Hardshrink_scalar": "IndexError: tuple index out of range",
    "test_nn_LeakyReLU_with_negval_scalar": "IndexError: tuple index out of range",
    "test_nn_LogSigmoid_scalar": "IndexError: tuple index out of range",
    "test_nn_Softplus_beta_threshold_scalar": "IndexError: tuple index out of range",
    "test_nn_Softshrink_lambda_scalar": "IndexError: tuple index out of range",
    "test_nn_PReLU_scalar": "IndexError: tuple index out of range",
    "test_nn_Softsign_scalar": "IndexError: tuple index out of range",
    "test_nn_Softmin_scalar": "IndexError: tuple index out of range",
    "test_nn_Tanhshrink_scalar": "IndexError: tuple index out of range",

    "test_nn_InstanceNorm3d_tracking_stats": "Unsupported op(s): aten::instance_norm",
    "test_nn_FractionalMaxPool2d_ratio": "Unsupported op(s): aten::fractional_max_pool2d",
    "test_nn_FractionalMaxPool2d_size": "Unsupported op(s): aten::fractional_max_pool2d",
    "test_nn_FractionalMaxPool3d_ratio": "Unsupported op(s): aten::fractional_max_pool3d",
    "test_nn_FractionalMaxPool3d_size": "Unsupported op(s): aten::fractional_max_pool3d",
    "test_nn_FractionalMaxPool3d_asymsize": "Unsupported op(s): aten::fractional_max_pool3d",
    "test_nn_Threshold_threshold_value": "Unsupported op(s): aten::threshold",
    "test_nn_Threshold_large_value": "Unsupported op(s): aten::threshold",
    "test_nn_RReLU": "Unsupported op(s): aten::rrelu",
    "test_nn_RReLU_with_up_down": "Unsupported op(s): aten::rrelu",
    "test_nn_LogSigmoid": "Unsupported op(s): aten::log_sigmoid",
    "test_nn_Softplus": "Unsupported op(s): aten::softplus",
    "test_nn_Softplus_beta": "Unsupported op(s): aten::softplus",
    "test_nn_Softplus_beta_threshold": "Unsupported op(s): aten::softplus",
    "test_nn_Softshrink": "Unsupported op(s): aten::softshrink",
    "test_nn_PoissonNLLLoss_no_reduce": "Unsupported op(s): aten::poisson_nll_loss",
    "test_nn_BCELoss_no_reduce": "Unsupported op(s): aten::type_as aten::type_as aten::binary_cross_entropy_with_logits",
    "test_nn_BCEWithLogitsLoss_no_reduce": "Unsupported op(s): aten::type_as aten::binary_cross_entropy_with_logits aten::kl_div",
    "test_nn_KLDivLoss_no_reduce": "Unsupported op(s): aten::kl_div aten::kl_div",
    "test_nn_KLDivLoss_no_reduce_log_target": "Unsupported op(s): aten::kl_div aten::type_as",
    "test_nn_NLLLoss_no_reduce_ignore_index": "Unsupported op(s): aten::type_as",
    "test_nn_NLLLoss_no_reduce_weights": "Unsupported op(s): aten::type_as",
    "test_nn_NLLLoss_no_reduce_weights_ignore_index": "Unsupported op(s): aten::type_as",
    "test_nn_NLLLoss_no_reduce_weights_ignore_index_neg": "Unsupported op(s): aten::type_as",
    "test_nn_NLLLoss2d_no_reduce": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_NLLLoss2d_no_reduce_weights": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_NLLLoss2d_no_reduce_ignore_index": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_NLLLossNd_no_reduce": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_NLLLossNd_no_reduce_weights": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_NLLLossNd_no_reduce_ignore_index": "Unsupported op(s): aten::type_as aten::nll_loss2d",
    "test_nn_SmoothL1Loss_no_reduce": "Unsupported op(s): aten::smooth_l1_loss aten::type_as aten::multilabel_margin_loss",
    "test_nn_MultiLabelMarginLoss_index_neg": "Unsupported op(s): aten::type_as aten::multilabel_margin_loss ",
    "test_nn_MultiLabelMarginLoss_no_reduce": "Unsupported op(s): aten::type_as aten::multilabel_margin_loss",
    "test_nn_HingeEmbeddingLoss_no_reduce": "Unsupported op(s): aten::type_as aten::hinge_embedding_loss",
    "test_nn_HingeEmbeddingLoss_margin_no_reduce": "Unsupported op(s): aten::type_as aten::hinge_embedding_loss",
    "test_nn_SoftMarginLoss_no_reduce": "Unsupported op(s): aten::soft_margin_loss",
    "test_nn_MultiLabelSoftMarginLoss_no_reduce": "Unsupported op(s): aten::log_sigmoid",
    "test_nn_MultiLabelSoftMarginLoss_weights_no_reduce": "Unsupported op(s): aten::log_sigmoid",
    "test_nn_MultiMarginLoss_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_MultiMarginLoss_1d_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_multimarginloss_1d_input_0d_target_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_MultiMarginLoss_p_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_MultiMarginLoss_margin_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_MultiMarginLoss_weights_no_reduce": "Unsupported op(s): aten::type_as aten::multi_margin_loss",
    "test_nn_InstanceNorm1d": "Unsupported op(s): aten::instance_norm",
    "test_nn_InstanceNorm1d_tracking_stats": "Unsupported op(s): aten::instance_norm",
    "test_nn_InstanceNorm2d": "Unsupported op(s): aten::instance_norm",
    "test_nn_InstanceNorm2d_tracking_stats": "Unsupported op(s): aten::instance_norm",
    "test_nn_InstanceNorm3d": "Unsupported op(s): aten::instance_norm",
    "test_nn_PixelShuffle": "Unsupported op(s): aten::pixel_shuffle",
    "test_nn_AdaptiveMaxPool1d": "Unsupported op(s): aten::adaptive_max_pool1d aten::adaptive_max_pool3d ",
    "test_nn_AdaptiveMaxPool3d_tuple": "Unsupported op(s): aten::adaptive_max_pool3d",
    "test_nn_AdaptiveMaxPool3d_tuple_none": "Unsupported op(s): aten::adaptive_max_pool3d",
    "test_nn_AdaptiveMaxPool3d_single_nonatomic": "Unsupported op(s): aten::adaptive_max_pool3d",
    "test_nn_AdaptiveMaxPool3d_tuple_nonatomic": "Unsupported op(s): aten::adaptive_max_pool3d",
    "test_nn_AdaptiveAvgPool1d": "Unsupported op(s): aten::adaptive_avg_pool1d",
    "test_nn_AdaptiveAvgPool1d_one_output": "Unsupported op(s): aten::adaptive_avg_pool1d aten::adaptive_avg_pool3d",
    "test_nn_AdaptiveAvgPool3d_tuple": "Unsupported op(s): aten::adaptive_avg_pool3d",
    "test_nn_AdaptiveAvgPool3d_tuple_none": "Unsupported op(s): aten::adaptive_avg_pool3d aten::celu aten::glu",
    "test_nn_GLU_dim": "Unsupported op(s): aten::glu aten::im2col",
    "test_nn_Fold": "Unsupported op(s): aten::col2im",
    "test_nn_Unfold_int_input": "Unsupported op(s): aten::im2col",
    "test_nn_Fold_int_input": "Unsupported op(s): aten::col2im",
    "test_nn_LSTMCell": "Unsupported op(s): aten::sigmoid_ aten::tanh_",
    "test_nn_GRUCell": "Unsupported op(s): aten::sigmoid_ aten::tanh_",
    "test_nn_BCEWithLogitsLoss_legacy_enum": "Unsupported op(s): aten::type_as aten::binary_cross_entropy_with_logits",
    "test_nn_KLDivLoss_with_target_no_reduce": "Unsupported op(s): aten::kl_div",
    "test_nn_KLDivLoss_with_log_target_no_reduce": "Unsupported op(s): aten::kl_div",
    "test_nn_NLLLoss_no_reduce": "Unsupported op(s): aten::type_as",
    "test_nn_MultiLabelMarginLoss_1d_no_reduce": "Unsupported op(s): aten::type_as aten::multilabel_margin_loss",
    "test_nn_AdaptiveMaxPool3d_single": "Unsupported op(s): aten::adaptive_max_pool3d",
    "test_nn_AdaptiveAvgPool3d_single": "Unsupported op(s): aten::adaptive_avg_pool3d",
    "test_nn_CELU": "Unsupported op(s): aten::celu",
    "test_nn_GLU": "Unsupported op(s): aten::glu",
    "test_nn_Unfold": "Unsupported op(s): aten::im2col",

    "test_nn_interpolate_linear_1d": "Upsample mode not supported",
    "test_nn_interpolate_linear_tuple_1d": "Upsample mode not supported",
    "test_nn_interpolate_linear_scale_1d": "Upsample mode not supported",
    "test_nn_interpolate_linear_1d_zero_dim": "Upsample mode not supported",
    "test_nn_interpolate_linear_1d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_linear_scale_1d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_2d": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_2d_zero_dim": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_tuple_2d": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_scale_2d": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_scale_tuple_shared_2d": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_scale_tuple_skewed_2d": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_tuple_2d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_bilinear_scale_tuple_skewed_2d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_2d": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_2d_zero_dim": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_tuple_2d": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_scale_2d": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_scale_tuple_shared_2d": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_scale_tuple_skewed_2d": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_tuple_2d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_bicubic_scale_tuple_skewed_2d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_3d": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_3d_zero_dim": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_tuple_3d": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_scale_3d": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_tuple_3d_align_corners": "Upsample mode not supported",
    "test_nn_interpolate_trilinear_scale_3d_align_corners": "Upsample mode not supported",

    "test_nn_EmbeddingBag_mean": "PopartCanonicalization: Unsupported arrange op",
    "test_nn_EmbeddingBag_sum": "PopartCanonicalization: Unsupported arrange op",
    "test_nn_EmbeddingBag_max": "PopartCanonicalization: Unsupported arrange op",
    "test_nn_EmbeddingBag_sparse": "PopartCanonicalization: Unsupported arrange op",
    "test_nn_Embedding_sparse": "PopartCanonicalization: Unsupported aten::embedding operation",

    "test_nn_Padding1221_2dcircular": "Takes too long",
    "test_nn_Padding2322_2dcircular": "Takes too long",
    "test_nn_Padding3331_2dcircular": "Takes too long",
    }

HALF_EXPECTED_FAILURES = {
    "test_nn_AvgPool1d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool1d_stride": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool2d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool2d_stride": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_LPPool2d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_LPPool1d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_LocalResponseNorm_1d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_LocalResponseNorm_2d_uneven_pad": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool3d": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool3d_stride": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_AvgPool3d_stride1_pad0_gpu_input": "Trying to connect tensor of type 'float' to field of type half",
    "test_nn_BatchNorm3d_3d_simple_average": "AssertionError: With rtol=0.05 and atol=0.0001, found 384 element(s) (out of 384) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 30.140776455402374 (0.9842235445976257 vs. 31.125), which occurred at index (1, 0, 2, 2, 3).",
    "test_nn_BatchNorm3d": "AssertionError: With rtol=0.05 and atol=0.0001, found 384 element(s) (out of 384) whose difference(s) exceeded the margin of error (including 0 nan comparisons). The greatest difference was 312.5105660557747 (0.9894339442253113 vs. 313.5), which occurred at index (1, 2, 2, 1, 1).",

    }

HALF_PRECISION_EXCEPTIONS = {
    "test_nn_Conv1d_dilated": (0.05, 1e-3),
    "test_nn_Conv3d_groups": (0.05, 1e-3),
    "test_nn_LayerNorm_1d_elementwise_affine": (0.05, 0.002),
    "test_nn_LayerNorm_3d_elementwise_affine": (0.05, 0.002)
    }

# pylint: enable=line-too-long
# yapf: enable

all_tests = {}
# Inspired from torch/testing/_internal/jit_metaprogramming_utils.py
for test in get_all_nn_module_tests():
    test_name = get_nn_mod_test_name(**test)

    name = get_nn_module_name_from_kwargs(**test)
    if "constructor_args_fn" in test:
        args = test["constructor_args_fn"]()
    else:
        args = test.get("constructor_args", ())

    if "constructor" in test:
        module = test["constructor"](*args)
    else:
        module = getattr(torch.nn, name)(*args)

    module.eval()

    if 'input_fn' in test:
        input = test['input_fn']()
    elif "input" in test:
        input = (test.get("input"), )
    else:
        input = (torch.rand(test['input_size'], dtype=torch.float), )
    if 'extra_args' in test:
        input = input + test['extra_args']
    if 'target_size' in test:
        input = input + (test['target_size'], )
    elif 'target_fn' in test:
        input = input + (test['target_fn'](), )

    if not isinstance(input, tuple):
        input = (input, )

    assert test_name not in all_tests
    all_tests[test_name] = (module, input)


@pytest.mark.parametrize("test_name", all_tests.keys())
@pytest.mark.parametrize("use_half", [False, True])
def test_pytorch_nn(test_name, use_half):
    reason = EXPECTED_FAILURES.get(test_name)
    if reason is None and use_half:
        reason = HALF_EXPECTED_FAILURES.get(test_name)
    if reason:
        pytest.skip(reason)

    print(f"Running {test_name}", flush=True)
    model, inputs = all_tests[test_name]
    model = model.float()
    inputs = [
        i.float()
        if isinstance(i, torch.Tensor) and i.is_floating_point() else i
        for i in inputs
    ]

    ref = model(*inputs)
    rtol = None
    atol = None

    if use_half:
        model = model.half()
        inputs = [
            i.half()
            if isinstance(i, torch.Tensor) and i.is_floating_point() else i
            for i in inputs
        ]
        rtol, atol = HALF_PRECISION_EXCEPTIONS.get(test_name, (0.05, 1e-4))

    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(*inputs)

    assert ref.size() == poptorch_out.size()
    torch.testing.assert_allclose(ref.float(),
                                  poptorch_out.float(),
                                  rtol=rtol,
                                  atol=atol)


if __name__ == "__main__":
    assert len(sys.argv) == 2, f"Usage {sys.argv[0]} test_name"

    # Disable expected failures:
    EXPECTED_FAILURES.clear()
    HALF_EXPECTED_FAILURES.clear()

    test_pytorch_nn(sys.argv[1], os.environ.get("HALF", "0") == "1")