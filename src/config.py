"""Project-wide constants: seeds, tracks, stage tags, paths.

Everything here is fixed once and read everywhere else. A value that changes
after a stage is tagged invalidates that stage's cache, its checkpoint, or both,
so nothing in this module is a runtime argument.

Governed by docs/adr/. See docs/CONTEXT.md for what these words mean.
"""

from pathlib import Path
from typing import Literal

# --------------------------------------------------------------------------
# Tracks (ADR-0001)
# --------------------------------------------------------------------------
# Two independent experimental lines. Separate label spaces, splits, caches,
# checkpoints and result tables. Never merged: a model trained on a combined
# 34-class space could score well by identifying the dataset rather than the
# family, which would inflate every fusion delta this project rests on.

Track = Literal["malimg", "big2015"]
TRACKS: tuple[Track, ...] = ("malimg", "big2015")

# --------------------------------------------------------------------------
# Seeds (ADR-0013)
# --------------------------------------------------------------------------
# Three seeds per stage, always. Every headline delta is reported as mean and
# standard deviation across them. This is a requirement, not a budget target --
# on a four-stage ladder the full sweep is affordable, and a single-seed delta
# is not evidence.

SEEDS: tuple[int, ...] = (42, 43, 44)

# The split seed is separate and never swept. Splits must regenerate
# byte-identically forever; rerolling them would silently break every
# comparison in the project.
SPLIT_SEED: int = 42
SPLIT_RATIOS: tuple[float, float, float] = (0.70, 0.15, 0.15)

# --------------------------------------------------------------------------
# BIG2015 sampling (ADR-0003, protocols/big2015_sampling.md)
# --------------------------------------------------------------------------
# Separate from SPLIT_SEED: this seed decides which raw samples exist in the
# track's corpus at all, extracted once from train.7z on Kaggle. SPLIT_SEED
# later decides how those same samples get partitioned into train/val/test.

BIG2015_SAMPLE_SEED = 2015
BIG2015_SAMPLES_PER_FAMILY = 100

# --------------------------------------------------------------------------
# Stages and git tags
# --------------------------------------------------------------------------
# Tags are "{stage}-{track}". A bare "m1-image" is ambiguous and is not used.
# M4 and M5 are paused (ADR-0017); their names are reserved, not built.

STAGES: tuple[str, ...] = (
    "m0-grayscale",
    "m1-image",
    "m2-audio",
    "m3-bimodal",
)

MILESTONE_TAGS: tuple[str, ...] = (
    "ms0-foundations",
    "ms5-probe",
    "ms6-robustness",
    "submission",
)


def tag(stage: str, track: Track) -> str:
    """The git tag and checkpoint name for one stage on one track."""
    if stage not in STAGES:
        raise ValueError(
            f"unknown stage {stage!r}; expected one of {STAGES}. "
            "m4-graph and m5-trimodal are paused (ADR-0017)."
        )
    if track not in TRACKS:
        raise ValueError(f"unknown track {track!r}; expected one of {TRACKS}")
    return f"{stage}-{track}"


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE = ROOT / "data_cache"
CHECKPOINTS = ROOT / "checkpoints"
RESULTS = ROOT / "results"
LOGS = ROOT / "logs"
PROTOCOLS = ROOT / "protocols"


def registry_path(track: Track) -> Path:
    return DATA_CACHE / f"registry_{track}.csv"


def family_map_path(track: Track) -> Path:
    return DATA_CACHE / f"family_to_id_{track}.json"


def image_cache_path(sample_id: str) -> Path:
    return DATA_CACHE / "image" / f"{sample_id}.pt"


def image_offsets_path(sample_id: str) -> Path:
    # Required alongside every cached image tensor (ADR-0008) -- a tensor
    # without its offset map cannot support FR6 attribution and is invalid.
    return DATA_CACHE / "image" / f"{sample_id}.offsets.json"


def audio_cache_path(sample_id: str) -> Path:
    return DATA_CACHE / "audio" / f"{sample_id}.pt"


def checkpoint_path(stage: str, track: Track, seed: int) -> Path:
    return CHECKPOINTS / track / f"{tag(stage, track)}-seed{seed}.pt"


def metrics_path(stage: str, track: Track) -> Path:
    return RESULTS / track / f"{stage}_metrics.csv"


# --------------------------------------------------------------------------
# Embedding dimensions (Data Dictionary section 4)
# --------------------------------------------------------------------------
# Fixed before the first checkpoint is tagged. Changing one afterwards means a
# version suffix on the stage name, not an edit here.

IMAGE_EMBEDDING_DIM = 512   # ResNet18 penultimate
AUDIO_EMBEDDING_DIM = 256
FUSION_INPUT_DIM = IMAGE_EMBEDDING_DIM + AUDIO_EMBEDDING_DIM  # M3

# --------------------------------------------------------------------------
# Preprocessing (values still open are marked; see docs/adr/README.md)
# --------------------------------------------------------------------------

IMAGE_TARGET_SHAPE = (224, 224)
ENTROPY_WINDOW = 256        # OPEN until Milestone 1 -- swept, not guessed
AUDIO_SAMPLE_RATE = 16_000  # OPEN until Milestone 2
AUDIO_N_MELS = 128          # OPEN until Milestone 2

# --------------------------------------------------------------------------
# Robustness sweep (ADR-0015)
# --------------------------------------------------------------------------
# Two axes. Strength is how much junk; composition is what the junk is. The
# panels are never averaged together -- the contrast between zero and random
# padding is the second of the two findings this study exists to produce.

PADDING_STRENGTHS: tuple[float, ...] = (0.0, 0.05, 0.10, 0.20)  # OPEN until Milestone 6
JUNK_COMPOSITIONS: tuple[str, ...] = ("zero", "random")
