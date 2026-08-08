import pygame
import math
import random
import sys
import array

# ============================================================
# INITIALIZE
# ============================================================

pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=1,
    buffer=512
)

pygame.init()

# ============================================================
# WINDOW
# ============================================================

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bubble Shooter")

clock = pygame.time.Clock()
FPS = 60

# ============================================================
# COLORS
# ============================================================

BG = (15, 19, 40)
BOARD_COLOR = (25, 31, 60)
BORDER_COLOR = (85, 95, 140)

WHITE = (255, 255, 255)
GRAY = (150, 155, 180)

RED = (235, 65, 75)
GREEN = (65, 205, 105)
BLUE = (65, 135, 240)
YELLOW = (245, 205, 60)
PURPLE = (165, 85, 220)
ORANGE = (245, 135, 50)
PINK = (235, 90, 165)

BUBBLE_COLORS = [
    RED,
    GREEN,
    BLUE,
    YELLOW,
    PURPLE,
    ORANGE,
    PINK
]

# ============================================================
# FONTS
# ============================================================

font_title = pygame.font.SysFont("arial", 38, bold=True)
font_large = pygame.font.SysFont("arial", 36, bold=True)
font_medium = pygame.font.SysFont("arial", 23, bold=True)
font_small = pygame.font.SysFont("arial", 17)

# ============================================================
# BOARD
# ============================================================

BOARD_LEFT = 50
BOARD_RIGHT = 850
BOARD_TOP = 75
BOARD_BOTTOM = 600

# Red danger line
DANGER_LINE_Y = 570

# ============================================================
# BUBBLE
# ============================================================

RADIUS = 18
DIAMETER = RADIUS * 2
ROW_HEIGHT = 34

# ============================================================
# SHOOTER
# ============================================================

SHOOTER_X = WIDTH // 2
SHOOTER_Y = 650

SHOT_SPEED = 11

# ============================================================
# GAME VARIABLES
# ============================================================

bubbles = []

current_color = None
next_color = None

shot_bubble = None

score = 0
shots_left = 12
combo = 0

game_over = False
game_won = False

popping_bubbles = []

# ============================================================
# POP SOUND
# ============================================================

pop_sound = None


def create_pop_sound():

    global pop_sound

    try:

        sample_rate = 44100
        duration = 0.13

        samples = int(
            sample_rate * duration
        )

        sound_data = array.array("h")

        for i in range(samples):

            t = i / sample_rate

            frequency = 750 - (
                600 * (t / duration)
            )

            envelope = 1 - (
                t / duration
            )

            value = math.sin(
                2 * math.pi * frequency * t
            )

            value *= envelope
            value *= 13000

            sound_data.append(
                int(value)
            )

        pop_sound = pygame.mixer.Sound(
            buffer=sound_data.tobytes()
        )

        pop_sound.set_volume(0.35)

    except Exception:

        pop_sound = None


def play_pop_sound():

    if pop_sound is not None:

        try:
            pop_sound.play()
        except Exception:
            pass


create_pop_sound()

# ============================================================
# HELPER
# ============================================================


def distance(x1, y1, x2, y2):

    return math.hypot(
        x2 - x1,
        y2 - y1
    )


def draw_text(
    text,
    font,
    color,
    x,
    y,
    center=True
):

    surface = font.render(
        text,
        True,
        color
    )

    if center:

        rect = surface.get_rect(
            center=(x, y)
        )

    else:

        rect = surface.get_rect(
            topleft=(x, y)
        )

    screen.blit(
        surface,
        rect
    )


# ============================================================
# BUBBLE CLASS
# ============================================================


class Bubble:

    def __init__(
        self,
        x,
        y,
        color
    ):

        self.x = float(x)
        self.y = float(y)
        self.color = color

        self.vx = 0
        self.vy = 0

    def draw(self):

        pygame.draw.circle(
            screen,
            self.color,
            (
                int(self.x),
                int(self.y)
            ),
            RADIUS
        )

        # Highlight
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (
                int(self.x - 6),
                int(self.y - 7)
            ),
            4
        )

        # Border
        darker = tuple(
            max(0, c - 55)
            for c in self.color
        )

        pygame.draw.circle(
            screen,
            darker,
            (
                int(self.x),
                int(self.y)
            ),
            RADIUS,
            2
        )


# ============================================================
# GRID
# ============================================================


def grid_position(row, col):

    x = (
        BOARD_LEFT
        + RADIUS
        + col * DIAMETER
    )

    if row % 2 == 1:
        x += RADIUS

    y = (
        BOARD_TOP
        + RADIUS
        + row * ROW_HEIGHT
    )

    return x, y


# ============================================================
# CREATE BOARD
# ============================================================


def create_initial_bubbles():

    global bubbles

    bubbles = []

    rows = 8
    cols = 21

    for row in range(rows):

        for col in range(cols):

            x, y = grid_position(
                row,
                col
            )

            # Make a few holes
            if (
                row >= 4
                and random.random() < 0.12
            ):
                continue

            color = random.choice(
                BUBBLE_COLORS[:6]
            )

            bubbles.append(
                Bubble(
                    x,
                    y,
                    color
                )
            )


# ============================================================
# NEIGHBORS
# ============================================================


def get_neighbors(target):

    neighbors = []

    for bubble in bubbles:

        if bubble is target:
            continue

        if distance(
            target.x,
            target.y,
            bubble.x,
            bubble.y
        ) <= DIAMETER + 5:

            neighbors.append(bubble)

    return neighbors


# ============================================================
# MATCHING GROUP
# ============================================================


def find_matching_group(start):

    group = []
    visited = set()

    stack = [start]

    while stack:

        current = stack.pop()

        if id(current) in visited:
            continue

        visited.add(
            id(current)
        )

        if current.color != start.color:
            continue

        group.append(current)

        for neighbor in get_neighbors(
            current
        ):

            if id(neighbor) not in visited:
                stack.append(neighbor)

    return group


# ============================================================
# POP ANIMATION
# ============================================================


def add_pop_animation(bubble):

    popping_bubbles.append(
        {
            "x": bubble.x,
            "y": bubble.y,
            "color": bubble.color,
            "radius": RADIUS,
            "alpha": 255
        }
    )


def update_pop_animation():

    for item in popping_bubbles[:]:

        item["radius"] += 2.3
        item["alpha"] -= 20

        if item["alpha"] <= 0:

            popping_bubbles.remove(item)


def draw_pop_animation():

    for item in popping_bubbles:

        radius = int(
            item["radius"]
        )

        if radius <= 1:
            continue

        surface = pygame.Surface(
            (
                radius * 2 + 12,
                radius * 2 + 12
            ),
            pygame.SRCALPHA
        )

        color = (
            item["color"][0],
            item["color"][1],
            item["color"][2],
            max(0, item["alpha"])
        )

        pygame.draw.circle(
            surface,
            color,
            (
                radius + 6,
                radius + 6
            ),
            radius,
            3
        )

        screen.blit(
            surface,
            (
                int(
                    item["x"]
                    - radius
                    - 6
                ),
                int(
                    item["y"]
                    - radius
                    - 6
                )
            )
        )


# ============================================================
# FLOATING BUBBLES
# ============================================================


def remove_floating_bubbles():

    connected = set()

    stack = []

    # All bubbles connected to ceiling
    for bubble in bubbles:

        if bubble.y <= BOARD_TOP + RADIUS + 5:
            stack.append(bubble)

    while stack:

        current = stack.pop()

        if id(current) in connected:
            continue

        connected.add(
            id(current)
        )

        for neighbor in get_neighbors(
            current
        ):

            if id(neighbor) not in connected:
                stack.append(neighbor)

    floating = [
        bubble
        for bubble in bubbles
        if id(bubble) not in connected
    ]

    for bubble in floating:

        if bubble in bubbles:
            bubbles.remove(bubble)

        add_pop_animation(
            bubble
        )

    if floating:
        play_pop_sound()

    return len(floating)


# ============================================================
# SWITCH BUBBLES
# ============================================================


def switch_bubbles():

    global current_color
    global next_color

    if shot_bubble is not None:
        return

    if game_over or game_won:
        return

    current_color, next_color = (
        next_color,
        current_color
    )


# ============================================================
# AIM DIRECTION
# ============================================================


def get_aim_direction():

    mouse_x, mouse_y = pygame.mouse.get_pos()

    dx = float(
        mouse_x - SHOOTER_X
    )

    dy = float(
        mouse_y - SHOOTER_Y
    )

    length = math.hypot(
        dx,
        dy
    )

    # IMPORTANT:
    # Prevent division by zero.
    if length < 0.0001:

        return 0.0, -1.0

    dx /= length
    dy /= length

    # Never allow downward shooting
    if dy > -0.15:

        dy = -0.15

        length = math.hypot(
            dx,
            dy
        )

        if length < 0.0001:
            return 0.0, -1.0

        dx /= length
        dy /= length

    return dx, dy


# ============================================================
# AIM PATH
# ============================================================


def draw_aim_path():

    if shot_bubble is not None:
        return

    dx, dy = get_aim_direction()

    x = float(SHOOTER_X)
    y = float(SHOOTER_Y)

    points = [
        (x, y)
    ]

    remaining = 520

    # Maximum 3 segments
    for _ in range(3):

        # --------------------------------------------
        # Distance to wall
        # --------------------------------------------

        if abs(dx) < 0.0001:

            wall_distance = float("inf")

        elif dx > 0:

            wall_distance = (
                BOARD_RIGHT
                - RADIUS
                - x
            ) / dx

        else:

            wall_distance = (
                BOARD_LEFT
                + RADIUS
                - x
            ) / dx

        # --------------------------------------------
        # Distance to ceiling
        # --------------------------------------------

        if dy < -0.0001:

            ceiling_distance = (
                BOARD_TOP
                + RADIUS
                - y
            ) / dy

        else:

            ceiling_distance = float("inf")

        # --------------------------------------------
        # Choose next collision
        # --------------------------------------------

        distances = [
            remaining
        ]

        if wall_distance > 0:
            distances.append(
                abs(wall_distance)
            )

        if ceiling_distance > 0:
            distances.append(
                abs(ceiling_distance)
            )

        step = min(distances)

        if step < 0.1:
            break

        x += dx * step
        y += dy * step

        points.append(
            (x, y)
        )

        remaining -= step

        # Ceiling
        if (
            y <= BOARD_TOP
            + RADIUS
            + 1
        ):
            break

        # Wall
        if (
            x <= BOARD_LEFT
            + RADIUS
            + 1
            or
            x >= BOARD_RIGHT
            - RADIUS
            - 1
        ):

            dx *= -1

            # Move away from wall
            x += dx * 1.5

        else:

            break

        if remaining <= 0:
            break

    # ========================================================
    # DRAW DOTTED LINE
    # ========================================================

    for i in range(
        len(points) - 1
    ):

        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        segment_length = distance(
            x1,
            y1,
            x2,
            y2
        )

        if segment_length <= 0:
            continue

        dots = max(
            1,
            int(
                segment_length / 14
            )
        )

        for j in range(
            1,
            dots + 1
        ):

            ratio = j / dots

            px = (
                x1
                + (x2 - x1)
                * ratio
            )

            py = (
                y1
                + (y2 - y1)
                * ratio
            )

            pygame.draw.circle(
                screen,
                (200, 205, 225),
                (
                    int(px),
                    int(py)
                ),
                3
            )


# ============================================================
# SHOOTER
# ============================================================


def draw_shooter():

    # Base
    pygame.draw.circle(
        screen,
        (45, 50, 80),
        (
            SHOOTER_X,
            SHOOTER_Y
        ),
        32
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            SHOOTER_X,
            SHOOTER_Y
        ),
        32,
        2
    )

    # Current bubble
    pygame.draw.circle(
        screen,
        current_color,
        (
            SHOOTER_X,
            SHOOTER_Y
        ),
        RADIUS
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            SHOOTER_X - 6,
            SHOOTER_Y - 7
        ),
        4
    )


# ============================================================
# NEXT BUBBLE
# ============================================================


def draw_next_bubble():

    box_x = 735
    box_y = 615

    pygame.draw.rect(
        screen,
        (35, 40, 70),
        (
            box_x,
            box_y,
            105,
            60
        ),
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        BORDER_COLOR,
        (
            box_x,
            box_y,
            105,
            60
        ),
        2,
        border_radius=12
    )

    draw_text(
        "NEXT",
        font_small,
        WHITE,
        box_x + 30,
        box_y + 13
    )

    pygame.draw.circle(
        screen,
        next_color,
        (
            box_x + 78,
            box_y + 30
        ),
        15
    )


# ============================================================
# SHOOT
# ============================================================


def shoot():

    global shot_bubble

    if shot_bubble is not None:
        return

    if game_over or game_won:
        return

    dx, dy = get_aim_direction()

    shot_bubble = Bubble(
        SHOOTER_X,
        SHOOTER_Y,
        current_color
    )

    shot_bubble.vx = (
        dx * SHOT_SPEED
    )

    shot_bubble.vy = (
        dy * SHOT_SPEED
    )


# ============================================================
# FIND BEST POSITION
# ============================================================


def find_best_position():

    if shot_bubble is None:
        return None

    candidates = []

    # Generate grid positions
    for row in range(18):

        for col in range(21):

            x, y = grid_position(
                row,
                col
            )

            # Don't put bubbles through danger line
            if (
                y + RADIUS
                >= DANGER_LINE_Y
            ):
                continue

            valid = True

            for bubble in bubbles:

                if distance(
                    x,
                    y,
                    bubble.x,
                    bubble.y
                ) < DIAMETER - 2:

                    valid = False
                    break

            if valid:

                d = distance(
                    shot_bubble.x,
                    shot_bubble.y,
                    x,
                    y
                )

                candidates.append(
                    (
                        d,
                        x,
                        y
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0]
    )

    return candidates[0]


# ============================================================
# PLACE SHOT
# ============================================================


def place_shot_bubble():

    global shot_bubble
    global current_color
    global next_color
    global score
    global shots_left
    global combo
    global game_won

    if shot_bubble is None:
        return

    position = find_best_position()

    if position is None:

        game_over = True
        shot_bubble = None
        return

    _, x, y = position

    shot_bubble.x = x
    shot_bubble.y = y

    bubbles.append(
        shot_bubble
    )

    # ========================================================
    # MATCHES
    # ========================================================

    group = find_matching_group(
        shot_bubble
    )

    if len(group) >= 3:

        combo += 1

        score += (
            len(group) * 10
            + combo * 5
        )

        for bubble in group:

            if bubble in bubbles:

                bubbles.remove(
                    bubble
                )

                add_pop_animation(
                    bubble
                )

        # Play pop sound
        play_pop_sound()

        # Floating bubbles
        floating = (
            remove_floating_bubbles()
        )

        score += (
            floating * 20
        )

        # Bonus
        if len(group) >= 5:

            score += 50

    else:

        combo = 0

        shots_left -= 1

    # ========================================================
    # WIN
    # ========================================================

    if len(bubbles) == 0:

        game_won = True

    # ========================================================
    # NEXT BUBBLE
    # ========================================================

    current_color = next_color

    next_color = random.choice(
        BUBBLE_COLORS[:6]
    )

    shot_bubble = None


# ============================================================
# UPDATE SHOT
# ============================================================


def update_shot():

    global shot_bubble

    if shot_bubble is None:
        return

    shot_bubble.x += (
        shot_bubble.vx
    )

    shot_bubble.y += (
        shot_bubble.vy
    )

    # --------------------------------------------------------
    # LEFT WALL
    # --------------------------------------------------------

    if (
        shot_bubble.x
        <= BOARD_LEFT + RADIUS
    ):

        shot_bubble.x = (
            BOARD_LEFT + RADIUS
        )

        shot_bubble.vx = abs(
            shot_bubble.vx
        )

    # --------------------------------------------------------
    # RIGHT WALL
    # --------------------------------------------------------

    elif (
        shot_bubble.x
        >= BOARD_RIGHT - RADIUS
    ):

        shot_bubble.x = (
            BOARD_RIGHT - RADIUS
        )

        shot_bubble.vx = -abs(
            shot_bubble.vx
        )

    # --------------------------------------------------------
    # CEILING
    # --------------------------------------------------------

    if (
        shot_bubble.y
        <= BOARD_TOP + RADIUS
    ):

        shot_bubble.y = (
            BOARD_TOP + RADIUS
        )

        place_shot_bubble()
        return

    # --------------------------------------------------------
    # EXISTING BUBBLE COLLISION
    # --------------------------------------------------------

    for bubble in bubbles:

        if distance(
            shot_bubble.x,
            shot_bubble.y,
            bubble.x,
            bubble.y
        ) <= DIAMETER - 2:

            place_shot_bubble()
            return


# ============================================================
# DRAW BOARD
# ============================================================


def draw_board():

    # Main board
    pygame.draw.rect(
        screen,
        BOARD_COLOR,
        (
            BOARD_LEFT,
            BOARD_TOP,
            BOARD_RIGHT - BOARD_LEFT,
            BOARD_BOTTOM - BOARD_TOP
        ),
        border_radius=15
    )

    # Border
    pygame.draw.rect(
        screen,
        BORDER_COLOR,
        (
            BOARD_LEFT,
            BOARD_TOP,
            BOARD_RIGHT - BOARD_LEFT,
            BOARD_BOTTOM - BOARD_TOP
        ),
        3,
        border_radius=15
    )

    # ========================================================
    # DANGER LINE
    # ========================================================

    pygame.draw.line(
        screen,
        RED,
        (
            BOARD_LEFT,
            DANGER_LINE_Y
        ),
        (
            BOARD_RIGHT,
            DANGER_LINE_Y
        ),
        4
    )

    # Warning marks
    for x in range(
        BOARD_LEFT,
        BOARD_RIGHT,
        25
    ):

        pygame.draw.line(
            screen,
            (255, 120, 120),
            (
                x,
                DANGER_LINE_Y
            ),
            (
                x + 12,
                DANGER_LINE_Y
            ),
            2
        )

    draw_text(
        "DANGER",
        font_small,
        (255, 120, 120),
        BOARD_RIGHT - 45,
        DANGER_LINE_Y - 18
    )

    # Bubbles
    for bubble in bubbles:

        bubble.draw()


# ============================================================
# UI
# ============================================================


def draw_ui():

    draw_text(
        "BUBBLE SHOOTER",
        font_title,
        WHITE,
        WIDTH // 2,
        32
    )

    draw_text(
        f"SCORE: {score}",
        font_medium,
        WHITE,
        90,
        32
    )

    draw_text(
        f"SHOTS: {shots_left}",
        font_medium,
        WHITE,
        790,
        32
    )

    if combo > 1:

        draw_text(
            f"COMBO x{combo}",
            font_medium,
            YELLOW,
            WIDTH // 2,
            635
        )


# ============================================================
# CONTROLS
# ============================================================


def draw_controls():

    draw_text(
        "LEFT CLICK = SHOOT",
        font_small,
        GRAY,
        145,
        680
    )

    draw_text(
        "SPACE = SWITCH",
        font_small,
        GRAY,
        350,
        680
    )

    draw_text(
        "R = RESTART",
        font_small,
        GRAY,
        545,
        680
    )


# ============================================================
# END SCREEN
# ============================================================


def draw_end_screen():

    overlay = pygame.Surface(
        (
            WIDTH,
            HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            0,
            200
        )
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    if game_won:

        draw_text(
            "YOU WIN!",
            font_large,
            YELLOW,
            WIDTH // 2,
            275
        )

        draw_text(
            "Amazing shooting!",
            font_medium,
            WHITE,
            WIDTH // 2,
            325
        )

    else:

        draw_text(
            "GAME OVER",
            font_large,
            RED,
            WIDTH // 2,
            275
        )

        draw_text(
            "The bubbles reached the danger line!",
            font_medium,
            WHITE,
            WIDTH // 2,
            325
        )

    draw_text(
        f"FINAL SCORE: {score}",
        font_medium,
        WHITE,
        WIDTH // 2,
        380
    )

    draw_text(
        "Press R to play again",
        font_medium,
        WHITE,
        WIDTH // 2,
        435
    )


# ============================================================
# RESTART
# ============================================================


def restart_game():

    global current_color
    global next_color
    global shot_bubble

    global score
    global shots_left
    global combo

    global game_over
    global game_won

    global popping_bubbles

    current_color = random.choice(
        BUBBLE_COLORS[:6]
    )

    next_color = random.choice(
        BUBBLE_COLORS[:6]
    )

    shot_bubble = None

    score = 0
    shots_left = 12
    combo = 0

    game_over = False
    game_won = False

    popping_bubbles = []

    create_initial_bubbles()


# ============================================================
# MAIN LOOP
# ============================================================


restart_game()

running = True

while running:

    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif (
            event.type
            == pygame.MOUSEBUTTONDOWN
        ):

            if event.button == 1:

                shoot()

        elif (
            event.type
            == pygame.KEYDOWN
        ):

            # Switch bubbles
            if (
                event.key
                == pygame.K_SPACE
            ):

                switch_bubbles()

            # Restart
            elif (
                event.key
                == pygame.K_r
            ):

                restart_game()

            # Exit
            elif (
                event.key
                == pygame.K_ESCAPE
            ):

                running = False

    # ========================================================
    # UPDATE
    # ========================================================

    if not game_over and not game_won:

        update_shot()

        update_pop_animation()

        # Shots finished
        if (
            shots_left <= 0
            and shot_bubble is None
        ):

            game_over = True

        # Bottom danger line
        for bubble in bubbles:

            if (
                bubble.y + RADIUS
                >= DANGER_LINE_Y
            ):

                game_over = True
                break

    else:

        update_pop_animation()

    # ========================================================
    # DRAW
    # ========================================================

    screen.fill(BG)

    draw_ui()

    draw_board()

    draw_pop_animation()

    if not game_over and not game_won:

        draw_aim_path()

        draw_shooter()

        draw_next_bubble()

        if shot_bubble is not None:

            shot_bubble.draw()

    draw_controls()

    if game_over or game_won:

        draw_end_screen()

    pygame.display.flip()

    clock.tick(FPS)


# ============================================================
# EXIT
# ============================================================

pygame.quit()
sys.exit()