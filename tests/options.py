#!/usr/bin/env python3
# Copyright (c) 2020 Graphcore Ltd. All rights reserved.

import torch
import torch.nn as nn
import numpy as np
import poptorch
import poptorch.testing
import pytest
import unittest.mock


def test_jit_script():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    # Create our model.
    model = Network()
    opts = poptorch.Options()
    opts.Jit.traceModel(False)
    inference_model = poptorch.inferenceModel(model, opts)

    x = torch.ones(2)
    y = torch.zeros(2)

    ipu = inference_model(x, y)
    ref = model(x, y)
    assert poptorch.testing.allclose(
        ref, ipu), "%s doesn't match the expected output %s" % (ipu, ref)


def test_set_options():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    # Create our model.
    model = Network()
    opts = poptorch.Options()
    # Just set a bunch of options and check they're successfully parsed.
    opts.deviceIterations(1).enablePipelining(False).replicationFactor(
        1).logDir("/tmp").profile(False)
    inference_model = poptorch.inferenceModel(model, opts)

    x = torch.ones(2)
    y = torch.zeros(2)

    ipu = inference_model(x, y)


def test_set_popart_options():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    # Create our model.
    model = Network()
    opts = poptorch.Options()
    opts.Popart.set("hardwareInstrumentations", set([0, 1]))
    opts.Popart.set("dotChecks", [0, 1])
    opts.Popart.set("engineOptions", {
        "debug.allowOutOfMemory": "true",
        "exchange.streamBufferOverlap": "any"
    })
    opts.Popart.set("customCodelets", [])
    opts.Popart.set("autoRecomputation", 1)
    opts.Popart.set("cachePath", "/tmp")
    opts.Popart.set("enableOutlining", True)
    inference_model = poptorch.inferenceModel(model, opts)
    x = torch.ones(2)
    y = torch.zeros(2)

    ipu = inference_model(x, y)


@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_real_ipu_selection():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    model = Network()
    # Force-disable the IPU model
    opts = poptorch.Options().useIpuModel(False)
    inference_model = poptorch.inferenceModel(model, opts)
    x = torch.ones(2)
    y = torch.zeros(2)

    ipu = inference_model(x, y)


@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_ipu_id_selection():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    model = Network()
    # Force-disable the IPU model
    opts = poptorch.Options().useIpuId(0)
    inference_model = poptorch.inferenceModel(model, opts)
    x = torch.ones(2)
    y = torch.zeros(2)

    ipu = inference_model(x, y)


@unittest.mock.patch.dict("os.environ", {"POPTORCH_IPU_MODEL": "0"})
def test_offline_ipu():
    class Network(nn.Module):
        def forward(self, x, y):
            return x + y

    model = Network()
    # Force-disable the IPU model
    opts = poptorch.Options().useOfflineIpuTarget()
    inference_model = poptorch.inferenceModel(model, opts)
    x = torch.ones(2)
    y = torch.zeros(2)

    #TODO(T23447): Support offline compilation
    #ipu = inference_model(x, y)
    #assert not ipu, "Offline compilation shouldn't return anything"