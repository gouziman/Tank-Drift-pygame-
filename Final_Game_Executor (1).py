import pygame
import sys
import math
import random
import numpy as np

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors (Enhanced Sci-Fi Tactical palette)
BG_COLOR = (12, 14, 20)  # Deep space dark blue-gray
BG_GRID_COLOR = (25, 30, 45)
WALL_COLOR = (55, 65, 85)
WALL_HIGHLIGHT = (75, 85, 105)
MUD_COLOR = (40, 32, 22)
MUD_HIGHLIGHT = (55, 45, 35)
PLAYER_HULL_COLOR = (78, 204, 163)  # Neon Teal
PLAYER_HULL_GLOW = (78, 204, 163, 80)
PLAYER_TURRET_COLOR = (200, 225, 240)
PLAYER_OVERDRIVE_COLOR = (255, 180, 50)  # Warm Orange-Gold
PLAYER_OVERDRIVE_GLOW = (255, 180, 50, 100)
ENEMY_COLOR = (235, 85, 75)  # Vibrant Red
ENEMY_GLOW = (235, 85, 75, 60)
BULLET_COLOR = (255, 250, 150)
BULLET_GLOW = (255, 250, 150, 150)
BULLET_TRAIL_COLOR = (255, 200, 100)
TEXT_COLOR = (245, 245, 250)
TEXT_SHADOW = (20, 20, 30)
HUD_BG_COLOR = (20, 25, 35, 200)
HEALTH_HIGH = (80, 220, 120)
HEALTH_LOW = (255, 100, 100)

# Particle colors
EXPLOSION_COLORS = [(255, 200, 50), (255, 150, 50), (255, 100, 50), (200, 80, 40)]
MUZZLE_COLORS = [(200, 255, 255), (150, 255, 255), (100, 255, 255)]
SPARK_COLORS = [(255, 255, 200), (255, 220, 150), (255, 200, 100)]

# Physics constants
HULL_ACCELERATION = 0.15
HULL_ROTATION_SPEED = 3
NORMAL_FRICTION = 0.98
MUD_FRICTION = 0.92
MAX_SPEED = 5.0

# Combat constants
NORMAL_FIRE_COOLDOWN = 15
OVERDRIVE_FIRE_COOLDOWN = 8
BULLET_SPEED = 12
BULLET_DAMAGE = 25
ENEMY_SPEED = 2.0
ENEMY_DAMAGE = 10
ENEMY_HP = 50
PLAYER_MAX_HP = 100

# Game constants
OVERDRIVE_THRESHOLD = 1000
WALL_COUNT = 12
MUD_COUNT = 8
ENEMY_SPAWN_INTERVAL = 180

# Enhanced particle system
class Particle:
    def __init__(self, x, y, color, velocity, lifetime, size=4, fade=True, gravity=0):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = velocity
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.fade = fade
        self.gravity = gravity
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)

    def update(self):
        self.pos += self.vel
        self.vel.y += self.gravity
        self.lifetime -= 1
        self.rotation += self.rotation_speed
        if self.fade:
            self.size *= 0.96
        return self.lifetime > 0 and self.size > 0.5

    def draw(self, surface, camera):
        alpha = int((self.lifetime / self.max_lifetime) * 255) if self.fade else 255
        pos = camera.apply(self.pos)

        # Create glow effect
        glow_size = int(self.size * 2.5)
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(alpha * 0.3)
        pygame.draw.circle(glow_surface, (*self.color, glow_alpha), (glow_size, glow_size), glow_size)
        surface.blit(glow_surface, (pos.x - glow_size, pos.y - glow_size))

        # Main particle
        particle_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(particle_surface, (pos.x - self.size, pos.y - self.size))

# Trail particle for bullets
class TrailParticle:
    def __init__(self, x, y, color):
        self.pos = pygame.math.Vector2(x, y)
        self.color = color
        self.lifetime = 15
        self.size = 3

    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, surface, camera):
        alpha = int((self.lifetime / 15) * 180)
        pos = camera.apply(self.pos)
        trail_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(trail_surface, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(trail_surface, (pos.x - self.size, pos.y - self.size))

# Enhanced bullet with trail
class Bullet:
    def __init__(self, x, y, angle):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(BULLET_SPEED, 0).rotate(-angle)
        self.radius = 5
        self.active = True
        self.trail_timer = 0

    def update(self):
        # Add trail
        self.trail_timer += 1
        if self.trail_timer >= 2:
            self.trail_timer = 0
            return TrailParticle(self.pos.x, self.pos.y, BULLET_TRAIL_COLOR)

        self.pos += self.vel

        # Check bounds
        if (self.pos.x < -50 or self.pos.x > SCREEN_WIDTH + 50 or 
            self.pos.y < -50 or self.pos.y > SCREEN_HEIGHT + 50):
            self.active = False

        return None

    def draw(self, surface, camera):
        pos = camera.apply(self.pos)

        # Glow effect
        glow_surface = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, BULLET_GLOW, (12, 12), 12)
        surface.blit(glow_surface, (pos.x - 12, pos.y - 12))

        # Core
        pygame.draw.circle(surface, BULLET_COLOR, (int(pos.x), int(pos.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(pos.x), int(pos.y)), 2)

    def get_rect(self):
        return pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, 
                          self.radius * 2, self.radius * 2)

# Enhanced enemy with hexagon and glow
class Enemy:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.angle = 0
        self.hp = ENEMY_HP
        self.radius = 22
        self.active = True
        self.pulse_phase = random.uniform(0, math.pi * 2)

    def update(self, player_pos):
        # Track player
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * ENEMY_SPEED
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))

        self.pulse_phase += 0.1

    def draw(self, surface, camera):
        pos = camera.apply(self.pos)

        # Glow effect
        pulse = 1 + math.sin(self.pulse_phase) * 0.1
        glow_size = int(self.radius * 2.5 * pulse)
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, ENEMY_GLOW, (glow_size, glow_size), glow_size)
        surface.blit(glow_surface, (pos.x - glow_size, pos.y - glow_size))

        # Draw hexagon
        points = []
        for i in range(6):
            angle_rad = math.radians(self.angle + i * 60)
            x = pos.x + self.radius * math.cos(angle_rad)
            y = pos.y + self.radius * math.sin(angle_rad)
            points.append((x, y))

        pygame.draw.polygon(surface, ENEMY_COLOR, points)
        pygame.draw.polygon(surface, (180, 60, 55), points, 3)

        # Inner hexagon
        inner_points = []
        for i in range(6):
            angle_rad = math.radians(self.angle + i * 60 + 30)
            x = pos.x + (self.radius * 0.5) * math.cos(angle_rad)
            y = pos.y + (self.radius * 0.5) * math.sin(angle_rad)
            inner_points.append((x, y))
        pygame.draw.polygon(surface, (150, 50, 45), inner_points)

        # Turret circle with glow
        turret_glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(turret_glow, (200, 70, 65, 100), (15, 15), 12)
        surface.blit(turret_glow, (pos.x - 15, pos.y - 15))
        pygame.draw.circle(surface, (220, 90, 85), (int(pos.x), int(pos.y)), 10)
        pygame.draw.circle(surface, (150, 50, 45), (int(pos.x), int(pos.y)), 10, 2)

        # Health bar
        if self.hp < ENEMY_HP:
            bar_width = 40
            bar_height = 4
            health_percent = self.hp / ENEMY_HP
            bar_x = pos.x - bar_width // 2
            bar_y = pos.y - self.radius - 12

            pygame.draw.rect(surface, (50, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, (255, 100, 100), (bar_x, bar_y, int(bar_width * health_percent), bar_height))

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, 
                          self.radius * 2, self.radius * 2)

# Enhanced player with better visuals
class Player:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.hull_angle = 0
        self.turret_angle = 0
        self.hp = PLAYER_MAX_HP
        self.score = 0
        self.fire_cooldown = 0
        self.recoil_timer = 0
        self.in_mud = False
        self.overdrive = False
        self.tracks = []
        self.muzzle_flash = False
        self.engine_particles = []

    def get_fire_cooldown_max(self):
        return OVERDRIVE_FIRE_COOLDOWN if self.overdrive else NORMAL_FIRE_COOLDOWN

    def get_defense_multiplier(self):
        return 1.5 if self.overdrive else 1.0

    def update(self, walls, mud_zones):
        keys = pygame.key.get_pressed()

        # Hull rotation
        if keys[pygame.K_a]:
            self.hull_angle += HULL_ROTATION_SPEED
        if keys[pygame.K_d]:
            self.hull_angle -= HULL_ROTATION_SPEED

        # Acceleration
        acceleration = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]:
            forward = pygame.math.Vector2(HULL_ACCELERATION, 0).rotate(-self.hull_angle)
            acceleration += forward
        if keys[pygame.K_s]:
            backward = pygame.math.Vector2(-HULL_ACCELERATION * 0.6, 0).rotate(-self.hull_angle)
            acceleration += backward

        self.vel += acceleration

        # Engine particles when moving
        if self.vel.length() > 1:
            if random.random() < 0.3:
                track_offset = pygame.math.Vector2(10, 0).rotate(-self.hull_angle)
                engine_pos = self.pos - pygame.math.Vector2(20, 0).rotate(-self.hull_angle)
                particle_vel = -self.vel * 0.3 + pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                self.engine_particles.append(
                    Particle(engine_pos.x, engine_pos.y, (100, 150, 180), particle_vel, 20, 3, True, 0)
                )

        # Check mud
        self.in_mud = False
        player_rect = pygame.Rect(self.pos.x - 15, self.pos.y - 15, 30, 30)
        for mud in mud_zones:
            if player_rect.colliderect(mud):
                self.in_mud = True
                break

        # Friction
        friction = MUD_FRICTION if self.in_mud else NORMAL_FRICTION
        self.vel *= friction

        # Speed limit
        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

        # Movement with collision
        new_pos = self.pos + self.vel
        player_rect = pygame.Rect(new_pos.x - 15, new_pos.y - 15, 30, 30)
        can_move = True
        for wall in walls:
            if player_rect.colliderect(wall):
                can_move = False
                self.vel *= -0.5
                break

        if (new_pos.x < 20 or new_pos.x > SCREEN_WIDTH - 20 or
            new_pos.y < 20 or new_pos.y > SCREEN_HEIGHT - 20):
            can_move = False
            self.vel *= -0.5

        if can_move:
            self.pos = new_pos

        # Turret aiming
        mouse_pos = pygame.mouse.get_pos()
        direction = pygame.math.Vector2(mouse_pos) - self.pos
        self.turret_angle = math.degrees(math.atan2(-direction.y, direction.x))

        # Cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.recoil_timer > 0:
            self.recoil_timer -= 1

        # Tracks
        if self.vel.length() > 0.5:
            track_offset = pygame.math.Vector2(12, 0).rotate(-self.hull_angle)
            left_track = self.pos - track_offset
            right_track = self.pos + track_offset
            self.tracks.append({'pos': left_track, 'alpha': 120, 'time': pygame.time.get_ticks()})
            self.tracks.append({'pos': right_track, 'alpha': 120, 'time': pygame.time.get_ticks()})

        # Fade tracks
        current_time = pygame.time.get_ticks()
        self.tracks = [t for t in self.tracks if current_time - t['time'] < 3000]
        for track in self.tracks:
            track['alpha'] = max(0, track['alpha'] - 0.8)

        # Engine particles
        self.engine_particles = [p for p in self.engine_particles if p.update()]

        # Overdrive check
        self.overdrive = self.score >= OVERDRIVE_THRESHOLD

    def fire(self, sound_manager, camera):
        if self.fire_cooldown <= 0:
            self.fire_cooldown = self.get_fire_cooldown_max()
            self.recoil_timer = 5
            self.muzzle_flash = True

            barrel_length = 35
            bullet_pos = self.pos + pygame.math.Vector2(barrel_length, 0).rotate(-self.turret_angle)

            camera.add_shake(3)
            sound_manager.play('shoot')

            return Bullet(bullet_pos.x, bullet_pos.y, self.turret_angle)
        return None

    def take_damage(self, damage):
        actual_damage = int(damage * self.get_defense_multiplier())
        self.hp -= actual_damage
        return self.hp <= 0

    def draw(self, surface, camera):
        # Draw tracks
        for track in self.tracks:
            pos = camera.apply(track['pos'])
            track_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.rect(track_surface, (70, 65, 55, int(track['alpha'])), (0, 0, 8, 8), border_radius=2)
            surface.blit(track_surface, (pos.x - 4, pos.y - 4))

        # Draw engine particles
        for particle in self.engine_particles:
            particle.draw(surface, camera)

        pos = camera.apply(self.pos)

        hull_color = PLAYER_OVERDRIVE_COLOR if self.overdrive else PLAYER_HULL_COLOR
        hull_glow = PLAYER_OVERDRIVE_GLOW if self.overdrive else PLAYER_HULL_GLOW

        # Hull glow
        glow_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, hull_glow, (40, 40), 35)
        surface.blit(glow_surface, (pos.x - 40, pos.y - 40))

        # Draw hull
        hull_surf = pygame.Surface((44, 34), pygame.SRCALPHA)
        pygame.draw.rect(hull_surf, hull_color, (0, 0, 44, 34), border_radius=5)
        pygame.draw.rect(hull_surf, (40, 50, 60), (0, 0, 44, 34), 2, border_radius=5)

        # Hull details
        pygame.draw.rect(hull_surf, (50, 60, 70), (5, 5, 34, 24), border_radius=3)

        rotated_hull = pygame.transform.rotate(hull_surf, self.hull_angle)
        hull_rect = rotated_hull.get_rect(center=(pos.x, pos.y))
        surface.blit(rotated_hull, hull_rect)

        # Turret barrel
        barrel_length = 35 - self.recoil_timer
        barrel_end = pos + pygame.math.Vector2(barrel_length, 0).rotate(-self.turret_angle)

        # Barrel glow
        barrel_glow_surf = pygame.Surface((int(barrel_length + 20), 20), pygame.SRCALPHA)
        pygame.draw.line(barrel_glow_surf, (*PLAYER_TURRET_COLOR, 80), (10, 10), (barrel_length + 10, 10), 14)
        surface.blit(barrel_glow_surf, (pos.x - 10, pos.y - 10))

        pygame.draw.line(surface, PLAYER_TURRET_COLOR, pos, barrel_end, 7)
        pygame.draw.line(surface, (80, 100, 110), pos, barrel_end, 3)

        # Muzzle flash
        if self.muzzle_flash:
            flash_pos = barrel_end
            flash_sizes = [25, 18, 12]
            flash_alphas = [200, 150, 100]
            for size, alpha in zip(flash_sizes, flash_alphas):
                flash_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color = random.choice(MUZZLE_COLORS)
                pygame.draw.circle(flash_surface, (*color, alpha), (size, size), size)
                surface.blit(flash_surface, (flash_pos.x - size, flash_pos.y - size))

            # Sparks
            for _ in range(5):
                spark_vel = pygame.math.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
                spark = Particle(flash_pos.x, flash_pos.y, random.choice(SPARK_COLORS), 
                               spark_vel, random.randint(5, 10), 2, True, 0.2)
                return spark  # Return spark to be added to game particles

            self.muzzle_flash = False

        # Turret body
        turret_glow = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(turret_glow, (*PLAYER_TURRET_COLOR, 60), (18, 18), 14)
        surface.blit(turret_glow, (pos.x - 18, pos.y - 18))

        pygame.draw.circle(surface, PLAYER_TURRET_COLOR, (int(pos.x), int(pos.y)), 13)
        pygame.draw.circle(surface, (80, 100, 110), (int(pos.x), int(pos.y)), 13, 2)

        # Turret center
        pygame.draw.circle(surface, (150, 170, 180), (int(pos.x), int(pos.y)), 6)

        # Overdrive effect
        if self.overdrive:
            overdrive_glow = pygame.Surface((70, 70), pygame.SRCALPHA)
            pulse = 1 + math.sin(pygame.time.get_ticks() * 0.01) * 0.2
            pygame.draw.circle(overdrive_glow, (255, 180, 50, int(40 * pulse)), (35, 35), int(30 * pulse))
            surface.blit(overdrive_glow, (pos.x - 35, pos.y - 35))

        return None

    def get_rect(self):
        return pygame.Rect(self.pos.x - 22, self.pos.y - 17, 44, 34)

# SoundManager
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.generate_sounds()

    def generate_sounds(self):
        try:
            # Shoot sound
            duration = 0.1
            sample_rate = 44100
            n_samples = int(duration * sample_rate)
            shoot_samples = np.random.uniform(-0.3, 0.3, n_samples)
            envelope = np.linspace(1, 0, n_samples)
            shoot_samples = shoot_samples * envelope
            shoot_samples = (shoot_samples * 32767).astype(np.int16)
            shoot_stereo = np.column_stack((shoot_samples, shoot_samples))
            self.sounds['shoot'] = pygame.sndarray.make_sound(shoot_stereo)

            # Explosion sound
            duration = 0.3
            n_samples = int(duration * sample_rate)
            exp_samples = np.random.uniform(-0.4, 0.4, n_samples)
            for i in range(1, n_samples):
                exp_samples[i] = exp_samples[i] * 0.3 + exp_samples[i-1] * 0.7
            envelope = np.linspace(1, 0, n_samples)
            exp_samples = exp_samples * envelope
            exp_samples = (exp_samples * 32767).astype(np.int16)
            exp_stereo = np.column_stack((exp_samples, exp_samples))
            self.sounds['explosion'] = pygame.sndarray.make_sound(exp_stereo)

            # Hit sound
            duration = 0.08
            n_samples = int(duration * sample_rate)
            t = np.linspace(0, duration, n_samples)
            hit_samples = np.sin(2 * np.pi * 440 * t) * 0.3
            envelope = np.linspace(1, 0, n_samples)
            hit_samples = hit_samples * envelope
            hit_samples = (hit_samples * 32767).astype(np.int16)
            hit_stereo = np.column_stack((hit_samples, hit_samples))
            self.sounds['hit'] = pygame.sndarray.make_sound(hit_stereo)

        except Exception as e:
            print(f"Sound generation failed: {e}")
            self.sounds = {}

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

# Camera with smooth shake
class Camera:
    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
        self.shake_intensity = 0

    def add_shake(self, intensity):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def update(self):
        if self.shake_intensity > 0:
            self.offset.x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.offset.y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity *= 0.88
            if self.shake_intensity < 0.3:
                self.shake_intensity = 0
                self.offset = pygame.math.Vector2(0, 0)

    def apply(self, pos):
        return pos + self.offset

# Main Game class
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Tank Commander - Phase 2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)

        self.sound_manager = SoundManager()
        self.camera = Camera()

        self.state = "MENU"
        self.reset_game()

        # Pre-render background
        self.background = self.create_background()

    def create_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(BG_COLOR)

        # Draw subtle grid
        grid_size = 50
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(bg, BG_GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(bg, BG_GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

        # Add subtle stars
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 2)
            alpha = random.randint(30, 80)
            star_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(star_surface, (255, 255, 255, alpha), (size, size), size)
            bg.blit(star_surface, (x - size, y - size))

        return bg

    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.trails = []
        self.walls = []
        self.mud_zones = []
        self.spawn_timer = 0
        self.wave = 1

        self.generate_map()

    def generate_map(self):
        self.walls = []
        self.mud_zones = []

        safe_zone = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 150, 300, 300)

        # Generate walls
        for _ in range(WALL_COUNT):
            valid = False
            while not valid:
                w = random.randint(60, 150)
                h = random.randint(60, 150)
                x = random.randint(50, SCREEN_WIDTH - w - 50)
                y = random.randint(50, SCREEN_HEIGHT - h - 50)
                wall = pygame.Rect(x, y, w, h)

                if not wall.colliderect(safe_zone):
                    overlap = False
                    for existing in self.walls:
                        if wall.colliderect(existing):
                            overlap = True
                            break
                    if not overlap:
                        self.walls.append(wall)
                        valid = True

        # Generate mud zones
        for _ in range(MUD_COUNT):
            valid = False
            while not valid:
                w = random.randint(80, 200)
                h = random.randint(80, 200)
                x = random.randint(50, SCREEN_WIDTH - w - 50)
                y = random.randint(50, SCREEN_HEIGHT - h - 50)
                mud = pygame.Rect(x, y, w, h)

                if not mud.colliderect(safe_zone):
                    overlap = False
                    for wall in self.walls:
                        if mud.colliderect(wall):
                            overlap = True
                            break
                    for existing in self.mud_zones:
                        if mud.colliderect(existing):
                            overlap = True
                            break
                    if not overlap:
                        self.mud_zones.append(mud)
                        valid = True

    def spawn_enemy(self):
        side = random.randint(0, 3)
        if side == 0:
            x = random.randint(0, SCREEN_WIDTH)
            y = -30
        elif side == 1:
            x = SCREEN_WIDTH + 30
            y = random.randint(0, SCREEN_HEIGHT)
        elif side == 2:
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 30
        else:
            x = -30
            y = random.randint(0, SCREEN_HEIGHT)

        self.enemies.append(Enemy(x, y))

    def create_explosion(self, pos, color, count=20):
        # Main explosion particles
        for _ in range(count):
            vel = pygame.math.Vector2(random.uniform(-5, 5), random.uniform(-5, 5))
            particle_color = random.choice(EXPLOSION_COLORS)
            self.particles.append(Particle(pos.x, pos.y, particle_color, vel, random.randint(30, 70), 
                                          random.uniform(4, 8), True, 0.1))

        # Smoke particles
        for _ in range(count // 2):
            vel = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-3, -1))
            self.particles.append(Particle(pos.x, pos.y, (80, 70, 60), vel, random.randint(40, 80), 
                                          random.uniform(6, 12), True, -0.02))

        # Sparks
        for _ in range(10):
            vel = pygame.math.Vector2(random.uniform(-6, 6), random.uniform(-6, 6))
            self.particles.append(Particle(pos.x, pos.y, random.choice(SPARK_COLORS), vel, 
                                          random.randint(10, 25), random.uniform(2, 4), True, 0.3))

    def update(self):
        if self.state == "PLAYING":
            self.camera.update()

            # Update player
            self.player.update(self.walls, self.mud_zones)

            # Handle shooting
            if pygame.mouse.get_pressed()[0]:
                bullet = self.player.fire(self.sound_manager, self.camera)
                if bullet:
                    self.bullets.append(bullet)

            # Update bullets and collect trails
            for bullet in self.bullets[:]:
                trail = bullet.update()
                if trail:
                    self.trails.append(trail)

                if not bullet.active:
                    self.bullets.remove(bullet)
                    continue

                bullet_rect = bullet.get_rect()
                for wall in self.walls:
                    if bullet_rect.colliderect(wall):
                        bullet.active = False
                        self.create_explosion(bullet.pos, (180, 180, 140), 10)
                        break

                if not bullet.active:
                    continue

                for enemy in self.enemies[:]:
                    enemy_rect = enemy.get_rect()
                    if bullet_rect.colliderect(enemy_rect):
                        bullet.active = False
                        died = enemy.take_damage(BULLET_DAMAGE)
                        self.sound_manager.play('hit')
                        self.create_explosion(bullet.pos, ENEMY_COLOR, 12)
                        if died:
                            self.enemies.remove(enemy)
                            self.player.score += 100
                            self.create_explosion(enemy.pos, ENEMY_COLOR, 30)
                            self.sound_manager.play('explosion')
                            self.camera.add_shake(6)
                        break

            self.bullets = [b for b in self.bullets if b.active]

            # Update enemies
            for enemy in self.enemies[:]:
                enemy.update(self.player.pos)

                enemy_rect = enemy.get_rect()
                player_rect = self.player.get_rect()
                if enemy_rect.colliderect(player_rect):
                    died = self.player.take_damage(ENEMY_DAMAGE)
                    self.create_explosion(self.player.pos, PLAYER_HULL_COLOR, 15)
                    self.camera.add_shake(10)
                    self.enemies.remove(enemy)
                    self.create_explosion(enemy.pos, ENEMY_COLOR, 30)
                    self.sound_manager.play('explosion')

                    if died:
                        self.state = "GAMEOVER"

            # Spawn enemies
            self.spawn_timer += 1
            if self.spawn_timer >= ENEMY_SPAWN_INTERVAL:
                self.spawn_timer = 0
                self.spawn_enemy()

            # Update particles
            self.particles = [p for p in self.particles if p.update()]

            # Update trails
            self.trails = [t for t in self.trails if t.update()]

    def draw(self):
        # Draw pre-rendered background
        self.screen.blit(self.background, (0, 0))

        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING" or self.state == "GAMEOVER":
            self.draw_game()
            if self.state == "GAMEOVER":
                self.draw_gameover()

        pygame.display.flip()

    def draw_menu(self):
        # Title with glow
        title = self.large_font.render("NEON TANK COMMANDER", True, PLAYER_HULL_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120))

        # Title glow
        for i in range(3):
            glow_title = self.large_font.render("NEON TANK COMMANDER", True, (*PLAYER_HULL_COLOR, max(0, 50 - i * 15)))
            glow_rect = glow_title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120))
            self.screen.blit(glow_title, (glow_rect.x + i * 2, glow_rect.y + i * 2))

        self.screen.blit(title, title_rect)

        instruction = self.font.render("Press SPACE to Start", True, TEXT_COLOR)
        inst_rect = instruction.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
        self.screen.blit(instruction, inst_rect)

        controls = [
            "WASD - Move Hull",
            "Mouse - Aim Turret",
            "Left Click - Fire",
            "R - Restart (anytime)"
        ]

        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, (140, 150, 170))
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40 + i * 35))
            self.screen.blit(text, text_rect)

        # Decorative elements
        for i in range(8):
            angle = (pygame.time.get_ticks() * 0.001 + i * (math.pi * 2 / 8)) % (math.pi * 2)
            radius = 200 + math.sin(pygame.time.get_ticks() * 0.002 + i) * 20
            x = SCREEN_WIDTH//2 + math.cos(angle) * radius
            y = SCREEN_HEIGHT//2 + math.sin(angle) * radius
            pygame.draw.circle(self.screen, (*PLAYER_HULL_COLOR, 30), (int(x), int(y)), 4)

    def draw_game(self):
        # Draw mud zones with texture
        for mud in self.mud_zones:
            mud_pos = self.camera.apply(pygame.math.Vector2(mud.x, mud.y))

            # Base mud
            mud_surface = pygame.Surface((mud.width, mud.height), pygame.SRCALPHA)
            pygame.draw.rect(mud_surface, (*MUD_COLOR, 200), (0, 0, mud.width, mud.height), border_radius=8)

            # Texture dots
            for _ in range(int(mud.width * mud.height / 400)):
                dot_x = random.randint(0, mud.width)
                dot_y = random.randint(0, mud.height)
                pygame.draw.circle(mud_surface, (*MUD_HIGHLIGHT, 80), (dot_x, dot_y), 2)

            self.screen.blit(mud_surface, (mud_pos.x, mud_pos.y))

            # Border
            pygame.draw.rect(self.screen, MUD_HIGHLIGHT, 
                           (mud_pos.x, mud_pos.y, mud.width, mud.height), 2, border_radius=8)

        # Draw walls with 3D effect
        for wall in self.walls:
            wall_pos = self.camera.apply(pygame.math.Vector2(wall.x, wall.y))

            # Shadow
            shadow_surface = pygame.Surface((wall.width + 8, wall.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (10, 10, 15, 100), (4, 4, wall.width, wall.height), border_radius=4)
            self.screen.blit(shadow_surface, (wall_pos.x - 4, wall_pos.y - 4))

            # Main wall
            pygame.draw.rect(self.screen, WALL_COLOR, 
                           (wall_pos.x, wall_pos.y, wall.width, wall.height), border_radius=4)

            # Highlight edges
            pygame.draw.rect(self.screen, WALL_HIGHLIGHT, 
                           (wall_pos.x, wall_pos.y, wall.width, wall.height), 3, border_radius=4)

            # Top highlight for 3D effect
            pygame.draw.line(self.screen, (90, 100, 120), 
                           (wall_pos.x, wall_pos.y), (wall_pos.x + wall.width, wall_pos.y), 2)

        # Draw trails
        for trail in self.trails:
            trail.draw(self.screen, self.camera)

        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen, self.camera)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)

        # Draw player
        spark = self.player.draw(self.screen, self.camera)
        if spark:
            self.particles.append(spark)

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        # Health bar container
        health_width = 220
        health_height = 24
        health_x = 20
        health_y = 20

        # Background panel
        panel_surface = pygame.Surface((health_width + 20, health_height + 40), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, HUD_BG_COLOR, (0, 0, health_width + 20, health_height + 40), border_radius=8)
        self.screen.blit(panel_surface, (health_x - 10, health_y - 10))

        # Health bar background
        pygame.draw.rect(self.screen, (30, 35, 45), 
                        (health_x, health_y, health_width, health_height), border_radius=4)

        # Health bar fill with gradient effect
        health_percent = max(0, self.player.hp / PLAYER_MAX_HP)
        fill_width = int(health_width * health_percent)
        health_color = HEALTH_HIGH if health_percent > 0.5 else HEALTH_LOW

        if fill_width > 0:
            pygame.draw.rect(self.screen, health_color, 
                           (health_x, health_y, fill_width, health_height), border_radius=4)

            # Highlight on top
            highlight_width = max(0, fill_width - 4)
            if highlight_width > 0:
                pygame.draw.rect(self.screen, (*health_color, 150), 
                               (health_x + 2, health_y + 2, highlight_width, health_height // 3), border_radius=2)

        # Border
        pygame.draw.rect(self.screen, (60, 70, 90), 
                        (health_x, health_y, health_width, health_height), 2, border_radius=4)

        # Health text with shadow
        health_text = self.font.render(f"HP: {self.player.hp}/{PLAYER_MAX_HP}", True, TEXT_COLOR)
        health_shadow = self.font.render(f"HP: {self.player.hp}/{PLAYER_MAX_HP}", True, TEXT_SHADOW)
        self.screen.blit(health_shadow, (health_x + 2, health_y + health_height + 8))
        self.screen.blit(health_text, (health_x, health_y + health_height + 6))

        # Score panel
        score_width = 180
        score_surface = pygame.Surface((score_width + 20, 50), pygame.SRCALPHA)
        pygame.draw.rect(score_surface, HUD_BG_COLOR, (0, 0, score_width + 20, 50), border_radius=8)
        self.screen.blit(score_surface, (SCREEN_WIDTH - score_width - 30, 15))

        score_text = self.font.render(f"SCORE: {self.player.score}", True, TEXT_COLOR)
        score_shadow = self.font.render(f"SCORE: {self.player.score}", True, TEXT_SHADOW)
        score_rect = score_text.get_rect()
        self.screen.blit(score_shadow, (SCREEN_WIDTH - score_width - 20 + 2, 32))
        self.screen.blit(score_text, (SCREEN_WIDTH - score_width - 20, 30))

        # Overdrive indicator
        if self.player.overdrive:
            overdrive_width = 280
            overdrive_surface = pygame.Surface((overdrive_width, 40), pygame.SRCALPHA)
            pygame.draw.rect(overdrive_surface, (*PLAYER_OVERDRIVE_COLOR, 40), (0, 0, overdrive_width, 40), border_radius=8)

            overdrive_text = self.font.render("⚡ OVERDRIVE ACTIVE ⚡", True, PLAYER_OVERDRIVE_COLOR)
            overdrive_rect = overdrive_text.get_rect(center=(overdrive_width // 2, 20))
            overdrive_surface.blit(overdrive_text, overdrive_rect)

            # Pulsing glow
            pulse = 1 + math.sin(pygame.time.get_ticks() * 0.008) * 0.3
            glow_width = int(overdrive_width * pulse)
            glow_surface = pygame.Surface((glow_width, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surface, (*PLAYER_OVERDRIVE_COLOR, 50), 
                              (0, 0, glow_width, 50))

            final_x = SCREEN_WIDTH // 2 - overdrive_width // 2
            self.screen.blit(glow_surface, (final_x + (overdrive_width - glow_width) // 2, 55))
            self.screen.blit(overdrive_surface, (final_x, 60))

        # Controls reminder
        if self.player.score < 200:
            reminder_text = self.small_font.render("WASD to Move | Mouse to Aim | Click to Fire", True, (100, 110, 130))
            reminder_rect = reminder_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 25))

            reminder_surface = pygame.Surface((reminder_rect.width + 20, 30), pygame.SRCALPHA)
            reminder_surface.fill((0, 0, 0, 80))
            self.screen.blit(reminder_surface, (reminder_rect.x - 10, reminder_rect.y - 5))
            self.screen.blit(reminder_text, reminder_rect)

    def draw_gameover(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 10, 200))
        self.screen.blit(overlay, (0, 0))

        # Game Over text with glow
        gameover_text = self.large_font.render("GAME OVER", True, ENEMY_COLOR)
        gameover_rect = gameover_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))

        for i in range(3):
            glow = self.large_font.render("GAME OVER", True, (*ENEMY_COLOR, max(0, 60 - i * 20)))
            glow_rect = glow.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
            self.screen.blit(glow, (glow_rect.x + i * 3, glow_rect.y + i * 3))

        self.screen.blit(gameover_text, gameover_rect)

        # Score panel
        score_panel = pygame.Surface((300, 80), pygame.SRCALPHA)
        pygame.draw.rect(score_panel, (*ENEMY_COLOR, 30), (0, 0, 300, 80), border_radius=10)
        score_panel_rect = score_panel.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(score_panel, score_panel_rect)

        score_text = self.font.render(f"Final Score: {self.player.score}", True, TEXT_COLOR)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(score_text, score_rect)

        # Restart instruction
        restart_text = self.font.render("Press R to Restart or SPACE for Menu", True, TEXT_COLOR)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90))
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.state == "MENU" or self.state == "GAMEOVER":
                            self.reset_game()
                            self.state = "PLAYING"

                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "PLAYING"

            self.update()
            self.draw()

        pygame.quit()
        sys.exit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
