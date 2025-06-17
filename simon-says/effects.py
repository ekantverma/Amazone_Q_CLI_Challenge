"""Simple particle burst effect for success / failure feedback."""

import random, pygame

class ParticleSystem:
    def __init__(self):
        self.parts = []  # list of dicts

    def burst(self, x, y, colours, n=120):
        for _ in range(n):
            self.parts.append({
                'x': x, 'y': y,
                'vx': random.uniform(-4,4), 'vy': random.uniform(-4,4),
                'life': random.randint(30, 65),
                'c': random.choice(colours),
                's': random.randint(2, 5)
            })

    def update(self):
        for p in self.parts[:]:
            p['x'] += p['vx']; p['y'] += p['vy']
            p['vy'] += 0.05  # gravity
            p['life'] -= 1
            if p['life'] <= 0:
                self.parts.remove(p)

    def draw(self, surf):
        for p in self.parts:
            pygame.draw.circle(surf, p['c'], (int(p['x']), int(p['y'])), p['s'])
