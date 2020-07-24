#!/usr/bin/env python3
# Copyright (c) 2020 Graphcore Ltd. All rights reserved.
import torch
import poptorch
import torch.optim as optim
import pytest
import json
from io import StringIO


@pytest.mark.parametrize("opt", [optim.SGD, optim.Adam])
def test_optimizer(opt):
    torch.manual_seed(42)

    model = torch.nn.Linear(10, 10)

    # "Train" with learning rate of zero and check the loss remains the same.
    optimizer = opt(model.parameters(), lr=0.00)

    poptorch_model = poptorch.trainingModel(
        model,
        loss=torch.nn.CrossEntropyLoss(reduction="mean"),
        optimizer=optimizer)

    input = torch.randn(1, 10)
    label = torch.randint(0, 10, [1])

    # Make sure the first run doesn't already pass the test.
    original, original_loss = poptorch_model(input, label)

    # Loss shouldn't change.
    for i in range(0, 50):
        out, loss = poptorch_model(input, label)
        assert loss == original_loss

    # We shouldn't get the right result.
    assert not torch.argmax(out, dim=1) == label

    # Update the optimizer and check the loss now begins to decrease.
    optimizer = opt(model.parameters(), lr=0.01)
    poptorch_model.setOptimizer(optimizer)
    poptorch_model(input, label)

    for i in range(0, 1000):
        out, loss = poptorch_model(input, label)

    # Check we have trained the "model"
    assert loss < original_loss
    assert loss < 0.03
    assert torch.argmax(out, dim=1) == label


@pytest.mark.parametrize("opt", [optim.SGD, optim.Adam])
def test_sgd_IR(opt):
    torch.manual_seed(42)
    model = torch.nn.Linear(10, 10)

    # "Train" with learning rate of zero and check the loss remains the same.
    optimizer = opt(model.parameters(), lr=0.01)

    poptorch_model = poptorch.trainingModel(
        model,
        loss=torch.nn.CrossEntropyLoss(reduction="mean"),
        optimizer=optimizer)

    input = torch.randn(1, 10)
    label = torch.randint(0, 10, [1])

    original, original_loss = poptorch_model(input, label)

    as_json = json.load(StringIO(poptorch_model._debugGetPopartIR()))

    AdamVarUpdate = 0
    AdamUpdater = 0
    SGD0VarUpdate = 0
    for name in as_json:
        assert name == "maingraph"
        for op in as_json[name]:
            if op['type'] == "AdamUpdater":
                AdamUpdater += 1
            elif op['type'] == "AdamVarUpdate":
                AdamVarUpdate += 1
            elif op['type'] == "SGD0VarUpdate":
                SGD0VarUpdate += 1

    if opt == optim.SGD:
        assert SGD0VarUpdate == 2
        assert AdamVarUpdate == 0 and AdamUpdater == 0
    else:
        assert SGD0VarUpdate == 0
        assert AdamVarUpdate == 2 and AdamUpdater == 2
