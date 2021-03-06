// Copyright (c) 2020 Graphcore Ltd. All rights reserved.

#include <torch/csrc/jit/ir/ir.h>

#include "PoptorchSymbols.hpp"
#include "poptorch/OpBuilder.hpp"
#include "poptorch/PopartCanonicalization.hpp"
#include "poptorch/Utils.hpp"
#include "poptorch_logging/Logging.hpp"
/*
  Removes losses such that the module only has one loss at the end.
  1. Finds any loss in the module.
  2. Looks through the use-def chain of that loss to see if it is used in
  another loss, if so removes it.
  3. At the end there will only be one loss used.
*/

namespace poptorch {

bool traverseUseDef(torch::jit::Node *node) {
  bool used_in_loss = false;

  // Look through the use-def chain.
  for (torch::jit::Value *output : node->outputs()) {
    // name
    for (torch::jit::Use use : output->uses()) {
      const torch::jit::Symbol kind = use.user->kind();

      // If this is a loss then |node| is used in a loss.
      if (kind == symbols::popart::identityloss) {
        used_in_loss = true;
      }

      // Uses can't be circular.
      used_in_loss |= traverseUseDef(use.user);

      // Early exit if true.
      if (used_in_loss) {
        return true;
      }
    }
  }

  return used_in_loss;
}

void removeSurplusIdentityLosses(torch::jit::Graph *graph) {
  std::unordered_set<torch::jit::Node *> to_delete;

  // For diagnostics.
  std::size_t total_found_losses = 0;
  std::size_t independent_loss_count = 0;

  // For all nodes in the IR.
  for (torch::jit::Node *node : graph->nodes()) {
    const torch::jit::Symbol kind = node->kind();

    // For each loss see if it is used in a loss.
    if (kind == symbols::popart::identityloss) {
      total_found_losses++;

      bool used_in_loss = traverseUseDef(node);

      if (used_in_loss) {
        // Remove the node by replacing it with either the input or the input
        // transformed by some operation.
        torch::jit::Node *new_node = node->input()->node();

        // If the operation was performing a reduction replace it with a manual
        // reduction operation.
        const std::size_t reduction =
            node->i(c10::Symbol::fromQualString("attr::reduction"));
        if (reduction == 0) {
          // Sum
          new_node = createSum(graph, {new_node->output()});
          new_node->moveAfter(node);
        } else if (reduction == 1) {
          // Mean
          new_node = createMean(graph, {new_node->output()});
          new_node->moveAfter(node);
        }

        node->replaceAllUsesWith(new_node);
        to_delete.insert(node);
      } else {
        independent_loss_count++;
      }
    }
  }

  logging::debug("Found {} losses and removed {}", total_found_losses,
                 total_found_losses - independent_loss_count);

  if (total_found_losses == 0) {
    logging::warn("Couldn't find a loss in graph!");
  }

  if (independent_loss_count != 1) {
    logging::warn("Multiple independent losses found in graph. Graph must have "
                  "one final loss.");
  }

  // Remove the dead nodes.
  searchAndPossiblyDestroy(to_delete);
}
} // namespace poptorch
