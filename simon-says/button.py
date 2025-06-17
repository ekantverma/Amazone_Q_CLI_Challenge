"""Interactive coloured button with animation and optional sound."""

import pygame, math
from dataclasses import dataclass

@dataclass
class Button:
    rect:   pygame.Rect
    dark_c: tuple[int, int, int]
    light_c: tuple[int, int, int]
    sound:  pygame.mixer.Sound | None = None

    _lit_until: int = 0
    _scale: float = 1.0
    _colour: tuple[int, int, int] = (0,0,0)

    def __post_init__(self):
        self._colour = self.dark_c

    def light_up(self, now: int, ms: int = 450):
        self._lit_until = now + ms
        if self.sound:
            self.sound.play(fade_ms=25)

    def update(self, now: int):
        if now < self._lit_until:
            t = (self._lit_until - now) / 450  # 1 → 0
            self._colour = tuple(int(self.light_c[i]*t + self.dark_c[i]*(1-t)) for i in range(3))
            self._scale  = 1.0 + 0.12 * t
        else:
            self._colour, self._scale = self.dark_c, 1.0

    def draw(self, surf: pygame.Surface):
        r = self.rect.inflate(self.rect.w*(self._scale-1), self.rect.h*(self._scale-1))
        pygame.draw.rect(surf, self._colour, r, border_radius=22)
        pygame.draw.rect(surf, (255,255,255), r, width=3, border_radius=22)

    def collide(self, pos):
        return self.rect.collidepoint(pos)