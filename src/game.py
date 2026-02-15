from __future__ import annotations

import math
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pygame

WIDTH, HEIGHT = 1280, 760
FPS = 60

BG = (10, 10, 22)
TEXT = (240, 230, 255)
UI_PANEL = (22, 18, 46)
ACCENT = (168, 120, 255)
GOOD = (100, 255, 180)
BAD = (255, 110, 140)


@dataclass
class SpellDef:
    name: str
    school: str
    coeff_key: str
    color: tuple[int, int, int]
    mana_cost: float
    cooldown: float
    speed: float
    size: int
    base_damage: float
    equation: str


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    radius: int
    color: tuple[int, int, int]
    damage: float
    owner: str
    life: float = 3.0
    pulse: float = 0.0


@dataclass
class Mage:
    pos: pygame.Vector2
    hp: float
    hp_max: float
    mana: float
    mana_max: float
    focus: float
    velocity: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    shield: float = 0.0
    burn: float = 0.0
    slow: float = 0.0


SPELLS: list[SpellDef] = [
    SpellDef("Lance Linéaire", "Linear", "a", (110, 220, 255), 18, 0.4, 540, 10, 16, "E = a·x + b"),
    SpellDef("Orbe Quadratique", "Quadratic", "q", (230, 120, 255), 28, 1.0, 420, 14, 34, "E = ax² + bx + c"),
    SpellDef("Onde Sinusoïdale", "sine", "s", (130, 255, 180), 22, 0.7, 470, 11, 22, "E = A·sin(ωx+φ)"),
]


class ArcaneEquationGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Arcane Equation — Sorcellerie Symbolique")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.asset_dir = Path(__file__).resolve().parents[1] / "assets"
        self._ensure_assets()

        self.title_font = pygame.font.SysFont("consolas", 38, bold=True)
        self.ui_font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)

        self.player = Mage(pygame.Vector2(220, HEIGHT * 0.5), 180, 180, 120, 120, 0.0)
        self.enemy = Mage(pygame.Vector2(WIDTH - 220, HEIGHT * 0.5), 260, 260, 200, 200, 0.0)

        self.projectiles: list[Projectile] = []
        self.rings: list[tuple[pygame.Vector2, float, tuple[int, int, int]]] = []
        self.particles: list[tuple[pygame.Vector2, pygame.Vector2, float, tuple[int, int, int]]] = []
        self.shake = 0.0
        self.stars = [pygame.Vector2(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(240)]

        self.enemy_phase = "pressure"
        self.enemy_intent = "Opening stance"
        self.combo = 0
        self.enemy_cast_timer = 0.9
        self.enemy_dash_timer = 2.4
        self.enemy_think = 0.0

        self.channel_a = 2.0
        self.channel_b = 1.0
        self.channel_c = 0.0
        self.channel_omega = 1.0
        self.channel_phi = 0.0

        self.selected_spell = 0
        self.cooldowns = {spell.name: 0.0 for spell in SPELLS}
        self.message = "Canalise les paramètres d'équation (1-9), puis lance un sort (F/G/H)."
        self.last_player_spell = "None"

        self.running = True
        self.winner: str | None = None

    def _ensure_assets(self) -> None:
        generator = Path(__file__).resolve().parents[1] / "scripts" / "generate_assets.py"
        required = ["mage.bmp", "archmage.bmp", "arcane_floor.bmp"]
        if all((self.asset_dir / f).exists() for f in required):
            return
        if generator.exists():
            subprocess.run([sys.executable, generator.as_posix()], check=False)

    def _spell_power(self, spell: SpellDef) -> float:
        if spell.school == "Linear":
            return max(0.4, min(2.5, abs(self.channel_a) * 0.25 + abs(self.channel_b) * 0.16))
        if spell.school == "Quadratic":
            return max(0.5, min(2.8, abs(self.channel_a) * 0.2 + abs(self.channel_b) * 0.12 + abs(self.channel_c) * 0.07))
        return max(0.5, min(2.4, abs(self.channel_a) * 0.19 + abs(self.channel_omega) * 0.32 + abs(math.sin(self.channel_phi))))

    def _cast(self, caster: Mage, target: Mage, spell: SpellDef, owner: str) -> bool:
        if owner == "player":
            if caster.mana < spell.mana_cost or self.cooldowns[spell.name] > 0:
                self.message = "Sort indisponible (mana/cooldown)."
                return False
            self.cooldowns[spell.name] = spell.cooldown

        power = self._spell_power(spell)
        caster.mana = max(0, caster.mana - spell.mana_cost * (0.7 if owner == "enemy" else 1.0))
        direction = (target.pos - caster.pos).normalize()
        speed = spell.speed * (0.85 + power * 0.22)

        if owner == "player":
            self.last_player_spell = spell.name

        if spell.school == "sine":
            perp = pygame.Vector2(-direction.y, direction.x)
            for k in (-1, 0, 1):
                vel = direction * speed + perp * (k * 120)
                self.projectiles.append(Projectile(caster.pos.copy(), vel / FPS, spell.size, spell.color, spell.base_damage * power * 0.7, owner, 3.0, random.random() * 6.28))
        elif spell.school == "Quadratic":
            spread = random.uniform(-0.2, 0.2)
            vel = direction.rotate_rad(spread) * speed
            self.projectiles.append(Projectile(caster.pos.copy(), vel / FPS, spell.size + int(power * 2), spell.color, spell.base_damage * power, owner, 3.6))
            self.rings.append((caster.pos.copy(), 16, spell.color))
        else:
            vel = direction * speed
            self.projectiles.append(Projectile(caster.pos.copy(), vel / FPS, spell.size, spell.color, spell.base_damage * power, owner, 2.9))

        return True

    def _enemy_ai(self, dt: float) -> None:
        hp_ratio = self.enemy.hp / self.enemy.hp_max
        if hp_ratio < 0.35:
            self.enemy_phase = "desperate"
        elif self.enemy.mana < 45:
            self.enemy_phase = "recover"
        else:
            self.enemy_phase = "pressure"
        self.enemy_intent = "Opening stance"
        self.combo = 0

        self.enemy_think -= dt
        to_player = self.player.pos - self.enemy.pos
        dist = to_player.length()

        if self.enemy_think <= 0:
            self.enemy_think = random.uniform(0.22, 0.42)
            desired = 430 if self.enemy_phase == "pressure" else 520
            if dist < desired - 40:
                self.enemy.velocity = (-to_player.normalize()) * random.uniform(120, 180)
                self.enemy_intent = "Repositionnement défensif"
            elif dist > desired + 70:
                self.enemy.velocity = to_player.normalize() * random.uniform(90, 140)
                self.enemy_intent = "Approche agressive"
            else:
                self.enemy.velocity = pygame.Vector2(0, random.choice([-1, 1]) * random.uniform(110, 170))
                self.enemy_intent = "Strafe latéral"

        dodge = any(p.owner == "player" and p.pos.distance_to(self.enemy.pos) < 120 for p in self.projectiles)
        self.enemy_dash_timer -= dt
        if dodge and self.enemy_dash_timer <= 0:
            self.enemy_dash_timer = random.uniform(1.4, 2.2)
            self.enemy.pos.y += random.choice([-140, 140])

        self.enemy_cast_timer -= dt
        if self.enemy_cast_timer <= 0 and self.enemy.mana > 12:
            if self.enemy_phase == "desperate":
                spell = SPELLS[2] if random.random() < 0.7 else SPELLS[1]
                self.enemy_cast_timer = random.uniform(0.35, 0.75)
                self.enemy_intent = "Rafale sinusoïdale"
            elif self.enemy_phase == "recover":
                spell = SPELLS[0]
                self.enemy_cast_timer = random.uniform(0.9, 1.2)
                self.enemy.mana = min(self.enemy.mana_max, self.enemy.mana + 8)
                self.enemy_intent = "Récupération de mana"
            else:
                spell = random.choice([SPELLS[0], SPELLS[1]])
                self.enemy_cast_timer = random.uniform(0.55, 0.95)
                self.enemy_intent = "Pression balistique"
            self._cast(self.enemy, self.player, spell, "enemy")

        self.enemy.pos += self.enemy.velocity * dt
        self.enemy.pos.x = max(WIDTH * 0.55, min(WIDTH - 120, self.enemy.pos.x))
        self.enemy.pos.y = max(130, min(HEIGHT - 110, self.enemy.pos.y))

    def _handle_player_keys(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_z]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_q]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1
        if move.length_squared() > 0:
            speed_mult = 1.0 - min(0.6, self.player.slow * 0.2)
            self.player.pos += move.normalize() * 260 * speed_mult * dt

        self.player.pos.x = max(90, min(WIDTH * 0.45, self.player.pos.x))
        self.player.pos.y = max(120, min(HEIGHT - 100, self.player.pos.y))

    def _tick_projectiles(self, dt: float) -> None:
        alive: list[Projectile] = []
        for p in self.projectiles:
            p.pos += p.vel
            p.life -= dt
            p.pulse += dt * 8
            if p.life <= 0:
                continue
            if p.pos.x < -30 or p.pos.x > WIDTH + 30 or p.pos.y < -30 or p.pos.y > HEIGHT + 30:
                continue
            if p.owner == "player" and p.pos.distance_to(self.enemy.pos) < 36 + p.radius:
                dmg = max(0.0, p.damage - self.enemy.shield)
                self.enemy.shield = max(0.0, self.enemy.shield - p.damage * 0.35)
                self.enemy.hp -= dmg
                self.enemy.burn = min(4.0, self.enemy.burn + 0.7)
                self.combo += 1
                self.rings.append((p.pos.copy(), p.radius * 1.2, p.color))
                self.shake = min(9.0, self.shake + 2.4)
                for _ in range(8):
                    self.particles.append((p.pos.copy(), pygame.Vector2(random.uniform(-90,90), random.uniform(-90,90)), random.uniform(0.2,0.6), p.color))
                continue
            if p.owner == "enemy" and p.pos.distance_to(self.player.pos) < 32 + p.radius:
                dmg = max(0.0, p.damage - self.player.shield)
                self.player.shield = max(0.0, self.player.shield - p.damage * 0.3)
                self.player.hp -= dmg
                self.player.slow = min(2.0, self.player.slow + 0.35)
                self.combo = 0
                self.rings.append((p.pos.copy(), p.radius * 1.2, BAD))
                self.shake = min(12.0, self.shake + 3.0)
                for _ in range(10):
                    self.particles.append((p.pos.copy(), pygame.Vector2(random.uniform(-120,120), random.uniform(-120,120)), random.uniform(0.25,0.7), BAD))
                continue
            alive.append(p)
        self.projectiles = alive

    def _update_equation_channels(self, key: int) -> None:
        if key == pygame.K_1:
            self.channel_a += 0.5
        elif key == pygame.K_2:
            self.channel_a -= 0.5
        elif key == pygame.K_3:
            self.channel_b += 0.5
        elif key == pygame.K_4:
            self.channel_b -= 0.5
        elif key == pygame.K_5:
            self.channel_c += 1.0
        elif key == pygame.K_6:
            self.channel_c -= 1.0
        elif key == pygame.K_7:
            self.channel_omega += 0.2
        elif key == pygame.K_8:
            self.channel_omega = max(0.2, self.channel_omega - 0.2)
        elif key == pygame.K_9:
            self.channel_phi += 0.4

        self.channel_a = max(-10, min(10, self.channel_a))
        self.channel_b = max(-10, min(10, self.channel_b))
        self.channel_c = max(-25, min(25, self.channel_c))
        self.channel_phi = ((self.channel_phi + math.pi) % (2 * math.pi)) - math.pi

    def _draw_bar(self, x: int, y: int, w: int, h: int, ratio: float, fg: tuple[int, int, int], bg: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.screen, bg, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, fg, (x, y, int(w * max(0.0, min(1.0, ratio))), h), border_radius=8)

    def _draw(self) -> None:
        self.shake = max(0.0, self.shake - 0.5)
        cam = pygame.Vector2(random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))
        self.screen.fill(BG)
        for i, star in enumerate(self.stars):
            tw = 120 + (i * 17 + pygame.time.get_ticks() // 8) % 120
            pygame.draw.circle(self.screen, (tw, tw, 255), star + cam * 0.3, 1)

        for y in range(130, HEIGHT, 30):
            alpha = 20 + int(12 * math.sin(y * 0.04 + pygame.time.get_ticks() * 0.002))
            layer = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
            layer.fill((140, 90, 255, alpha))
            self.screen.blit(layer, (cam.x * 0.2, y + cam.y * 0.2))

        for pos, r, color in self.rings[:]:
            pygame.draw.circle(self.screen, color, pos + cam, int(r), width=2)
        self.rings[:] = [(pos, r + 2.5, c) for pos, r, c in self.rings if r < 120]

        for p in self.projectiles:
            wobble = int(2 * math.sin(p.pulse))
            glow = pygame.Surface((p.radius*6, p.radius*6), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*p.color, 70), (p.radius*3, p.radius*3), p.radius*2)
            self.screen.blit(glow, p.pos + cam - pygame.Vector2(p.radius*3, p.radius*3), special_flags=pygame.BLEND_PREMULTIPLIED)
            pygame.draw.circle(self.screen, p.color, p.pos + cam, max(2, p.radius + wobble))

        pygame.draw.circle(self.screen, (120, 180, 255), self.player.pos + cam, 30)
        pygame.draw.circle(self.screen, (255, 90, 190), self.enemy.pos + cam, 36)

        panel = pygame.Surface((WIDTH, 118), pygame.SRCALPHA)
        panel.fill((*UI_PANEL, 215))
        self.screen.blit(panel, (0, 0))

        self.screen.blit(self.title_font.render("ARCANE EQUATION: BATTLE OF FORMS", True, ACCENT), (20, 10))

        self._draw_bar(24, 56, 320, 16, self.player.hp / self.player.hp_max, GOOD, (50, 20, 30))
        self._draw_bar(24, 78, 320, 14, self.player.mana / self.player.mana_max, (90, 180, 255), (20, 32, 64))
        self.screen.blit(self.small_font.render(f"Mage HP {self.player.hp:.0f}/{self.player.hp_max:.0f} | Mana {self.player.mana:.0f}", True, TEXT), (28, 94))

        self._draw_bar(WIDTH - 344, 56, 320, 16, self.enemy.hp / self.enemy.hp_max, BAD, (50, 20, 30))
        self._draw_bar(WIDTH - 344, 78, 320, 14, self.enemy.mana / self.enemy.mana_max, (255, 160, 100), (62, 34, 20))
        self.screen.blit(self.small_font.render(f"Archonte HP {self.enemy.hp:.0f}/{self.enemy.hp_max:.0f} | Phase: {self.enemy_phase}", True, TEXT), (WIDTH - 338, 94))
        self.screen.blit(self.small_font.render(f"Intent: {self.enemy_intent}", True, (255, 205, 205)), (WIDTH - 338, 114))

        eq = f"Canaux: a={self.channel_a:.1f}  b={self.channel_b:.1f}  c={self.channel_c:.1f}  ω={self.channel_omega:.1f}  φ={self.channel_phi:.2f}"
        self.screen.blit(self.ui_font.render(eq, True, TEXT), (350, 58))
        self.screen.blit(self.small_font.render("1/2:a± 3/4:b± 5/6:c± 7/8:ω± 9:φ+ | F/G/H: sorts", True, (210, 210, 255)), (350, 86))

        spell_x = 16
        for i, spell in enumerate(SPELLS):
            cd = self.cooldowns[spell.name]
            strength = self._spell_power(spell)
            y = HEIGHT - 96
            box = pygame.Rect(spell_x, y, 300, 80)
            pygame.draw.rect(self.screen, (35, 24, 70), box, border_radius=10)
            if i == self.selected_spell:
                pygame.draw.rect(self.screen, spell.color, box, width=2, border_radius=10)
            self.screen.blit(self.small_font.render(f"{['F','G','H'][i]} — {spell.name}", True, TEXT), (spell_x + 10, y + 8))
            self.screen.blit(self.small_font.render(spell.equation, True, (200, 200, 240)), (spell_x + 10, y + 28))
            self.screen.blit(self.small_font.render(f"Puissance {strength:.2f} | Mana {spell.mana_cost:.0f} | CD {max(0,cd):.2f}s", True, spell.color), (spell_x + 10, y + 50))
            spell_x += 314

        self.screen.blit(self.small_font.render(f"Combo: x{self.combo} | Dernier sort: {self.last_player_spell}", True, (190, 255, 220)), (980, HEIGHT - 50))
        self.screen.blit(self.small_font.render(self.message, True, (236, 230, 255)), (980, HEIGHT - 28))


        alive_particles = []
        for pos, vel, life, col in self.particles:
            pos = pos + vel * (1 / FPS)
            life -= 1 / FPS
            if life > 0:
                alive_particles.append((pos, vel * 0.96, life, col))
                pygame.draw.circle(self.screen, (*col,), pos + cam, max(1, int(4 * life / 0.7)))
        self.particles = alive_particles

        if self.winner:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 6, 16, 170))
            self.screen.blit(overlay, (0, 0))
            txt = "Victoire Arcane" if self.winner == "player" else "Défaite Occulte"
            c = GOOD if self.winner == "player" else BAD
            t1 = self.title_font.render(txt, True, c)
            t2 = self.ui_font.render("R: recommencer | Échap: quitter", True, TEXT)
            self.screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 12))

        pygame.display.flip()

    def _reset(self) -> None:
        self.player.hp, self.player.mana = self.player.hp_max, self.player.mana_max
        self.enemy.hp, self.enemy.mana = self.enemy.hp_max, self.enemy.mana_max
        self.player.pos = pygame.Vector2(220, HEIGHT * 0.5)
        self.enemy.pos = pygame.Vector2(WIDTH - 220, HEIGHT * 0.5)
        self.projectiles.clear()
        self.rings.clear()
        self.enemy_phase = "pressure"
        self.enemy_intent = "Opening stance"
        self.combo = 0
        self.enemy_cast_timer = 0.9
        self.enemy_dash_timer = 2.0
        self.winner = None
        self.message = "Nouvelle bataille. Ajuste les coefficients et lance tes formes."

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and self.winner:
                        self._reset()
                    elif not self.winner:
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                            self._update_equation_channels(event.key)
                        elif event.key == pygame.K_f:
                            self.selected_spell = 0
                            self._cast(self.player, self.enemy, SPELLS[0], "player")
                        elif event.key == pygame.K_g:
                            self.selected_spell = 1
                            self._cast(self.player, self.enemy, SPELLS[1], "player")
                        elif event.key == pygame.K_h:
                            self.selected_spell = 2
                            self._cast(self.player, self.enemy, SPELLS[2], "player")
                        elif event.key == pygame.K_SPACE and self.player.mana >= 18:
                            self.player.mana -= 18
                            self.player.shield = min(26, self.player.shield + 12)
                            self.message = "Barrière active."

            if not self.winner:
                self.player.mana = min(self.player.mana_max, self.player.mana + dt * 12)
                self.enemy.mana = min(self.enemy.mana_max, self.enemy.mana + dt * 9)
                self.player.shield = max(0.0, self.player.shield - dt * 2.2)
                self.enemy.shield = max(0.0, self.enemy.shield - dt * 1.5)
                self.player.slow = max(0.0, self.player.slow - dt)
                self.enemy.burn = max(0.0, self.enemy.burn - dt)
                self.enemy.hp -= self.enemy.burn * dt * 3.2
                for spell in SPELLS:
                    self.cooldowns[spell.name] = max(0.0, self.cooldowns[spell.name] - dt)

                self._handle_player_keys(dt)
                self._enemy_ai(dt)
                self._tick_projectiles(dt)

                for star in self.stars:
                    star.x -= 35 * dt
                    if star.x < 0:
                        star.x = WIDTH
                        star.y = random.randint(0, HEIGHT)

                if self.enemy.hp <= 0:
                    self.winner = "player"
                elif self.player.hp <= 0:
                    self.winner = "enemy"

            self._draw()

        pygame.quit()
        raise SystemExit(0)


def main() -> None:
    ArcaneEquationGame().run()


if __name__ == "__main__":
    main()
