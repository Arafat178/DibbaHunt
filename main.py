import random
import math
import pygame
from pygame import mixer
import os
import asyncio
import sys

# ---------------- Init (pygbag-friendly) ----------------
pygame.init()
try:
    # কিছু ব্রাউজারে mixer init ব্যর্থ হতে পারে—fail হলেও গেম চলবে
    mixer.pre_init(44100, -16, 2, 512)
    mixer.init()
    SOUND_OK = True
except Exception:
    SOUND_OK = False

clock = pygame.time.Clock()

# ---------------- Asset Loads ----------------
background = pygame.image.load("assets/images/gamebg1.png")
cover = pygame.image.load("assets/images/DIBBAHUNT.png")
tank_img = pygame.image.load("assets/images/tankF.png")
jet_img = pygame.image.load("assets/images/jet.png")
diploma_img = pygame.image.load("assets/images/Diploma_Milk1.png")

explosion_frames = [pygame.image.load(f"assets/images/e-{i}.png") for i in range(21)]

if SOUND_OK:
    try:
        mixer.music.load("assets/sounds/bgmusic.ogg")
        mixer.music.play(-1)
        mixer.music.set_volume(0.5)
    except Exception:
        SOUND_OK = False

def safe_sound(path):
    if not SOUND_OK:
        return None
    try:
        return mixer.Sound(path)
    except Exception:
        return None

gun_sound = safe_sound("assets/sounds/fianl_tank.ogg")
siren_sound = safe_sound("assets/sounds/siren1.ogg")
exp_sound  = safe_sound("assets/sounds/explosion.ogg")

# ---------------- Display ----------------
screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption('Hunter')

# ---------------- Draw Helpers ----------------
def tankF(x, y):
    screen.blit(tank_img, (x, y))

def tank_pipe(x1, y1, x2, y2):
    pygame.draw.line(screen, (0, 0, 0), (x1, y1), (x2, y2), 10)
    pygame.draw.circle(screen, (0, 0, 0), (x2, y2), 8)

def bullet(x, y):
    pygame.draw.circle(screen, (155, 0, 0), (int(x), int(y)), 10)

def jet(x, y):
    screen.blit(jet_img, (x, y))

def diploma(x, y):
    screen.blit(diploma_img, (x, y))

def explosionXY(xe, ye, frame):
    index = frame // 50 #change
    if index < len(explosion_frames):
        x = xe - 100
        y = ye - 100
        screen.blit(explosion_frames[index], (x, y))

# Fonts (SysFont ওয়েবে fallback নেয়; সমস্যা হলে default ব্যবহার করবে)
sfont = pygame.font.SysFont('freesansbold.ttf', 40)
def scoreXY(x, y, score_value):
    score = sfont.render('SCORE:' + str(score_value), True, (0, 0, 0))
    screen.blit(score, (x, y))

gfont = pygame.font.SysFont('freesansbold.ttf', 128)
def gameXY(x, y):
    gameO = gfont.render('GAME OVER', True, (0, 0, 0))
    screen.blit(gameO, (x, y))

# ---------------- UI Buttons ----------------
button_up   = pygame.Rect(250, 500, 80, 60)
button_down = pygame.Rect(350, 500, 80, 60)
button_fire = pygame.Rect(600, 500, 80, 80)
button_start= pygame.Rect(350, 500, 200, 80)
font_btn = pygame.font.SysFont('freesansbold.ttf', 25)
font_start= pygame.font.SysFont('freesansbold.ttf', 32)

def draw_buttons():
    pygame.draw.rect(screen, (200, 200, 20), button_up)
    pygame.draw.rect(screen, (200, 200, 20), button_down)
    pygame.draw.rect(screen, (255, 0, 0), button_fire)
    screen.blit(font_btn.render('UP', True, (0, 0, 0)), (260, 520))
    screen.blit(font_btn.render('DOWN', True, (0, 0, 0)), (355, 520))
    screen.blit(font_btn.render('FIRE', True, (255, 255, 255)), (615, 520))

def draw_start_button():
    pygame.draw.rect(screen, (10, 180, 10), button_start, border_radius=15)
    text = font_start.render("START", True, (0, 0, 0))
    screen.blit(text, (button_start.x + 50, button_start.y + 30))

# ---------------- Game State ----------------
theta = 0
x2, y2 = 158, 540
jet_x, jet_y = 800, 10
diploma_x, diploma_y = 800, 100
dip_drop_range = 700
milk_drop = False

g = 9.8
v = 100
x_bu, y_bu = 158, 540
y_buf = 540
x_buf = 0
theta_bu = 0
bullet_fire = False
bullet_run = False
hit_diploma = False

explosion_show = False
k = 0
gmOver = False
passing = 0
score_value = 0
gameStart = False
running = True
passing_condition = True

# ---------------- Async Main Loop ----------------
async def main():
    global theta, x2, y2, jet_x, jet_y, diploma_x, diploma_y, dip_drop_range, milk_drop
    global x_bu, y_bu, y_buf, x_buf, theta_bu, bullet_fire, bullet_run, hit_diploma
    global explosion_show, k, gmOver, passing, score_value, gameStart, running, passing_condition
    global exp_sound, gun_sound, siren_sound

    while running:
        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    gameStart = True
                if event.key == pygame.K_UP:
                    theta = min(90, theta + 5)
                if event.key == pygame.K_DOWN:
                    theta = max(0, theta - 5)
                if event.key == pygame.K_SPACE and not bullet_fire:
                    if gun_sound: gun_sound.play()
                    bullet_fire = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if button_down.collidepoint(x, y):
                    theta = max(0, theta - 5)
                if button_up.collidepoint(x, y):
                    theta = min(90, theta + 5)
                if button_start.collidepoint(x, y):
                    gameStart = True
                if button_fire.collidepoint(x, y) and not bullet_fire:
                    if gun_sound: gun_sound.play()
                    bullet_fire = True

        # ---- Draw ----
        screen.fill((255, 255, 255))
        screen.blit(background, (0, 0))

        if not gameStart:
            screen.blit(cover, (0, 0))
            draw_start_button()
        else:
            if not gmOver:
                # Tank calc
                x2 = 68 + 90 * math.cos(math.radians(theta))
                y2 = 540 - 90 * math.sin(math.radians(theta))

                if bullet_fire and not bullet_run:
                    x_bu, y_bu = x2, y2
                    theta_bu = theta
                    bullet_run = True

                pygame.draw.line(screen, (0, 0, 0), (0, 595), (900, 595), 7)
                tank_pipe(68, 540, x2, y2)
                tankF(10, 520)

                # Bullet hit check
                if (x_bu + x_buf >= diploma_x + 13 and
                    x_bu + x_buf <= diploma_x + 54 and
                    y_buf >= diploma_y and
                    y_buf <= diploma_y + 70 and
                    not hit_diploma and not explosion_show):
                    xe = x_bu + x_buf
                    ye = y_buf
                    if exp_sound: exp_sound.play()
                    explosion_show = True
                    hit_diploma = True
                    bullet_fire = False
                    bullet_run = False
                    x_buf = 0
                    score_value += 10
                    passing_condition = False

                # Jet movement
                jet_x -= 1.5 #same as diploma_x
                if jet_x <= -200:
                    jet_x = 800
                    jet_y = 100 + random.randint(0, 100)
                    diploma_x = jet_x

                # Diploma drop
                diploma_x -= 1.5 #same as jet_x
                if (dip_drop_range - 6) <= jet_x <= dip_drop_range and not milk_drop:
                    milk_drop = True
                    if siren_sound:
                        siren_sound.play()
                        siren_sound.set_volume(0.5)

                if milk_drop:
                    diploma_y += 2
                    if not explosion_show:
                        diploma(diploma_x + 90, diploma_y + 10)

                jet(jet_x, jet_y)

                if diploma_y >= 680 and passing_condition:
                    passing += 1
                    passing_condition = False

                if diploma_y >= 680 and jet_x == 800:
                    milk_drop = False
                    if siren_sound: siren_sound.stop()
                    diploma_y = jet_y
                    dip_drop_range = random.randint(500, 700)
                    passing_condition = True

                # Bullet movement
                if bullet_fire and bullet_run and not hit_diploma and not explosion_show:
                    x_buf += 4 #change
                    rad = math.radians(theta_bu)
                    y_buf = y_bu - x_buf * math.tan(rad) + (g * x_buf ** 2) / (2 * v ** 2 * (math.cos(rad) ** 2))
                    bullet(x_bu + x_buf, y_buf)
                    if (x_bu + x_buf >= 908) or (y_buf >= 600) or (y_buf <= -10):
                        bullet_fire = False
                        bullet_run = False
                        x_buf = 0

                # Left-side decorations
                if passing == 0:
                    diploma(0, 300); diploma(0, 364); diploma(0, 428)
                elif passing == 1:
                    diploma(0, 364); diploma(0, 428)
                elif passing == 2:
                    diploma(0, 428)

                # Explosion
                if explosion_show:
                    k += 5
                    if k >= 1050:
                        explosion_show = False
                        k = 0
                        hit_diploma = False
                    explosionXY(xe + 100, ye + 20, k)

                # Score & Buttons
                scoreXY(10, 10, score_value)
                draw_buttons()

                if passing == 3:
                    gmOver = True

            if gmOver:
                gameXY(150, 200)

        # ---- Present ----
        pygame.display.flip()

        # Limit FPS but yield control to browser
        clock.tick(60)
        # pygbag-এর জন্য critical: প্রতি ফ্রেমে yield
        await asyncio.sleep(0)

    pygame.quit()

# ---------------- Entry ----------------
# This is the program entry point
asyncio.run(main())