#!/usr/bin/env python3
"""
Simon Says – complete Pygame implementation
Author: ChatGPT (2025‑06‑17)
"""

import sys, random, math, time, os, pathlib

import pygame

# ========= Optional NumPy sound synthesis =========
try:
    import numpy as np
    HAS_NUMPY = True
except ModuleNotFoundError:
    HAS_NUMPY = False
# ==================================================

# ---------------- Pygame init ---------------------
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
# --------------------------------------------------

# -------------- Constants & colours ---------------
WIDTH, HEIGHT   = 800, 600
FPS             = 60
BUTTON_SIZE     = 200
MARGIN          = 24
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2 - 30

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
DARK_BG = (25,  25,  25)

RED,    DARK_RED    = (255,  40,  40), (140,  20,  20)
GREEN,  DARK_GREEN  = ( 40, 255,  40), ( 20, 140,  20)
BLUE,   DARK_BLUE   = ( 40,  40, 255), ( 20,  20, 140)
YELLOW, DARK_YELLOW = (255, 255,  40), (140, 140,  20)

BUTTON_COLOURS = [
    (DARK_RED,    RED ),
    (DARK_GREEN,  GREEN ),
    (DARK_BLUE,   BLUE ),
    (DARK_YELLOW, YELLOW),
]
BUTTON_FREQS   = [261.63, 329.63, 392.00, 523.25]   # C4, E4, G4, C5
# --------------------------------------------------

# -------------- Helper: tone generator ------------
def make_tone(freq: float, dur: float = .35, volume: float = 1.0) -> pygame.mixer.Sound | None:
    if not (HAS_NUMPY and pygame.mixer.get_init()):
        return None
    sr = 44100
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * np.linspace(1, .05, t.size)  # gentle decay
    audio = np.int16(wave * volume * 32767)
    # Convert mono to stereo if needed
    if pygame.mixer.get_init()[2] == 2:  # stereo
        audio = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(audio)

    return pygame.sndarray.make_sound(audio)
# --------------------------------------------------

class Button:
    """A colourful square that lights up and plays a tone."""
    def __init__(self, rect: pygame.Rect, dark_c, light_c, tone: pygame.mixer.Sound | None):
        self.base_rect      = rect
        self.dark_colour    = dark_c
        self.light_colour   = light_c
        self.colour         = dark_c
        self.scale          = 1.0
        self.lit_until_ms   = 0
        self.tone           = tone

    def light_up(self, now_ms: int, flash_ms=500):
        self.lit_until_ms = now_ms + flash_ms
        if self.tone:
            self.tone.play(fade_ms=20)

    def update(self, now_ms: int):
        if now_ms < self.lit_until_ms:
            progress = (self.lit_until_ms - now_ms) / 500  # 1 → 0
            self.colour = tuple(
                int(self.light_colour[i]*progress + self.dark_colour[i]*(1-progress))
                for i in range(3)
            )
            self.scale = 1.0 + 0.1 * progress
        else:
            self.colour, self.scale = self.dark_colour, 1.0

    def draw(self, surf: pygame.Surface):
        rect = self.base_rect.inflate(
            self.base_rect.w * (self.scale - 1),
            self.base_rect.h * (self.scale - 1)
        )
        pygame.draw.rect(surf, self.colour, rect, border_radius=20)
        pygame.draw.rect(surf, WHITE, rect, width=3, border_radius=20)

    def collidepoint(self, pos):
        return self.base_rect.collidepoint(pos)

class SimonGame:
    START, SHOW, PLAYER, GAMEOVER = range(4)

    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simon Says • Pygame")

        self.clock  = pygame.time.Clock()

        # Fonts
        self.font_big   = pygame.font.SysFont(None, 72)
        self.font_med   = pygame.font.SysFont(None, 40)
        self.font_small = pygame.font.SysFont(None, 28)

        # Buttons
        btn_pos = [
            (CENTER_X - BUTTON_SIZE - MARGIN//2, CENTER_Y - BUTTON_SIZE - MARGIN//2),
            (CENTER_X + MARGIN//2,               CENTER_Y - BUTTON_SIZE - MARGIN//2),
            (CENTER_X - BUTTON_SIZE - MARGIN//2, CENTER_Y + MARGIN//2),
            (CENTER_X + MARGIN//2,               CENTER_Y + MARGIN//2)
        ]
        self.buttons: list[Button] = []
        for i, (x, y) in enumerate(btn_pos):
            rect = pygame.Rect(x, y, BUTTON_SIZE, BUTTON_SIZE)
            dark, light = BUTTON_COLOURS[i]
            tone = make_tone(BUTTON_FREQS[i])
            self.buttons.append(Button(rect, dark, light, tone))

        # Game variables
        self.state          = self.START
        self.pattern        = []
        self.player_index   = 0
        self.score          = 0
        self.best_score     = 0

        self.show_idx       = -1
        self.show_next_ms   = 0          # when to flash next button
        self.response_deadline = 0       # for timer bar

        # Success / fail sounds
        self.beep_good = make_tone(880, .15)
        self.beep_bad  = make_tone(110, .7)

    # ---------- state helpers ----------
    def _add_step(self):
        self.pattern.append(random.randrange(4))

    def start_game(self):
        self.pattern.clear()
        self.score = 0
        self._add_step()
        self.state = self.SHOW
        self.show_idx = -1
        self.show_next_ms = pygame.time.get_ticks() + 800

    def game_over(self):
        self.state = self.GAMEOVER
        if self.beep_bad: self.beep_bad.play()
        self.best_score = max(self.best_score, self.score)

    # ---------- main loop ----------
    def run(self):
        while True:
            now = pygame.time.get_ticks()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._handle_click(ev.pos, now)

            # state machine
            if self.state == self.SHOW:
                if now >= self.show_next_ms:
                    self.show_idx += 1
                    if self.show_idx >= len(self.pattern):
                        # switch to player turn
                        self.state = self.PLAYER
                        self.player_index = 0
                        self.response_deadline = now + 5000
                    else:
                        btn = self.buttons[self.pattern[self.show_idx]]
                        btn.light_up(now)
                        self.show_next_ms = now + 700

            elif self.state == self.PLAYER:
                if now > self.response_deadline:
                    self.game_over()

            # update buttons
            for b in self.buttons:
                b.update(now)

            self._draw(now)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ---------- input ----------
    def _handle_click(self, pos, now):
        if self.state == self.START:
            # anywhere click starts game
            self.start_game()
            return
        if self.state == self.GAMEOVER:
            self.state = self.START
            return
        if self.state != self.PLAYER:
            return

        for idx, btn in enumerate(self.buttons):
            if btn.collidepoint(pos):
                btn.light_up(now, 300)
                if idx == self.pattern[self.player_index]:
                    # correct
                    self.player_index += 1
                    if self.player_index == len(self.pattern):
                        # round done
                        if self.beep_good: self.beep_good.play()
                        self.score += 1
                        self._add_step()
                        self.state = self.SHOW
                        self.show_idx = -1
                        self.show_next_ms = now + 1000
                    else:
                        # extend timer
                        self.response_deadline = now + 5000
                else:
                    self.game_over()
                break

    # ---------- drawing ----------
    def _draw(self, now):
        self.screen.fill(DARK_BG)

        # gradient background effect
        for y in range(0, HEIGHT, 2):
            shade = 25 + int(25 * y / HEIGHT)
            pygame.draw.line(self.screen, (shade, shade, shade), (0, y), (WIDTH, y))

        # center circle
        pygame.draw.circle(self.screen, (50, 50, 50), (CENTER_X, CENTER_Y), 55)
        pygame.draw.circle(self.screen, WHITE,            (CENTER_X, CENTER_Y), 55, 3)

        # buttons
        for b in self.buttons:
            b.draw(self.screen)

        # UI text
        if self.state == self.START:
            self._draw_center_text("SIMON SAYS", self.font_big, YELLOW, -120)
            self._draw_center_text("Click anywhere to start", self.font_med, WHITE, -30)
            if self.best_score:
                self._draw_center_text(f"High Score  {self.best_score}", self.font_small, WHITE, 40)

        elif self.state == self.SHOW:
            self._draw_center_text("Watch…", self.font_med, WHITE, -260)
        elif self.state == self.PLAYER:
            self._draw_center_text("Your turn!", self.font_med, WHITE, -260)
            # timer bar
            remain = max(0, self.response_deadline - now)
            bar_w = int(300 * remain / 5000)
            colour = (255 * (1 - remain/5000), 255 * remain/5000, 0)
            pygame.draw.rect(self.screen, (40,40,40), (CENTER_X-150, HEIGHT-50, 300, 18))
            pygame.draw.rect(self.screen, colour,     (CENTER_X-150, HEIGHT-50, bar_w, 18))
        elif self.state == self.GAMEOVER:
            self._draw_center_text("GAME OVER!", self.font_big, RED, -120)
            self._draw_center_text(f"Score  {self.score}", self.font_med, WHITE, -30)
            self._draw_center_text("Click to play again", self.font_small, WHITE, 40)

        # persistent score display during play
        if self.state in (self.SHOW, self.PLAYER):
            score_surf = self.font_med.render(f"Score  {self.score}", True, WHITE)
            self.screen.blit(score_surf, (20, 20))
            best_surf  = self.font_small.render(f"High {self.best_score}", True, WHITE)
            self.screen.blit(best_surf, (20, 60))

    def _draw_center_text(self, txt, font, colour, y_offset=0):
        surf = font.render(txt, True, colour)
        self.screen.blit(surf, (CENTER_X - surf.get_width()//2, CENTER_Y + y_offset))

# ---------------- Launch --------------------------
if __name__ == "__main__":
    SimonGame().run()
