"""Fusion model (Module Interface Spec Section 3.2).

M3 = FusionModel([image_model, audio_model], num_families, freeze_branches=True)
-- the delivered fusion stage (ADR-0011: branches frozen, only the fusion
layers train). embed() is not dead weight: probe_eval (Section 5) needs M3's
fused representation with the classification head discarded, and it is what
would let M3 nest as a branch inside the paused second stage (paused
ADR-0010).
"""

from __future__ import annotations

import torch
import torch.nn as nn

from src.models.branches import AudioCNN, BranchModel, ImageCNN

# The spec's inputs example keys branches by name ('image', 'audio') but its
# constructor takes a positional list, not a name->model mapping. This fills
# that gap: known branch classes get their conventional name; anything else
# falls back to a positional name so the class still works if extended later.
_DEFAULT_BRANCH_NAMES: dict[type, str] = {
    ImageCNN: "image",
    AudioCNN: "audio",
}


def _branch_names(branch_models: list[BranchModel]) -> list[str]:
    names = []
    seen = set()
    for i, branch in enumerate(branch_models):
        name = _DEFAULT_BRANCH_NAMES.get(type(branch), f"branch{i}")
        if name in seen:
            name = f"branch{i}"
        seen.add(name)
        names.append(name)
    return names


class FusionModel(nn.Module):
    def __init__(
        self,
        branch_models: list[BranchModel],
        num_families: int,
        freeze_branches: bool = True,
    ):
        super().__init__()
        if not branch_models:
            raise ValueError("FusionModel requires at least one branch model")

        self.freeze_branches = freeze_branches
        names = _branch_names(branch_models)
        self.branches = nn.ModuleDict(dict(zip(names, branch_models)))
        self.branch_names = names

        if freeze_branches:
            for branch in self.branches.values():
                for p in branch.parameters():
                    p.requires_grad_(False)
                branch.eval()

        # Set alongside classifier so load_checkpoint can sanity-check this
        # model the same way it does ImageCNN/AudioCNN (Data Dictionary S5:
        # embedding_dim is recorded "for downstream fusion sanity-check").
        self.embedding_dim = sum(b.embedding_dim for b in branch_models)
        self.classifier = nn.Linear(self.embedding_dim, num_families)

    def train(self, mode: bool = True) -> "FusionModel":
        super().train(mode)
        if self.freeze_branches:
            # Frozen branches stay in eval mode regardless -- ADR-0011 means
            # their BatchNorm/Dropout must never update on fusion-stage data.
            for branch in self.branches.values():
                branch.eval()
        return self

    def embed(self, inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        """Returns the fused representation before the final classification
        layer (used by probe_eval and by a later fusion stage nesting this
        model as a branch)."""
        embeddings = []
        for name in self.branch_names:
            branch = self.branches[name]
            x = inputs[name]
            if self.freeze_branches:
                with torch.no_grad():
                    embeddings.append(branch.embed(x))
            else:
                embeddings.append(branch.embed(x))
        return torch.cat(embeddings, dim=1)

    def forward(self, inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        return self.classifier(self.embed(inputs))
