"""Tests for src/models/branches.py and src/models/fusion.py using random
dummy tensors -- shape/gradient-flow contracts don't need real data.

pretrained=False everywhere except one dedicated test, so the suite doesn't
depend on network access to download ImageNet weights.
"""

from __future__ import annotations

import pytest
import torch

from src.models.branches import AudioCNN, ImageCNN
from src.models.fusion import FusionModel


def test_image_cnn_forward_and_embed_shapes_two_channel():
    model = ImageCNN(num_families=9, embedding_dim=512, pretrained=False, channels=2)
    x = torch.randn(4, 2, 224, 224)

    logits = model(x)
    embedding = model.embed(x)

    assert logits.shape == (4, 9)
    assert embedding.shape == (4, 512)


def test_image_cnn_forward_single_channel_m0():
    model = ImageCNN(num_families=25, embedding_dim=512, pretrained=False, channels=1)
    x = torch.randn(2, 1, 224, 224)

    logits = model(x)
    assert logits.shape == (2, 25)


def test_image_cnn_custom_embedding_dim_adds_projection():
    model = ImageCNN(num_families=5, embedding_dim=128, pretrained=False, channels=2)
    x = torch.randn(2, 2, 224, 224)

    embedding = model.embed(x)
    assert embedding.shape == (2, 128)


@pytest.mark.parametrize("channels", [1, 2, 3])
def test_image_cnn_pretrained_weight_averaging_shapes(channels):
    # Exercises the pretrained conv1-adaptation path; skip cleanly if the
    # ImageNet weights can't be downloaded (no network in this environment).
    try:
        model = ImageCNN(num_families=9, pretrained=True, channels=channels)
    except Exception as e:
        pytest.skip(f"pretrained weights unavailable: {e}")

    assert model.backbone.conv1.in_channels == channels
    x = torch.randn(1, channels, 224, 224)
    assert model(x).shape == (1, 9)


def test_audio_cnn_forward_and_embed_shapes():
    model = AudioCNN(num_families=9, embedding_dim=256)
    x = torch.randn(4, 1, 128, 128)

    logits = model(x)
    embedding = model.embed(x)

    assert logits.shape == (4, 9)
    assert embedding.shape == (4, 256)


def test_fusion_model_infers_branch_names_and_shapes():
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=True)

    assert fusion.branch_names == ["image", "audio"]

    inputs = {
        "image": torch.randn(2, 2, 224, 224),
        "audio": torch.randn(2, 1, 128, 128),
    }
    embedding = fusion.embed(inputs)
    logits = fusion(inputs)

    assert embedding.shape == (2, 64 + 32)
    assert logits.shape == (2, 9)


def test_fusion_model_freezes_branch_parameters():
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=True)

    for branch in fusion.branches.values():
        for p in branch.parameters():
            assert p.requires_grad is False
    for p in fusion.classifier.parameters():
        assert p.requires_grad is True


def test_fusion_model_unfrozen_allows_branch_gradients():
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=False)

    for branch in fusion.branches.values():
        for p in branch.parameters():
            assert p.requires_grad is True


def test_fusion_model_frozen_branches_get_no_gradient_after_backward():
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=True)

    inputs = {
        "image": torch.randn(2, 2, 224, 224),
        "audio": torch.randn(2, 1, 128, 128),
    }
    logits = fusion(inputs)
    logits.sum().backward()

    for branch in fusion.branches.values():
        for p in branch.parameters():
            assert p.grad is None
    assert fusion.classifier.weight.grad is not None


def test_fusion_model_train_keeps_frozen_branches_in_eval():
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=True)

    fusion.train()

    assert fusion.training is True
    for branch in fusion.branches.values():
        assert branch.training is False


def test_fusion_model_rejects_empty_branch_list():
    with pytest.raises(ValueError):
        FusionModel([], num_families=9)


def test_fusion_model_duplicate_branch_types_get_positional_names():
    a = ImageCNN(num_families=5, embedding_dim=16, pretrained=False, channels=1)
    b = ImageCNN(num_families=5, embedding_dim=16, pretrained=False, channels=1)
    fusion = FusionModel([a, b], num_families=5)

    assert fusion.branch_names == ["image", "branch1"]
