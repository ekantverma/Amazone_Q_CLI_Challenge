"""Main game logic and state management for Simon Says Pro."""

import pygame, random, json, pathlib
from constants import *
from button import Button
from audio import make_tone
from effects import ParticleSystem

class SimonGame:
    START, SHOW, PLAY, GAMEOVER = range(4)

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simon Says Pro")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_big   = pygame.font.SysFont(None, 80, bold=True)
        self.font_med   = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 30)

        # Buttons layout – hexagon style (3 rows)
        offs = BTN_SIZE + MARGIN
        layout = [
            (-offs/2, -offs*1.2), (offs/2, -offs*1.2),  # row 1 (2)
            (-offs,     0),       (offs,     0),        # row 2 (2)
            (-offs/2,  offs*1.2), (offs/2,  offs*1.2)   # row 3 (2)
        ]
        self.buttons: list[Button] = []
        for i, (dx, dy) in enumerate(layout):
            rect = pygame.Rect(0,0, BTN_SIZE, BTN_SIZE)
            rect.center = (CENTER_X + dx, CENTER_Y + dy)
            dark, light = BUTTON_COLOURS[i]
            tone = make_tone(BUTTON_FREQS[i])
            self.buttons.append(Button(rect, dark, light, tone))

        # Game vars
        self.state          = self.START
        self.pattern        : list[int] = []
        self.player_idx     = 0
        self.score          = 0
        self.best           = self._load_best()
        self.show_next_ms   = 0
        self.show_idx       = -1
        self.deadline_ms    = 0

        # Sounds
        self.s_success = make_tone(880, .18)
        self.s_fail    = make_tone(120, .8)

        # Particles
        self.fx = ParticleSystem()

    # ---------------- Best score persistence -----------------
    def _load_best(self):
        f = pathlib.Path('simon_score.json')
        if f.exists():
            try:
                return json.loads(f.read_text())['best']
            except: pass
        return 0
    def _save_best(self):
        pathlib.Path('simon_score.json').write_text(json.dumps({'best': self.best}))

    # ---------------- Game flow helpers ----------------------
    def _add_step(self):
        self.pattern.append(random.randrange(len(self.buttons)))

    def start(self):
        self.pattern.clear(); self.score = 0
        self._add_step()
        self.state = self.SHOW; self.show_idx = -1
        self.show_next_ms = pygame.time.get_ticks() + 700

    def _fail(self):
        self.state = self.GAMEOVER
        if self.s_fail: self.s_fail.play()
        self.fx.burst(CENTER_X, CENTER_Y, [b.light_c for b in self.buttons], 180)
        self.best = max(self.best, self.score)
        self._save_best()

    # ---------------- Main loop ------------------------------
    def run(self):
        running=True
        while running:
            now = pygame.time.get_ticks()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running=False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1:
                    self._click(ev.pos, now)

            # state updates
            if self.state == self.SHOW and now >= self.show_next_ms:
                self.show_idx += 1
                if self.show_idx == len(self.pattern):
                    self.state = self.PLAY; self.player_idx = 0
                    self.deadline_ms = now + PLAYER_TIME_MS
                else:
                    idx = self.pattern[self.show_idx]
                    self.buttons[idx].light_up(now)
                    self.show_next_ms = now + 550

            elif self.state == self.PLAY and now > self.deadline_ms:
                self._fail()

            for b in self.buttons:
                b.update(now)
            self.fx.update()

            # draw
            self._draw(now)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    # ---------------- Input handling -------------------------
    def _click(self, pos, now):
        if self.state == self.START:
            self.start(); return
        if self.state == self.GAMEOVER:
            self.state = self.START; return
        if self.state != self.PLAY:
            return
        for idx, b in enumerate(self.buttons):
            if b.collide(pos):
                b.light_up(now, 300)
                if idx == self.pattern[self.player_idx]:
                    # correct
                    self.player_idx += 1
                    self.deadline_ms = now + PLAYER_TIME_MS
                    if self.player_idx == len(self.pattern):
                        self.score += 1
                        if self.s_success: self.s_success.play()
                        self.fx.burst(*b.rect.center, [b.light_c], 80)
                        self._add_step()
                        self.state = self.SHOW; self.show_idx = -1
                        self.show_next_ms = now + 900
                else:
                    self._fail()
                break

    # ---------------- Drawing --------------------------------
    def _draw(self, now):
        self.screen.fill((18,18,18))
        # subtle bg gradient
        for y in range(0, HEIGHT, 3):
            shade = 18 + y*4//HEIGHT
            pygame.draw.line(self.screen,(shade,shade,shade),(0,y),(WIDTH,y))

        for b in self.buttons:
            b.draw(self.screen)
        self.fx.draw(self.screen)

        if self.state == self.START:
            self._text_center("SIMON SAYS PRO", self.font_big, WHITE, -160)
            self._text_center("Click to start", self.font_med, WHITE, -60)
            self._text_center(f"High score: {self.best}", self.font_small, WHITE, 40)
        elif self.state == self.SHOW:
            self._text_center("Watch the pattern…", self.font_med, WHITE, -280)
        elif self.state == self.PLAY:
            rem = max(0, self.deadline_ms - now); bar = rem/PLAYER_TIME_MS
            pygame.draw.rect(self.screen, (50,50,50), (CENTER_X-160, HEIGHT-45, 320, 18), border_radius=9)
            pygame.draw.rect(self.screen, (255*(1-bar),255*bar,0), (CENTER_X-160, HEIGHT-45, int(320*bar), 18), border_radius=9)
        elif self.state == self.GAMEOVER:
            self._text_center("Game Over", self.font_big, RED, -130)
            self._text_center(f"Score: {self.score}", self.font_med, WHITE, -40)
            self._text_center("Click to play again", self.font_small, WHITE, 50)

        if self.state in (self.PLAY, self.SHOW):
            s_txt = self.font_small.render(f"Score: {self.score}", True, WHITE)
            self.screen.blit(s_txt, (20,20))

    def _text_center(self, txt, font, col, y_off=0):
        surf = font.render(txt, True, col)
        self.screen.blit(surf, (CENTER_X - surf.get_width()//2, CENTER_Y + y_off))
