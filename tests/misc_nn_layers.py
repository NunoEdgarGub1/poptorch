#!/usr/bin/env python3
# Copyright (c) 2020 Graphcore Ltd. All rights reserved.
import torch
import poptorch
import torch.optim as optim

import pytest

# Linears
# torch.nn.Identity, torch.nn.Linear, torch.nn.Bilinear,

# Dropouts
# torch.nn.Dropout, torch.nn.Dropout2d, torch.nn.Dropout3d, torch.nn.AlphaDropout,

# Sparse
# torch.nn.Embedding, torch.nn.Embedding.from_pretrained, torch.nn.EmbeddingBag, torch.nn.EmbeddingBag.from_pretrained,


def test_linear():
    model = torch.nn.Linear(20, 30)
    x = torch.randn(128, 20)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    torch.testing.assert_allclose(nativeOut, poptorch_out)


def test_identity():
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            self.op = torch.nn.Identity(20, 30, 40)

        def forward(self, x, y):
            # Make the graph compile
            return self.op(x) + y

    model = Model()

    x = torch.randn(128, 20)
    y = torch.zeros_like(x)

    # Run on CPU.
    nativeOut = model(x, y)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x, y)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_dropout():
    model = torch.nn.Dropout(0.1)
    model.eval()

    x = torch.randn(128, 20)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    # Dropout depends on HW for randomness so just test size for now.
    assert nativeOut.size() == poptorch_out.size()


def test_embedding():
    model = torch.nn.Embedding(10, 3)
    x = torch.LongTensor([[1, 2, 4, 5], [4, 3, 2, 9]])

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)
