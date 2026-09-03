"""Branch models (Module Interface Spec Section 3.1).

Every branch implements the same forward()/embed() contract so fusion code
is branch-agnostic (Section 3.1). GraphGNN is PAUSED (V3, ADR-0017) and not
implemented here; the base contract below is written so adding it back is a
matter of adding a class, not reworking ImageCNN/AudioCNN or FusionModel.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torchvision.models as tv_models


class BranchModel(nn.Module):
    """Base contract: forward() returns class logits, embed() returns the
    penultimate-layer embedding. embedding_dim is fixed per Data Dictionary
    Section 4 and must not change after a checkpoint is tagged."""

    embedding_dim: int

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError


class ImageCNN(BranchModel):
    """ResNet18 backbone. `channels` is not in the Module Interface Spec's
    listed signature but is required to make M0 (1-channel) and M1
    (2-channel) share one class (ADR-0007) -- filling a spec gap, documented
    here rather than silently added.

    A pretrained conv1 expects 3 channels; when channels != 3 its weights are
    averaged across the input-channel dimension and replicated, the standard
    way to adapt an RGB backbone to a different channel count.
    """

    def __init__(
        self,
        num_families: int,
        embedding_dim: int = 512,
        pretrained: bool = True,
        channels: int = 2,
    ):
        super().__init__()
        self.embedding_dim = embedding_dim

        weights = tv_models.ResNet18_Weights.DEFAULT if pretrained else None
        backbone = tv_models.resnet18(weights=weights)

        if channels != 3:
            old_conv = backbone.conv1
            new_conv = nn.Conv2d(
                channels, old_conv.out_channels, kernel_size=old_conv.kernel_size,
                stride=old_conv.stride, padding=old_conv.padding, bias=False,
            )
            if pretrained:
                with torch.no_grad():
                    avg_weight = old_conv.weight.mean(dim=1, keepdim=True)  # [out, 1, k, k]
                    new_conv.weight.copy_(avg_weight.repeat(1, channels, 1, 1))
            backbone.conv1 = new_conv

        backbone_out = backbone.fc.in_features  # 512 for resnet18
        backbone.fc = nn.Identity()  # expose the penultimate embedding
        self.backbone = backbone
        self.embed_proj = (
            nn.Identity() if backbone_out == embedding_dim
            else nn.Linear(backbone_out, embedding_dim)
        )
        self.classifier = nn.Linear(embedding_dim, num_families)

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return self.embed_proj(self.backbone(x))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.embed(x))


class AudioCNN(BranchModel):
    """Small conv stack over the [1, n_mels, n_frames] Mel-spectrogram from
    audio_prep -- trained from scratch, no pretrained backbone (System
    Architecture Section 3.2 names no pretrained audio model)."""

    def __init__(self, num_families: int, embedding_dim: int = 256):
        super().__init__()
        self.embedding_dim = embedding_dim

        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1), nn.BatchNorm2d(32),
            nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64),
            nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.embed_fc = nn.Linear(128, embedding_dim)
        self.classifier = nn.Linear(embedding_dim, num_families)

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.features(x).flatten(1)
        return self.embed_fc(feats)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.embed(x))
