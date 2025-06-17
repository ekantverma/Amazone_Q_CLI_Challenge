WIDTH, HEIGHT = 800, 600         # Slightly taller to fit buttons
FPS           = 60
BTN_SIZE      = 150               # Button size reduced slightly
MARGIN        = 20
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)

RED,    DARK_RED    = (255, 70,  70), (120,  20,  20)
GREEN,  DARK_GREEN  = ( 60, 255, 60), ( 20, 120,  20)
BLUE,   DARK_BLUE   = ( 70,  70,255), ( 20,  20,120)
YELLOW, DARK_YELLOW = (255,255, 70), (120,120, 20)
CYAN,   DARK_CYAN   = ( 70,255,255), ( 20,120,120)
MAG,    DARK_MAG    = (255, 70,255), (120, 20,120)

BUTTON_COLOURS = [
    (DARK_RED,    RED),
    (DARK_GREEN,  GREEN),
    (DARK_BLUE,   BLUE),
    (DARK_YELLOW, YELLOW),
    (DARK_CYAN,   CYAN),
    (DARK_MAG,    MAG),
]

BUTTON_FREQS = [261.63, 311.13, 369.99, 415.30, 493.88, 587.33]  # C4–D#4–F#4–G#4–B4–D5

PLAYER_TIME_MS = 6000  # milliseconds to respond
