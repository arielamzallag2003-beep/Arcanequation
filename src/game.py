import math
import random
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pygame

WIDTH, HEIGHT = 1080, 720
FPS = 60

BG = (15, 10, 35)
WHITE = (242, 234, 255)
ACCENT = (137, 96, 255)
ERROR = (255, 95, 140)
SUCCESS = (110, 240, 170)


@dataclass
class EquationChallenge:
    expression: str
    answer: int


class ArcaneEquationGame:
    """An arcade spell-casting game using equation solving and ZQSD controls."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Arcane Equation")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.ui_font = pygame.font.SysFont("consolas", 28)
        self.small_font = pygame.font.SysFont("consolas", 20)

        self.running = True
        self.asset_dir = Path(__file__).resolve().parents[1] / "assets"
        self._ensure_assets()
        self.floor_tex = self._load_sprite("arcane_floor.bmp", (320, 180))
        self.player_sprite = self._load_sprite("mage.bmp", (64, 64))
        self.enemy_sprite = self._load_sprite("void_lord.bmp", (80, 80))
        self.player_pos = pygame.Vector2(WIDTH * 0.15, HEIGHT * 0.55)
        self.enemy_pos = pygame.Vector2(WIDTH * 0.8, HEIGHT * 0.4)
        self.projectiles: list[dict] = []
        self.stars = [
            pygame.Vector2(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            for _ in range(120)
        ]

        self.player_hp = 8
        self.enemy_hp = 10
        self.score = 0
        self.enemy_cast_cooldown = 2.4
        self.enemy_cast_timer = self.enemy_cast_cooldown

        self.input_buffer = ""
        self.challenge = self._new_challenge()
        self.message = "Résous l'équation pour lancer un sort !"
        self.message_color = WHITE


    def _ensure_assets(self) -> None:
        required = ["arcane_floor.bmp", "mage.bmp", "void_lord.bmp"]
        if all((self.asset_dir / name).exists() for name in required):
            return
        generator = Path(__file__).resolve().parents[1] / "scripts" / "generate_assets.py"
        if generator.exists():
            subprocess.run([sys.executable, generator.as_posix()], check=False)

    def _load_sprite(self, file_name: str, size: tuple[int, int]) -> pygame.Surface | None:
        path = self.asset_dir / file_name
        if not path.exists():
            return None
        image = pygame.image.load(path.as_posix()).convert()
        return pygame.transform.smoothscale(image, size)

    def _new_challenge(self) -> EquationChallenge:
        a = random.randint(2, 11)
        b = random.randint(2, 11)
        c = random.randint(1, 30)
        choice = random.choice(["+", "-", "*"])
        if choice == "+":
            exp = f"{a}x + {b} = {a * c + b}"
        elif choice == "-":
            exp = f"{a}x - {b} = {a * c - b}"
        else:
            exp = f"{a}x = {a * c}"
        return EquationChallenge(expression=exp, answer=c)

    def _shoot(self, friendly: bool) -> None:
        if friendly:
            start = self.player_pos + pygame.Vector2(48, -8)
            velocity = pygame.Vector2(9, 0)
            color = SUCCESS
        else:
            start = self.enemy_pos + pygame.Vector2(-20, 10)
            velocity = pygame.Vector2(-6.5, 0)
            color = ERROR
        self.projectiles.append({"pos": start, "vel": velocity, "color": color, "friendly": friendly})

    def _handle_answer(self) -> None:
        if not self.input_buffer:
            return
        try:
            answer = int(self.input_buffer)
        except ValueError:
            self.message = "Entrée invalide. Utilise des chiffres."
            self.message_color = ERROR
            self.input_buffer = ""
            return

        if answer == self.challenge.answer:
            self.score += 100
            self._shoot(friendly=True)
            self.message = "Sort réussi ✨"
            self.message_color = SUCCESS
        else:
            self.player_hp -= 1
            self._shoot(friendly=False)
            self.message = f"Mauvaise réponse (x={self.challenge.answer})"
            self.message_color = ERROR

        self.challenge = self._new_challenge()
        self.input_buffer = ""

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        speed = 4.2
        # French AZERTY-friendly movement: ZQSD
        if keys[pygame.K_z]:
            self.player_pos.y -= speed
        if keys[pygame.K_s]:
            self.player_pos.y += speed
        if keys[pygame.K_q]:
            self.player_pos.x -= speed
        if keys[pygame.K_d]:
            self.player_pos.x += speed

        self.player_pos.x = max(48, min(WIDTH - 48, self.player_pos.x))
        self.player_pos.y = max(100, min(HEIGHT - 60, self.player_pos.y))

        for star in self.stars:
            star.x -= 18 * dt
            if star.x < 0:
                star.x = WIDTH
                star.y = random.randint(0, HEIGHT)

        self.enemy_cast_timer -= dt
        if self.enemy_cast_timer <= 0:
            self._shoot(friendly=False)
            self.enemy_cast_timer = self.enemy_cast_cooldown + random.uniform(-0.7, 0.5)

        for shot in self.projectiles:
            shot["pos"] += shot["vel"]

        alive = []
        for shot in self.projectiles:
            x, y = shot["pos"]
            if not (0 <= x <= WIDTH and 0 <= y <= HEIGHT):
                continue

            if shot["friendly"]:
                if self.enemy_pos.distance_to(shot["pos"]) < 42:
                    self.enemy_hp -= 1
                    self.score += 50
                    continue
            else:
                if self.player_pos.distance_to(shot["pos"]) < 34:
                    self.player_hp -= 1
                    self.message = "Le Néant te frappe !"
                    self.message_color = ERROR
                    continue
            alive.append(shot)

        self.projectiles = alive

    def _draw_arcane_grid(self) -> None:
        for i in range(24):
            alpha = 20 + int(10 * math.sin(i + pygame.time.get_ticks() * 0.002))
            color = (45, 25, 90, alpha)
            surface = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
            surface.fill(color)
            self.screen.blit(surface, (0, 110 + i * 24))

    def _draw(self) -> None:
        self.screen.fill(BG)
        for idx, star in enumerate(self.stars):
            twinkle = 120 + (idx * 13 + pygame.time.get_ticks() // 10) % 135
            pygame.draw.circle(self.screen, (twinkle, twinkle, 255), star, 1)
        if self.floor_tex:
            for y in range(110, HEIGHT, self.floor_tex.get_height()):
                for x in range(0, WIDTH, self.floor_tex.get_width()):
                    self.screen.blit(self.floor_tex, (x, y))
        self._draw_arcane_grid()

        title = self.title_font.render("ARCANE EQUATION", True, ACCENT)
        self.screen.blit(title, (35, 20))

        challenge = self.ui_font.render(f"Énigme: {self.challenge.expression}", True, WHITE)
        self.screen.blit(challenge, (40, 90))

        answer = self.ui_font.render(f"Ta réponse (Entrée): {self.input_buffer or '_'}", True, WHITE)
        self.screen.blit(answer, (40, 126))

        msg = self.small_font.render(self.message, True, self.message_color)
        self.screen.blit(msg, (40, 165))

        hud = self.ui_font.render(f"Vie: {self.player_hp}   Boss: {self.enemy_hp}   Score: {self.score}", True, WHITE)
        self.screen.blit(hud, (40, HEIGHT - 45))

        if self.player_sprite:
            self.screen.blit(self.player_sprite, self.player_sprite.get_rect(center=self.player_pos))
        else:
            pygame.draw.circle(self.screen, (120, 160, 255), self.player_pos, 28)

        if self.enemy_sprite:
            self.screen.blit(self.enemy_sprite, self.enemy_sprite.get_rect(center=self.enemy_pos))
        else:
            pygame.draw.circle(self.screen, (255, 80, 180), self.enemy_pos, 36)

        for shot in self.projectiles:
            pygame.draw.circle(self.screen, shot["color"], shot["pos"], 8)

        hint = self.small_font.render("Déplacement: ZQSD | Entrée: valider | Retour arrière: corriger", True, (200, 185, 240))
        self.screen.blit(hint, (40, HEIGHT - 18))

        if self.player_hp <= 0 or self.enemy_hp <= 0:
            win = self.enemy_hp <= 0
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 2, 15, 180))
            self.screen.blit(overlay, (0, 0))
            end_msg = "Victoire mystique !" if win else "Tu as été dissipé..."
            end_color = SUCCESS if win else ERROR
            text = self.title_font.render(end_msg, True, end_color)
            sub = self.ui_font.render("R: recommencer | Échap: quitter", True, WHITE)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.flip()

    def _reset(self) -> None:
        self.player_hp = 8
        self.enemy_hp = 10
        self.score = 0
        self.projectiles.clear()
        self.challenge = self._new_challenge()
        self.input_buffer = ""
        self.message = "Nouvelle partie !"
        self.message_color = WHITE

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN and self.player_hp > 0 and self.enemy_hp > 0:
                        self._handle_answer()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_buffer = self.input_buffer[:-1]
                    elif event.key == pygame.K_r and (self.player_hp <= 0 or self.enemy_hp <= 0):
                        self._reset()
                    elif event.unicode.isdigit() and len(self.input_buffer) < 3:
                        self.input_buffer += event.unicode

            if self.player_hp > 0 and self.enemy_hp > 0:
                self._update(1 / FPS)
            self._draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit(0)


def main() -> None:
    ArcaneEquationGame().run()


if __name__ == "__main__":
    main()
