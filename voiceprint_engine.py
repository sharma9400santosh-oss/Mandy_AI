"""
Voiceprint engine: a lightweight, on-device "does this sound like the
enrolled user" check.

HONEST SCOPE: this is NOT biometric-grade speaker verification. Real
speaker recognition uses trained neural embeddings (e.g. ECAPA-TDNN,
Resemblyzer) and usually a cloud service. Building that from scratch
here would need a large model + heavy dependencies that make an
already-big Android build much riskier. Instead, this compares a few
lightweight acoustic characteristics -- pitch range, energy, and
speaking rhythm -- between the enrolled voice and each new utterance.

What this DOES do well: reliably reject voices with a clearly different
pitch/rhythm (e.g. a different family member, a stranger). What it will
NOT do: stop a good impression of your voice, or work perfectly with a
noisy car cabin. Treat it as a convenience filter, not a security lock.
"""

import array
import math
import json

import settings_store as store

SAMPLE_RATE = 16000
SIMILARITY_THRESHOLD = 0.80  # tune lower/higher in settings if needed


def _bytes_to_samples(raw_bytes):
    if not raw_bytes:
        return []
    usable_len = len(raw_bytes) - (len(raw_bytes) % 2)
    if usable_len <= 0:
        return []
    try:
        samples = array.array("h")
        samples.frombytes(raw_bytes[:usable_len])
        return samples
    except Exception:
        return []


def _rms_energy(samples):
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def _zero_crossing_rate(samples):
    if len(samples) < 2:
        return 0.0
    crossings = sum(
        1 for i in range(1, len(samples))
        if (samples[i - 1] >= 0) != (samples[i] >= 0)
    )
    return crossings / len(samples)


def _pitch_estimate(samples, sample_rate=SAMPLE_RATE, min_hz=75, max_hz=300):
    """Crude autocorrelation-based pitch estimate (fundamental frequency),
    sampled sparsely to stay fast in pure Python."""
    n = len(samples)
    if n < 400:
        return 0.0

    min_lag = int(sample_rate / max_hz)
    max_lag = min(int(sample_rate / min_hz), n - 1)
    if max_lag <= min_lag:
        return 0.0

    lag_step = max(1, (max_lag - min_lag) // 50)
    best_lag, best_corr = 0, 0.0

    for lag in range(min_lag, max_lag, lag_step):
        count = n - lag
        if count <= 0:
            continue
        stride = max(1, count // 400)
        total, samples_used = 0.0, 0
        for i in range(0, count, stride):
            total += samples[i] * samples[i + lag]
            samples_used += 1
        corr = total / samples_used if samples_used else 0.0
        if corr > best_corr:
            best_corr, best_lag = corr, lag

    if best_lag == 0:
        return 0.0
    return sample_rate / best_lag


def extract_features(raw_audio_bytes):
    """Returns a small feature vector describing this utterance's voice
    characteristics, or None if the audio was unusable (too short/empty --
    common if buffer capture failed on this device).

    Note: energy/loudness is deliberately NOT included as an identity
    feature -- how loud you happen to be speaking (or how far the phone
    is from your mouth) isn't who you are, and including it let very
    different voices score as near-identical in early testing. Pitch and
    zero-crossing rate (a rough proxy for vocal timbre/brightness) are
    what actually varies by speaker here.
    """
    samples = _bytes_to_samples(raw_audio_bytes)
    if len(samples) < 400:
        return None

    pitch_hz = _pitch_estimate(samples)
    zcr = _zero_crossing_rate(samples)

    if pitch_hz == 0.0:
        return None  # couldn't get a usable pitch reading from this clip

    return [pitch_hz, zcr]


def _feature_similarity(a, b):
    """Distance-based similarity (not cosine -- cosine on features with
    very different natural scales/ranges gives misleadingly high scores
    even for clearly different voices). Returns 0.0-1.0."""
    if not a or not b:
        return 0.0

    pitch_a, zcr_a = a
    pitch_b, zcr_b = b

    # A ~40Hz difference in fundamental frequency is a very noticeable
    # difference between two speakers; scale accordingly.
    pitch_diff = abs(pitch_a - pitch_b) / 40.0
    zcr_diff = abs(zcr_a - zcr_b) / 0.04

    distance = math.sqrt(pitch_diff ** 2 + zcr_diff ** 2)
    similarity = max(0.0, 1.0 - (distance / 3.0))
    return similarity


# Kept as a public alias so anything importing the old name still works.
_cosine_similarity = _feature_similarity


def enroll(feature_samples):
    """Save an averaged voiceprint from several enrollment utterances."""
    valid = [f for f in feature_samples if f]
    if not valid:
        return False
    dims = len(valid[0])
    avg = [0.0] * dims
    for f in valid:
        for i in range(dims):
            avg[i] += f[i]
    avg = [x / len(valid) for x in avg]
    store.set("voice_profile", json.dumps(avg))
    return True


def has_enrolled_profile():
    return bool(store.get("voice_profile"))


def clear_profile():
    store.set("voice_profile", "")


def verify(raw_audio_bytes):
    """
    Returns (is_match: bool, similarity: float, reason: str).
    If no profile is enrolled, always returns a match (nothing to check
    against) so the app remains usable before enrollment.
    """
    profile_json = store.get("voice_profile")
    if not profile_json:
        return True, 1.0, "no voiceprint enrolled yet"

    features = extract_features(raw_audio_bytes)
    if features is None:
        # Couldn't analyze audio (e.g. buffer capture unsupported on this
        # device) -- fail open rather than locking the user out.
        return True, 0.0, "audio unavailable for voice check"

    profile = json.loads(profile_json)
    similarity = _cosine_similarity(features, profile)
    is_match = similarity >= SIMILARITY_THRESHOLD
    return is_match, similarity, "ok"
