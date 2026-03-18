import pygame
import sys
import random

# 1. 초기화
pygame.init()
SW, SH = 800, 600
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Super Thief: Visual FX Edition")

# 색상 정의 (NAVY 추가 완료!)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
GOLD = (255, 215, 0)
RED = (255, 50, 50)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
PURPLE = (150, 0, 255)
NAVY = (0, 0, 128)
ORANGE = (255, 165, 0)

# 2. 게임 변수 설정
p_x, p_y = 400, 300
p_radius = 15
p_speed = 6
fever_mode = False
fever_timer = 0

g_x, g_y = random.randint(50, 750), random.randint(50, 550)
score = 0
enemies = []
particles = []
shake_timer = 0

def spawn_police(px, py):
    while True:
        ex, ey = random.randint(50, 750), random.randint(50, 550)
        # 플레이어와 너무 가깝지 않게 생성
        if ((px - ex)**2 + (py - ey)**2)**0.5 > 300:
            return {'x': ex, 'y': ey, 'dx': random.choice([-4, 4]), 'dy': random.choice([-4, 4]), 'radius': 20}

# 첫 번째 경찰 생성
enemies.append(spawn_police(p_x, p_y))

def create_particles(x, y):
    for _ in range(15):
        particles.append([[x, y], [random.uniform(-5, 5), random.uniform(-5, 5)], random.randint(5, 8)])

clock = pygame.time.Clock()
start_ticks = pygame.time.get_ticks()
game_state = "PLAYING"
font = pygame.font.SysFont("Arial", 25, bold=True)

# 메인 루프
while True:
    # 화면 흔들림 효과 계산
    offset_x, offset_y = 0, 0
    if shake_timer > 0:
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        shake_timer -= 1

    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_state == "OVER" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # 초기화
                p_x, p_y, score, enemies, particles = 400, 300, 0, [spawn_police(400, 300)], []
                start_ticks = pygame.time.get_ticks()
                game_state = "PLAYING"

    if game_state == "PLAYING":
        # --- 시간 계산 (에러 해결 포인트!) ---
        seconds_passed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, 60 - seconds_passed)
        
        if time_left <= 0:
            game_state = "OVER"

        # 피버 타임 로직
        if fever_mode:
            fever_timer -= 1
            if fever_timer <= 0:
                fever_mode = False
                p_speed = 6

        # 플레이어 이동
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:  p_x -= p_speed
        if keys[pygame.K_RIGHT]: p_x += p_speed
        if keys[pygame.K_UP]:    p_y -= p_speed
        if keys[pygame.K_DOWN]:  p_y += p_speed
        p_x = max(p_radius, min(SW - p_radius, p_x))
        p_y = max(p_radius, min(SH - p_radius, p_y))

        # 경찰 이동 및 충돌
        for e in enemies:
            e['x'] += e['dx']
            e['y'] += e['dy']
            if e['x'] < e['radius'] or e['x'] > SW - e['radius']: e['dx'] *= -1
            if e['y'] < e['radius'] or e['y'] > SH - e['radius']: e['dy'] *= -1

            dist = ((p_x - e['x'])**2 + (p_y - e['y'])**2)**0.5
            if dist < (p_radius + e['radius']) and not fever_mode:
                game_state = "OVER"

        # 금괴 획득
        dist_g = ((p_x - g_x)**2 + (p_y - g_y)**2)**0.5
        if dist_g < 35:
            score += 1
            shake_timer = 10
            create_particles(g_x, g_y)
            g_x, g_y = random.randint(50, 750), random.randint(50, 550)
            if score % 5 == 0:
                enemies.append(spawn_police(p_x, p_y))
            if score % 10 == 0:
                fever_mode = True
                fever_timer = 180 # 3초
                p_speed = 10

        # 입자 업데이트
        for p in particles[:]:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 0.3
            if p[2] <= 0: particles.remove(p)

        # 그리기
        for p in particles:
            pygame.draw.circle(screen, GOLD, (int(p[0][0] + offset_x), int(p[0][1] + offset_y)), int(p[2]))
        
        pygame.draw.rect(screen, GOLD, (g_x-15+offset_x, g_y-10+offset_y, 30, 20))
        pygame.draw.rect(screen, ORANGE, (g_x-15+offset_x, g_y-10+offset_y, 30, 20), 2)
        
        for e in enemies:
            pygame.draw.circle(screen, NAVY, (int(e['x'] + offset_x), int(e['y'] + offset_y)), e['radius'])
            # 경찰 경광등
            l_color = RED if (pygame.time.get_ticks() // 150) % 2 == 0 else BLUE
            pygame.draw.circle(screen, l_color, (int(e['x'] + offset_x), int(e['y'] - 10 + offset_y)), 7)

        p_color = PURPLE if fever_mode and (fever_timer // 10) % 2 else GRAY
        pygame.draw.circle(screen, p_color, (int(p_x + offset_x), int(p_y + offset_y)), p_radius)

        # UI 표시 (seconds_passed 변수가 이제 정의된 상태!)
        ui_txt = font.render(f"Gold: {score}  Time: {int(time_left)}s", True, GOLD if fever_mode else WHITE)
        screen.blit(ui_txt, (20, 20))

    else:
        # 게임 오버 화면
        msg = font.render("BUSTED! Press 'R' to Restart", True, RED)
        screen.blit(msg, (SW//2-150, SH//2))

    pygame.display.flip()
    clock.tick(60)