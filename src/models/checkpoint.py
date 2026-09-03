"""Checkpoint save/load (Module Interface Spec Section 4, Data Dictionary
Section 5).

A checkpoint is a dict, not raw weights, so load_checkpoint can fail fast on
a mismatch -- loading against the wrong track's label map produces
confident, entirely meaningless predictions (ADR-0001).
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn

from src.config import Track

REQUIRED_KEYS = frozenset({
    "model_state_dict", "optimizer_state_dict", "epoch", "val_metric",
    "embedding_dim", "git_tag", "track", "num_families", "seed",
})


class CheckpointMismatchError(RuntimeError):
    """Raised when a checkpoint's track, embedding_dim or num_families
    disagrees with the model it is being loaded into, or with the track the
    caller expected. Failing fast here is the point: a checkpoint loaded
    against the wrong track's label map would otherwise produce confident,
    entirely meaningless predictions (ADR-0001)."""


def save_checkpoint(
    model: nn.Module,
    optimizer,
    epoch: int,
    val_metric: float,
    embedding_dim: int,
    git_tag: str,
    track: Track,
    num_families: int,
    seed: int,
    path: str,
) -> None:
    """Writes the checkpoint dict per Data Dictionary Section 5. git_tag must
    be per track (e.g. 'm1-image-malimg') -- a bare 'm1-image' is ambiguous
    and rejected."""
    if track not in git_tag:
        raise ValueError(
            f"git_tag {git_tag!r} must be per-track (e.g. '...-{track}'), "
            "not a bare stage name"
        )

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer is not None else None,
        "epoch": epoch,
        "val_metric": val_metric,
        "embedding_dim": embedding_dim,
        "git_tag": git_tag,
        "track": track,
        "num_families": num_families,
        "seed": seed,
    }

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, out_path)


def load_checkpoint(
    path: str, model: nn.Module, optimizer=None, expected_track: Track | None = None
) -> dict:
    """Loads a checkpoint and returns its metadata (everything but the state
    dicts). Fails fast if the file's embedding_dim or num_families disagrees
    with `model`, or if its track disagrees with `expected_track`.

    `expected_track` is not in the spec's listed signature, added here
    because track cannot be introspected from a bare nn.Module -- nothing
    about an ImageCNN's architecture reveals which track it was trained on,
    so the one check ADR-0001 most cares about needs the caller to state
    what it expected, not just what the model looks like.
    """
    checkpoint = torch.load(path, map_location="cpu")

    missing = REQUIRED_KEYS - checkpoint.keys()
    if missing:
        raise CheckpointMismatchError(f"checkpoint at {path} is missing fields: {sorted(missing)}")

    model_embedding_dim = getattr(model, "embedding_dim", None)
    if model_embedding_dim is not None and model_embedding_dim != checkpoint["embedding_dim"]:
        raise CheckpointMismatchError(
            f"checkpoint embedding_dim={checkpoint['embedding_dim']} does not match "
            f"model embedding_dim={model_embedding_dim} (path: {path})"
        )

    model_classifier = getattr(model, "classifier", None)
    if model_classifier is not None and hasattr(model_classifier, "out_features"):
        if model_classifier.out_features != checkpoint["num_families"]:
            raise CheckpointMismatchError(
                f"checkpoint num_families={checkpoint['num_families']} does not match "
                f"model num_families={model_classifier.out_features} (path: {path})"
            )

    if expected_track is not None and checkpoint["track"] != expected_track:
        raise CheckpointMismatchError(
            f"checkpoint track={checkpoint['track']!r} does not match "
            f"expected_track={expected_track!r} (path: {path})"
        )

    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and checkpoint["optimizer_state_dict"] is not None:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    return {k: v for k, v in checkpoint.items() if not k.endswith("_state_dict")}
