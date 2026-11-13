"""
Angry Birds Clone - built with Python + Pygame
Controls:
    Mouse drag  : pull the bird back, release to launch
    R           : restart current level
    N           : next level (after winning)
    ESC         : quit
"""
import math
import sys
import pygame

pygame.init()

# ---------- Settings ----------
WIDTH, HEIGHT = 1000, 600
GROUND = 540
FPS = 60
GRAVITY = 0.45
SLING = pygame.Vector2(180, 420)
MAX_PULL = 90
POWER = 0.19
BIRD_RADIUS = 16
PIG_RADIUS = 18

SKY = (135, 206, 235)
GRASS = (76, 153, 0)
BROWN = (139, 90, 43)
WOOD = (205, 150, 90)
RED = (220, 40, 40)
GREEN = (90, 200, 70)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Angry Birds - Python Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 26, bold=True)
big_font = pygame.font.SysFont("arial", 64, bold=True)

# ---------- Levels: (blocks as Rect tuples, pig positions) ----------
LEVELS = [
    {
        "blocks": [(700, 480, 20, 60), (780, 480, 20, 60), (690, 460, 120, 20)],
        "pigs": [(745, 510)],
    },
    {
        "blocks": [(650, 480, 20, 60), (760, 480, 20, 60), (640, 460, 150, 20),
                   (680, 400, 20, 60), (740, 400, 20, 60), (670, 380, 100, 20)],
        "pigs": [(715, 510), (715, 430)],
    },
    {
        "blocks": [(600, 480, 20, 60), (700, 480, 20, 60), (800, 480, 20, 60),
                   (590, 460, 140, 20), (690, 460, 140, 20),
                   (640, 400, 20, 60), (760, 400, 20, 60), (630, 380, 150, 20)],
        "pigs": [(660, 510), (760, 510), (710, 350)],
    },
]


class Bird:
    def __init__(self):
        self.pos = pygame.Vector2(SLING)
        self.vel = pygame.Vector2(0, 0)
        self.state = "ready"  # ready, dragging, flying, done
        self.timer = 0

    def update(self):
        if self.state != "flying":
            return
        self.timer += 1
        self.vel.y += GRAVITY
        self.pos += self.vel
        # Ground bounce
        if self.pos.y + BIRD_RADIUS >= GROUND:
            self.pos.y = GROUND - BIRD_RADIUS
            self.vel.y *= -0.35
            self.vel.x *= 0.8
        # Finished when slow, off-screen, or too long
        slow = self.vel.length() < 0.8 and self.pos.y + BIRD_RADIUS >= GROUND - 1
        if slow or self.pos.x > WIDTH + 50 or self.pos.x < -50 or self.timer > 480:
            self.state = "done"

    def draw(self):
        pygame.draw.circle(screen, RED, self.pos, BIRD_RADIUS)
        eye = (int(self.pos.x + 6), int(self.pos.y - 4))
        pygame.draw.circle(screen, WHITE, eye, 5)
        pygame.draw.circle(screen, BLACK, eye, 2)
        pygame.draw.polygon(screen, (255, 180, 0), [
            (self.pos.x + 12, self.pos.y), (self.pos.x + 22, self.pos.y + 3),
            (self.pos.x + 12, self.pos.y + 7)])


class Game:
    def __init__(self, level=0):
        self.level = level
        self.score = 0
        self.load_level()

    def load_level(self):
        data = LEVELS[self.level]
        self.blocks = [pygame.Rect(*b) for b in data["blocks"]]
        self.pigs = [pygame.Vector2(p) for p in data["pigs"]]
        self.birds_left = 3
        self.bird = Bird()
        self.status = "playing"  # playing, won, lost

    # ----- collision helpers -----
    def hit_rect(self, rect):
        cx = max(rect.left, min(self.bird.pos.x, rect.right))
        cy = max(rect.top, min(self.bird.pos.y, rect.bottom))
        return (self.bird.pos - pygame.Vector2(cx, cy)).length() < BIRD_RADIUS

    def check_collisions(self):
        b = self.bird
        if b.state != "flying":
            return
        speed = b.vel.length()
        for rect in self.blocks[:]:
            if self.hit_rect(rect):
                if speed > 7:  # strong hit destroys block
                    self.blocks.remove(rect)
                    self.score += 100
                    b.vel *= 0.7
                else:
                    b.vel.x *= -0.4
                    b.vel.y *= -0.4
                    b.pos += b.vel
        for pig in self.pigs[:]:
            if b.pos.distance_to(pig) < BIRD_RADIUS + PIG_RADIUS and speed > 2.5:
                self.pigs.remove(pig)
                self.score += 500
                b.vel *= 0.6

    # ----- game flow -----
    def handle_event(self, e):
        b = self.bird
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        if self.status != "playing":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and b.state == "ready":
            if mouse.distance_to(b.pos) < 40:
                b.state = "dragging"
        elif e.type == pygame.MOUSEBUTTONUP and b.state == "dragging":
            b.vel = (SLING - b.pos) * POWER * 4
            b.state = "flying"
            self.birds_left -= 1

    def update(self):
        b = self.bird
        if b.state == "dragging":
            mouse = pygame.Vector2(pygame.mouse.get_pos())
            offset = mouse - SLING
            if offset.length() > MAX_PULL:
                offset.scale_to_length(MAX_PULL)
            b.pos = SLING + offset
        b.update()
        self.check_collisions()

        if not self.pigs:
            self.status = "won"
        elif b.state == "done":
            if self.birds_left > 0:
                self.bird = Bird()
            else:
                self.status = "lost"

    # ----- drawing -----
    def draw_trajectory(self):
        b = self.bird
        pos = pygame.Vector2(b.pos)
        vel = (SLING - b.pos) * POWER * 4
        for i in range(30):
            vel.y += GRAVITY
            pos += vel
            if i % 2 == 0:
                pygame.draw.circle(screen, WHITE, pos, 3)

    def draw(self):
        screen.fill(SKY)
        pygame.draw.rect(screen, GRASS, (0, GROUND, WIDTH, HEIGHT - GROUND))

        # Slingshot
        pygame.draw.rect(screen, BROWN, (SLING.x - 6, SLING.y, 12, GROUND - SLING.y))
        pygame.draw.line(screen, BROWN, (SLING.x - 6, SLING.y), (SLING.x - 18, SLING.y - 25), 8)
        pygame.draw.line(screen, BROWN, (SLING.x + 6, SLING.y), (SLING.x + 18, SLING.y - 25), 8)

        for rect in self.blocks:
            pygame.draw.rect(screen, WOOD, rect)
            pygame.draw.rect(screen, BROWN, rect, 2)
        for pig in self.pigs:
            pygame.draw.circle(screen, GREEN, pig, PIG_RADIUS)
            pygame.draw.circle(screen, WHITE, (pig.x - 6, pig.y - 4), 5)
            pygame.draw.circle(screen, WHITE, (pig.x + 6, pig.y - 4), 5)
            pygame.draw.circle(screen, BLACK, (pig.x - 6, pig.y - 4), 2)
            pygame.draw.circle(screen, BLACK, (pig.x + 6, pig.y - 4), 2)

        if self.bird.state == "dragging":
            pygame.draw.line(screen, BLACK, (SLING.x - 18, SLING.y - 25), self.bird.pos, 4)
            pygame.draw.line(screen, BLACK, (SLING.x + 18, SLING.y - 25), self.bird.pos, 4)
            self.draw_trajectory()
        self.bird.draw()

        # HUD
        hud = f"Score: {self.score}   Birds: {self.birds_left}   Level: {self.level + 1}"
        screen.blit(font.render(hud, True, BLACK), (20, 15))

        if self.status == "won":
            self.banner("YOU WIN!", "Press N for next level")
        elif self.status == "lost":
            self.banner("GAME OVER", "Press R to retry")

    def banner(self, title, sub):
        t = big_font.render(title, True, BLACK)
        s = font.render(sub, True, BLACK)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 220)))
        screen.blit(s, s.get_rect(center=(WIDTH // 2, 280)))


def main():
    game = Game()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    game.load_level()
                elif e.key == pygame.K_n and game.status == "won":
                    game.level = (game.level + 1) % len(LEVELS)
                    game.load_level()
            game.handle_event(e)
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()