"""Tests for src/models/checkpoint.py using dummy models -- no real training
run needed to verify the save/load contract."""

from __future__ import annotations

import pytest
import torch

from src.models.branches import AudioCNN, ImageCNN
from src.models.checkpoint import CheckpointMismatchError, load_checkpoint, save_checkpoint
from src.models.fusion import FusionModel


def _make_model_and_optimizer(num_families=9, embedding_dim=32):
    model = AudioCNN(num_families=num_families, embedding_dim=embedding_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    return model, optimizer


def test_save_and_load_round_trip(tmp_path):
    model, optimizer = _make_model_and_optimizer()
    path = tmp_path / "m2-audio-malimg-seed42.pt"

    save_checkpoint(
        model, optimizer, epoch=5, val_metric=0.83, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    fresh_model, fresh_optimizer = _make_model_and_optimizer()
    meta = load_checkpoint(str(path), fresh_model, fresh_optimizer)

    assert meta["epoch"] == 5
    assert meta["val_metric"] == 0.83
    assert meta["track"] == "malimg"
    assert meta["num_families"] == 9
    assert meta["seed"] == 42
    assert "model_state_dict" not in meta
    assert "optimizer_state_dict" not in meta


def test_loaded_weights_actually_match(tmp_path):
    model, optimizer = _make_model_and_optimizer()
    path = tmp_path / "ckpt.pt"
    save_checkpoint(
        model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    fresh_model, _ = _make_model_and_optimizer()
    load_checkpoint(str(path), fresh_model)

    for p1, p2 in zip(model.parameters(), fresh_model.parameters()):
        assert torch.equal(p1, p2)


def test_save_checkpoint_rejects_bare_stage_git_tag(tmp_path):
    model, optimizer = _make_model_and_optimizer()
    with pytest.raises(ValueError):
        save_checkpoint(
            model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
            git_tag="m2-audio", track="malimg", num_families=9, seed=42,
            path=str(tmp_path / "ckpt.pt"),
        )


def test_load_checkpoint_rejects_embedding_dim_mismatch(tmp_path):
    model, optimizer = _make_model_and_optimizer(embedding_dim=32)
    path = tmp_path / "ckpt.pt"
    save_checkpoint(
        model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    wrong_model = AudioCNN(num_families=9, embedding_dim=64)
    with pytest.raises(CheckpointMismatchError):
        load_checkpoint(str(path), wrong_model)


def test_load_checkpoint_rejects_num_families_mismatch(tmp_path):
    model, optimizer = _make_model_and_optimizer(num_families=9)
    path = tmp_path / "ckpt.pt"
    save_checkpoint(
        model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    wrong_model = AudioCNN(num_families=25, embedding_dim=32)
    with pytest.raises(CheckpointMismatchError):
        load_checkpoint(str(path), wrong_model)


def test_load_checkpoint_rejects_track_mismatch_when_expected(tmp_path):
    model, optimizer = _make_model_and_optimizer()
    path = tmp_path / "ckpt.pt"
    save_checkpoint(
        model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    fresh_model, _ = _make_model_and_optimizer()
    with pytest.raises(CheckpointMismatchError):
        load_checkpoint(str(path), fresh_model, expected_track="big2015")


def test_load_checkpoint_allows_matching_track_when_expected(tmp_path):
    model, optimizer = _make_model_and_optimizer()
    path = tmp_path / "ckpt.pt"
    save_checkpoint(
        model, optimizer, epoch=1, val_metric=0.5, embedding_dim=32,
        git_tag="m2-audio-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    fresh_model, _ = _make_model_and_optimizer()
    meta = load_checkpoint(str(path), fresh_model, expected_track="malimg")
    assert meta["track"] == "malimg"


def test_load_checkpoint_rejects_missing_fields(tmp_path):
    path = tmp_path / "bad_ckpt.pt"
    torch.save({"model_state_dict": {}, "epoch": 1}, path)

    model, _ = _make_model_and_optimizer()
    with pytest.raises(CheckpointMismatchError):
        load_checkpoint(str(path), model)


def test_checkpoint_round_trip_with_fusion_model(tmp_path):
    image_model = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    audio_model = AudioCNN(num_families=9, embedding_dim=32)
    fusion = FusionModel([image_model, audio_model], num_families=9, freeze_branches=True)
    optimizer = torch.optim.Adam(fusion.classifier.parameters(), lr=1e-3)

    path = tmp_path / "m3-bimodal-malimg.pt"
    save_checkpoint(
        fusion, optimizer, epoch=2, val_metric=0.7, embedding_dim=fusion.embedding_dim,
        git_tag="m3-bimodal-malimg", track="malimg", num_families=9, seed=42, path=str(path),
    )

    fresh_image = ImageCNN(num_families=9, embedding_dim=64, pretrained=False, channels=2)
    fresh_audio = AudioCNN(num_families=9, embedding_dim=32)
    fresh_fusion = FusionModel([fresh_image, fresh_audio], num_families=9, freeze_branches=True)
    meta = load_checkpoint(str(path), fresh_fusion)
    assert meta["embedding_dim"] == 64 + 32
