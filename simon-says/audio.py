"""Audio helpers – generates tones on‑the‑fly with NumPy and handles mono/stereo."""

import pygame

try:
    import numpy as np
    _HAS_NUMPY = True
except ModuleNotFoundError:  # fallback – silent mode
    _HAS_NUMPY = False


def _stereo(array: "np.ndarray"):
    """Ensure (N, 2) shape for stereo mixers; duplicates mono to both channels."""
    if array.ndim == 1:
        return np.column_stack([array, array])
    return array


def make_tone(freq: float, dur: float = .35, vol: float = 1.0):
    if not (_HAS_NUMPY and pygame.mixer.get_init()):
        return None
    sr, size, ch = pygame.mixer.get_init()
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * np.linspace(1, .05, t.size)
    audio = np.int16(wave * vol * 32767)
    if ch == 2:
        audio = _stereo(audio)
    return pygame.sndarray.make_sound(audio)