"""Audio branch preprocessing (Module Interface Spec Section 2; System
Architecture Section 3.2).

Treats a sample's raw byte stream as a 1D amplitude signal and computes a
fixed-size Mel-spectrogram from it via librosa. No failure mode is expected
here (Architecture Section 3.2): any byte stream, however short, is a valid
signal to librosa -- it warns on a short input rather than raising.
"""

from __future__ import annotations

import warnings

import librosa
import numpy as np
import torch

from src.config import audio_cache_path
from src.data.recover import ResizedDistributionError
from src.preprocess.raw_bytes import load_raw_bytes


def audio_prep(
    sample_id: str,
    binary_path: str,
    sample_rate: int = 16000,
    n_mels: int = 128,
    n_frames: int = 128,
) -> torch.Tensor:
    """Returns a [1, n_mels, n_frames] float32 Mel-spectrogram tensor,
    normalized to [0, 1], and caches it to data_cache/audio/{sample_id}.pt.

    Never raises on generic malformed input (missing file, truncated hex,
    empty binary) -- these degrade to an all-zero spectrogram of the
    requested shape. A `ResizedDistributionError` from the Malimg recovery
    gate is the one exception, same as image_prep: that signal exists to be
    loud (ADR-0002) and is never swallowed here.
    """
    try:
        raw = load_raw_bytes(binary_path)
    except ResizedDistributionError:
        raise
    except (OSError, ValueError):
        raw = b""

    if raw:
        signal = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        signal = (signal / 127.5) - 1.0  # [0, 255] -> [-1, 1]
    else:
        signal = np.zeros(1, dtype=np.float32)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # librosa warns on short input, never raises
        mel = librosa.feature.melspectrogram(y=signal, sr=sample_rate, n_mels=n_mels)

    mel_db = librosa.power_to_db(mel, ref=np.max) if mel.max() > 0 else mel.astype(np.float32)

    span = mel_db.max() - mel_db.min()
    mel_norm = (mel_db - mel_db.min()) / span if span > 0 else np.zeros_like(mel_db)

    t = mel_norm.shape[1]
    if t < n_frames:
        mel_norm = np.pad(mel_norm, ((0, 0), (0, n_frames - t)))
    else:
        mel_norm = mel_norm[:, :n_frames]

    tensor = torch.from_numpy(mel_norm.astype(np.float32))[None]  # [1, n_mels, n_frames]

    cache_path = audio_cache_path(sample_id)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(tensor, cache_path)

    return tensor
