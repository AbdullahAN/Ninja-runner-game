
import pygame
import random
import sys
import math

# ---------- Config ----------
WIDTH, HEIGHT = 900, 340
GROUND_Y = 290
FPS = 60
GRAVITY = 0.6
JUMP_VELOCITY = -12.0
DUCK_HEIGHT = 28
RUN_HEIGHT = 46
INIT_SPEED = 6.2
SPEED_INCREASE_EVERY = 120  # points
MAX_SPEED = 17

# Day/Night
DAY_LENGTH_MS = 18000  # each cycle ~18s (day or night)
STAR_COUNT = 60

pygame.init()
pygame.display.set_caption("Ninja Runner")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("consolas", 18)
font_big = pygame.font.SysFont("consolas", 28)

# Colors
COLORS = {
    "day_bg": (245, 249, 255),
    "night_bg": (15, 18, 28),
    "ground": (40, 40, 40),
    "ninja": (20, 20, 20),
    "accent": (220, 20, 60),  # headband
    "obstacle": (30, 30, 30),
    "ui_light": (40, 40, 40),
    "ui_dark": (230, 230, 230),
    "sun": (255, 204, 0),
    "moon": (230, 230, 255),
    "star": (220, 220, 255)
}

def lerp(a, b, t):
    return a + (b - a) * t

# ---------- Ninja ----------
class Ninja:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 80
        self.y = GROUND_Y - RUN_HEIGHT
        self.width = 42
        self.height = RUN_HEIGHT
        self.vel_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.leg_frame = 0   # 0..3
        self.anim_time = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def on_ground(self):
        return not self.is_jumping and self.height == RUN_HEIGHT

    def handle_input(self, keys):
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and not self.is_jumping:
            self.is_jumping = True
            self.vel_y = JUMP_VELOCITY
            self.is_ducking = False
        self.is_ducking = (keys[pygame.K_DOWN] and not self.is_jumping)

    def update(self, dt):
        if self.is_jumping:
            self.y += self.vel_y
            self.vel_y += GRAVITY
            if self.y >= GROUND_Y - RUN_HEIGHT:
                self.y = GROUND_Y - RUN_HEIGHT
                self.is_jumping = False
                self.vel_y = 0

        target_h = DUCK_HEIGHT if (self.is_ducking and not self.is_jumping) else RUN_HEIGHT
        if target_h != self.height:
            dy = (self.height - target_h)
            self.y += dy
            self.height = target_h

        # 4-frame run cycle
        self.anim_time += dt
        if self.anim_time > 80:  # faster for smoothness
            self.leg_frame = (self.leg_frame + 1) % 4
            self.anim_time = 0

    def _draw_arm(self, surf, color, x, y, forward=True):
        # simple swing: forward arms slightly extended
        w, h = (7, 12) if forward else (6, 10)
        pygame.draw.rect(surf, color, pygame.Rect(int(x), int(y), w, h), border_radius=2)

    def _draw_leg(self, surf, color, hip_x, hip_y, phase, mirror=False):
        """
        Draw an articulated leg with thigh + shin + small foot.
        phase: 0..3 for animation frames
        mirror: if True, mirror the forward/back offsets
        """
        # Parameters
        thigh_len = 18
        shin_len = 18
        foot_len = 8
        width = 4  # line thickness

        # Forward/back offsets per frame (simple run cycle)
        # forward leg lifts; back leg extends
        frames = [
            (10, -6),   # frame 0: forward
            (5, -2),    # frame 1: passing
            (-8, 2),    # frame 2: back
            (2, -1)     # frame 3: passing other
        ]
        fx, fy = frames[phase % 4]
        if mirror:
            fx = -fx
            fy = -fy//2  # slight asymmetry

        # Hip point
        hx, hy = int(hip_x), int(hip_y)

        # Knee point (relative)
        kx = hx + int(fx * 0.5)
        ky = hy + int(thigh_len + fy)

        # Ankle/foot point
        ax = kx + int(fx * 0.4)
        ay = ky + int(shin_len - fy)

        # Clamp to ground for subtle contact when on ground
        ground_y = GROUND_Y - 2
        if not self.is_jumping and self.height == RUN_HEIGHT:
            ay = min(ay, ground_y)

        # Draw thigh, shin
        pygame.draw.line(surf, color, (hx, hy), (kx, ky), width)
        pygame.draw.line(surf, color, (kx, ky), (ax, ay), width)

        # Foot
        foot_dir = 1 if not mirror else -1
        fx1 = ax
        fx2 = ax + foot_dir * foot_len
        pygame.draw.line(surf, color, (fx1, ay), (fx2, ay), width)

    def draw(self, surf, is_night):
        fg = COLORS["ui_dark"] if is_night else COLORS["ninja"]
        body = self.rect
        # Body (robe)
        pygame.draw.rect(surf, fg, body, border_radius=6)
        # Headband
        hb_y = self.y + 10 if self.height == RUN_HEIGHT else self.y + 6
        pygame.draw.rect(surf, COLORS["accent"], (self.x + 6, hb_y, self.width - 12, 4), border_radius=2)
        # Eye slit
        eye_color = (235, 235, 235) if not is_night else (250, 250, 250)
        pygame.draw.rect(surf, eye_color, (self.x + 24, hb_y + 6, 8, 3), border_radius=2)

        # Arms + Legs
        hip_left_x = self.x + 12
        hip_right_x = self.x + self.width - 12
        hip_y = self.y + self.height - 18  # hip height inside body
        arm_y = self.y + 16 if self.height == RUN_HEIGHT else self.y + 10

        if self.is_jumping:
            # Slightly spread legs in air
            self._draw_leg(surf, fg, hip_left_x, hip_y, phase=1, mirror=False)
            self._draw_leg(surf, fg, hip_right_x, hip_y, phase=3, mirror=True)
            # arms slightly back
            self._draw_arm(surf, fg, self.x - 4, arm_y, forward=False)
            self._draw_arm(surf, fg, self.x + self.width - 3, arm_y, forward=False)
        elif self.height == DUCK_HEIGHT:
            # Tucked posture: legs closer, arms tucked
            self._draw_leg(surf, fg, hip_left_x, hip_y, phase=1, mirror=False)
            self._draw_leg(surf, fg, hip_right_x, hip_y, phase=1, mirror=True)
            self._draw_arm(surf, fg, self.x + 4, arm_y, forward=False)
            self._draw_arm(surf, fg, self.x + self.width - 12, arm_y, forward=False)
        else:
            # 4-frame cycle: alternate which leg is forward
            if self.leg_frame == 0:
                self._draw_leg(surf, fg, hip_left_x, hip_y, phase=0, mirror=False)   # left forward
                self._draw_leg(surf, fg, hip_right_x, hip_y, phase=2, mirror=True)   # right back
                # arms opposite
                self._draw_arm(surf, fg, self.x - 4, arm_y, forward=True)
                self._draw_arm(surf, fg, self.x + self.width - 2, arm_y, forward=False)
            elif self.leg_frame == 1:
                self._draw_leg(surf, fg, hip_left_x, hip_y, phase=1, mirror=False)
                self._draw_leg(surf, fg, hip_right_x, hip_y, phase=3, mirror=True)
                self._draw_arm(surf, fg, self.x - 2, arm_y, forward=True)
                self._draw_arm(surf, fg, self.x + self.width - 6, arm_y, forward=False)
            elif self.leg_frame == 2:
                self._draw_leg(surf, fg, hip_left_x, hip_y, phase=2, mirror=False)   # left back
                self._draw_leg(surf, fg, hip_right_x, hip_y, phase=0, mirror=True)   # right forward
                self._draw_arm(surf, fg, self.x - 6, arm_y, forward=False)
                self._draw_arm(surf, fg, self.x + self.width, arm_y, forward=True)
            else:
                self._draw_leg(surf, fg, hip_left_x, hip_y, phase=3, mirror=False)
                self._draw_leg(surf, fg, hip_right_x, hip_y, phase=1, mirror=True)
                self._draw_arm(surf, fg, self.x - 2, arm_y, forward=True)
                self._draw_arm(surf, fg, self.x + self.width - 6, arm_y, forward=False)

# ---------- Obstacles ----------
class Archer:
    def __init__(self, speed):
        self.width, self.height = 28, 46
        self.x = WIDTH + 10
        self.y = GROUND_Y - self.height
        self.speed = speed

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, speed):
        self.x -= speed

    def draw(self, surf, is_night):
        col = COLORS["ui_dark"] if is_night else COLORS["obstacle"]
        pygame.draw.rect(surf, col, self.rect, border_radius=5)
        pygame.draw.arc(surf, col, (self.x - 8, self.y + 10, 20, 26), math.pi/2, 3*math.pi/2, 2)
        pygame.draw.line(surf, col, (self.x + 2, self.y + 10), (self.x + 2, self.y + 36), 1)

    def offscreen(self):
        return self.x + self.width < -10

class Tower:
    def __init__(self, speed):
        self.width = random.randint(24, 34)
        self.height = random.randint(56, 96)
        self.x = WIDTH + 10
        self.y = GROUND_Y - self.height
        self.speed = speed

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, speed):
        self.x -= speed

    def draw(self, surf, is_night):
        col = COLORS["ui_dark"] if is_night else COLORS["obstacle"]
        pygame.draw.rect(surf, col, self.rect, border_radius=2)
        step = 8
        for i in range(int(self.x), int(self.x + self.width), step):
            pygame.draw.rect(surf, col, (i, self.y - 6, step//2, 6))

    def offscreen(self):
        return self.x + self.width < -10

class Rock:
    def __init__(self, speed):
        self.width = random.randint(18, 26)
        self.height = random.randint(14, 20)
        self.x = WIDTH + 10
        self.y = GROUND_Y - self.height
        self.speed = speed

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, speed):
        self.x -= speed * 1.05

    def draw(self, surf, is_night):
        col = COLORS["ui_dark"] if is_night else COLORS["obstacle"]
        pygame.draw.polygon(
            surf, col,
            [(self.x, self.y + self.height),
             (self.x + self.width*0.2, self.y + self.height*0.4),
             (self.x + self.width*0.6, self.y + self.height*0.2),
             (self.x + self.width, self.y + self.height),
             (self.x + self.width*0.5, self.y + self.height*0.8)]
        )

    def offscreen(self):
        return self.x + self.width < -10

def spawn_obstacle(speed):
    kind = random.choices(["archer", "tower", "rock"], weights=[0.35, 0.30, 0.35], k=1)[0]
    if kind == "archer":
        return Archer(speed)
    elif kind == "tower":
        return Tower(speed)
    else:
        return Rock(speed)

# ---------- Ground / Parallax ----------
class Ground:
    def __init__(self):
        self.segs = []
        self.reset()

    def reset(self):
        self.segs = []
        x = 0
        while x < WIDTH + 120:
            w = random.randint(30, 70)
            h = random.randint(2, 6)
            self.segs.append([x, GROUND_Y + random.randint(0, 2), w, h])
            x += w + random.randint(8, 24)

    def update(self, speed):
        for s in self.segs:
            s[0] -= speed * 0.9
        while self.segs and self.segs[0][0] + self.segs[0][2] < -20:
            self.segs.pop(0)
        last_x = self.segs[-1][0] + self.segs[-1][2] if self.segs else 0
        while last_x < WIDTH + 100:
            w = random.randint(30, 70)
            h = random.randint(2, 6)
            self.segs.append([last_x + random.randint(8, 24), GROUND_Y + random.randint(0, 2), w, h])
            last_x = self.segs[-1][0] + self.segs[-1][2]

    def draw(self, surf, is_night):
        col = COLORS["ui_dark"] if is_night else COLORS["ground"]
        for s in self.segs:
            pygame.draw.rect(surf, col, pygame.Rect(s))

class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(40, 130)
        self.speed = random.uniform(0.25, 0.6)

    def update(self):
        self.x -= self.speed
        if self.x < -40:
            self.x = WIDTH + random.randint(0, 160)
            self.y = random.randint(40, 130)
            self.speed = random.uniform(0.25, 0.6)

    def draw(self, surf):
        DIM = (200, 205, 210)
        pygame.draw.circle(surf, DIM, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surf, DIM, (int(self.x) + 14, int(self.y) + 4), 10)
        pygame.draw.circle(surf, DIM, (int(self.x) - 12, int(self.y) + 6), 8)

class Stars:
    def __init__(self):
        self.points = [(random.randint(0, WIDTH), random.randint(30, 170)) for _ in range(STAR_COUNT)]

    def twinkle(self):
        for i in range(0, STAR_COUNT, 7):
            x, y = self.points[i]
            self.points[i] = (x + random.randint(-1, 1), y + random.randint(-1, 1))

    def draw(self, surf):
        for (x, y) in self.points:
            pygame.draw.circle(surf, COLORS["star"], (x, y), 1)

# ---------- Sky ----------
def draw_day_sky(surf, t_ratio):
    surf.fill(COLORS["day_bg"])
    cx = int(lerp(60, WIDTH - 60, t_ratio))
    cy = int(lerp(160, 60, math.sin(t_ratio * math.pi)))
    pygame.draw.circle(surf, COLORS["sun"], (cx, max(40, cy)), 16)

def draw_night_sky(surf, stars, t_ratio):
    surf.fill(COLORS["night_bg"])
    stars.twinkle()
    stars.draw(surf)
    cx = int(lerp(WIDTH - 60, 60, t_ratio))
    cy = int(lerp(70, 160, math.sin(t_ratio * math.pi)))
    pygame.draw.circle(surf, COLORS["moon"], (cx, max(40, cy)), 14)
    pygame.draw.circle(surf, COLORS["night_bg"], (cx - 4, max(36, cy)), 12)

# ---------- Game ----------
def main():
    ninja = Ninja()
    ground = Ground()
    clouds = [Cloud() for _ in range(3)]
    obstacles = []
    stars = Stars()

    score = 0
    high_score = 0
    speed = INIT_SPEED
    spawn_timer = 0
    game_over = False

    cycle_timer = 0  # switches day/night every DAY_LENGTH_MS
    is_day = True

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and game_over:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                    ninja.reset()
                    obstacles.clear()
                    score = 0
                    speed = INIT_SPEED
                    spawn_timer = 0
                    game_over = False

        keys = pygame.key.get_pressed()
        if not game_over:
            ninja.handle_input(keys)
            ninja.update(dt)
            ground.update(speed)

            for c in clouds:
                c.update()

            spawn_timer -= dt
            if spawn_timer <= 0:
                obstacles.append(spawn_obstacle(speed))
                spawn_timer = random.randint(800, 1400) - int(speed * 20)

            for ob in obstacles:
                ob.update(speed)
            obstacles = [ob for ob in obstacles if not ob.offscreen()]

            for ob in obstacles:
                if ninja.rect.colliderect(ob.rect):
                    game_over = True
                    high_score = max(high_score, score)
                    break

            score += 1
            if score % SPEED_INCREASE_EVERY == 0 and speed < MAX_SPEED:
                speed += 0.5

            cycle_timer += dt
            if cycle_timer >= DAY_LENGTH_MS:
                is_day = not is_day
                cycle_timer = 0

        # ---------- Draw ----------
        t_ratio = cycle_timer / DAY_LENGTH_MS
        if is_day:
            draw_day_sky(screen, t_ratio)
            for c in clouds: c.draw(screen)
        else:
            draw_night_sky(screen, stars, t_ratio)

        ground.draw(screen, is_day)

        ninja.draw(screen, not is_day)
        for ob in obstacles:
            ob.draw(screen, not is_day)

        ui_col = COLORS["ui_dark"] if is_day else COLORS["ui_dark"]
        score_surf = font_small.render(f"Score: {score:05d}", True, ui_col)
        hs_surf = font_small.render(f"HI: {high_score:05d}", True, ui_col)
        hint = font_small.render("Space/Up: Jump   Down: Duck   Enter: Restart", True, ui_col)

        screen.blit(score_surf, (WIDTH - 160, 12))
        screen.blit(hs_surf, (WIDTH - 160, 32))
        screen.blit(hint, (12, 12))

        if game_over:
            over = font_big.render("GAME OVER", True, ui_col)
            prompt = font_small.render("Press Space/Up/Enter to restart", True, ui_col)
            screen.blit(over, (WIDTH//2 - over.get_width()//2, 110))
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 148))

        pygame.display.flip()

if __name__ == "__main__":
    main()
