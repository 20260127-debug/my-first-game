import pygame
import sys
import math

# 초기화
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Collision Lab")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 150)
BG_COLOR = WHITE

# 스프라이트 직접 생성
PLAYER_SIZE = (50, 70)
ENEMY_SIZE = (60, 60)


def make_player_sprite(w, h):
    """간단한 캐릭터 스프라이트 생성"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # 몸통 (파란 사각형)
    pygame.draw.rect(surf, (50, 120, 220), (10, 25, 30, 35))
    # 머리 (원)
    pygame.draw.circle(surf, (255, 200, 150), (w // 2, 15), 14)
    # 눈
    pygame.draw.circle(surf, (0, 0, 0), (w // 2 - 5, 13), 2)
    pygame.draw.circle(surf, (0, 0, 0), (w // 2 + 5, 13), 2)
    # 다리
    pygame.draw.rect(surf, (40, 40, 40), (14, 60, 10, 10))
    pygame.draw.rect(surf, (40, 40, 40), (26, 60, 10, 10))
    return surf


def make_enemy_sprite(w, h):
    """간단한 적 스프라이트 생성 (돌/바위 느낌)"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # 바위 몸체
    points = [
        (w // 2, 2),
        (w - 5, h // 4),
        (w - 2, h // 2),
        (w - 8, h - 5),
        (w // 2, h - 2),
        (5, h - 8),
        (2, h // 3),
        (8, 8),
    ]
    pygame.draw.polygon(surf, (140, 140, 140), points)
    pygame.draw.polygon(surf, (100, 100, 100), points, 3)
    # 눈 (화난 표정)
    pygame.draw.circle(surf, (255, 50, 50), (w // 2 - 10, h // 2 - 5), 5)
    pygame.draw.circle(surf, (255, 50, 50), (w // 2 + 10, h // 2 - 5), 5)
    pygame.draw.circle(surf, (0, 0, 0), (w // 2 - 10, h // 2 - 5), 2)
    pygame.draw.circle(surf, (0, 0, 0), (w // 2 + 10, h // 2 - 5), 2)
    return surf


player_img = make_player_sprite(*PLAYER_SIZE)
enemy_img_original = make_enemy_sprite(*ENEMY_SIZE)

# 플레이어 (키보드로 이동)
player_x, player_y = 100.0, 300.0
player_speed = 5

# 적 (화면 중앙 고정) - 중심 좌표 기준
enemy_cx = SCREEN_WIDTH // 2
enemy_cy = SCREEN_HEIGHT // 2

# 회전 관련 변수
enemy_angle = 0.0
enemy_rot_speed = 1.0
enemy_rot_boost = 5.0


def get_obb_corners(cx, cy, w, h, angle_deg):
    """중심 좌표, 크기, 각도로부터 OBB의 4개 꼭짓점을 계산"""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    hw, hh = w / 2, h / 2
    corners_local = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    corners = []
    for lx, ly in corners_local:
        rx = cx + lx * cos_a - ly * sin_a
        ry = cy + lx * sin_a + ly * cos_a
        corners.append((rx, ry))
    return corners


def get_axes(corners):
    """OBB 꼭짓점에서 분리축(법선 벡터) 2개를 추출"""
    axes = []
    for i in range(len(corners)):
        p1 = corners[i]
        p2 = corners[(i + 1) % len(corners)]
        edge = (p2[0] - p1[0], p2[1] - p1[1])
        # 수직 벡터 (법선)
        normal = (-edge[1], edge[0])
        # 정규화
        length = math.sqrt(normal[0] ** 2 + normal[1] ** 2)
        if length > 0:
            normal = (normal[0] / length, normal[1] / length)
        axes.append(normal)
    return axes


def project_polygon(axis, corners):
    """꼭짓점들을 축에 투영하여 (min, max) 반환"""
    dots = [c[0] * axis[0] + c[1] * axis[1] for c in corners]
    return min(dots), max(dots)


def sat_collision(corners_a, corners_b):
    """SAT(분리축 정리)로 두 OBB의 충돌 여부 판정"""
    for axis in get_axes(corners_a) + get_axes(corners_b):
        min_a, max_a = project_polygon(axis, corners_a)
        min_b, max_b = project_polygon(axis, corners_b)
        # 투영 구간이 겹치지 않으면 → 분리축 발견 → 충돌 아님
        if max_a < min_b or max_b < min_a:
            return False
    return True


# 메인 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
    if keys[pygame.K_UP]:
        player_y -= player_speed
    if keys[pygame.K_DOWN]:
        player_y += player_speed

    # Z키로 회전 속도 부스트
    current_rot_speed = enemy_rot_speed
    if keys[pygame.K_z]:
        current_rot_speed += enemy_rot_boost

    # 적 회전 업데이트
    enemy_angle = (enemy_angle + current_rot_speed) % 360

    # 회전된 적 이미지
    rotated_enemy = pygame.transform.rotate(enemy_img_original, enemy_angle)
    rotated_rect = rotated_enemy.get_rect(center=(enemy_cx, enemy_cy))

    # AABB 충돌 판정
    player_rect = pygame.Rect(player_x, player_y, PLAYER_SIZE[0], PLAYER_SIZE[1])
    enemy_rect = rotated_rect
    aabb_colliding = player_rect.colliderect(enemy_rect)

    # 원형 충돌 판정
    player_radius = min(PLAYER_SIZE) // 2
    enemy_radius = ENEMY_SIZE[0] // 2
    player_cx = player_x + PLAYER_SIZE[0] // 2
    player_cy = player_y + PLAYER_SIZE[1] // 2
    dist = math.sqrt((player_cx - enemy_cx) ** 2 + (player_cy - enemy_cy) ** 2)
    circle_colliding = dist <= player_radius + enemy_radius

    # OBB 충돌 판정 (SAT)
    player_obb = get_obb_corners(
        player_x + PLAYER_SIZE[0] / 2, player_y + PLAYER_SIZE[1] / 2,
        PLAYER_SIZE[0], PLAYER_SIZE[1], 0)
    enemy_obb = get_obb_corners(
        enemy_cx, enemy_cy,
        ENEMY_SIZE[0], ENEMY_SIZE[1], -enemy_angle)
    obb_colliding = sat_collision(player_obb, enemy_obb)

    # 배경색 - 어떤 충돌이든 발생하면 빨간색
    if obb_colliding or aabb_colliding or circle_colliding:
        bg = (255, 60, 60)
    else:
        bg = BG_COLOR

    # 그리기
    screen.fill(bg)
    screen.blit(player_img, (player_x, player_y))
    screen.blit(rotated_enemy, rotated_rect)

    # AABB (빨간 사각형)
    pygame.draw.rect(screen, RED, player_rect, 2)
    pygame.draw.rect(screen, RED, enemy_rect, 2)

    # OBB (초록 사각형) - 플레이어와 적 둘 다 표시
    pygame.draw.polygon(screen, GREEN, player_obb, 2)
    pygame.draw.polygon(screen, GREEN, enemy_obb, 2)

    # 원형 (파란 원)
    pygame.draw.circle(screen, BLUE, (int(player_cx), int(player_cy)), player_radius, 2)
    pygame.draw.circle(screen, BLUE, (int(enemy_cx), int(enemy_cy)), enemy_radius, 2)

    # 안내 텍스트
    font = pygame.font.SysFont(None, 28)
    text = font.render("Arrow keys | Z=Spin | AABB=Red | OBB=Green | Circle=Blue", True, (0, 0, 0))
    screen.blit(text, (10, 10))

    # 세 가지 충돌 상태를 항상 동시에 표시
    circle_status = "HIT" if circle_colliding else "---"
    aabb_status = "HIT" if aabb_colliding else "---"
    obb_status = "HIT" if obb_colliding else "---"

    circle_color = BLUE if circle_colliding else (150, 150, 150)
    aabb_color = RED if aabb_colliding else (150, 150, 150)
    obb_color = GREEN if obb_colliding else (150, 150, 150)

    screen.blit(font.render(f"Circle: {circle_status}", True, circle_color), (10, 40))
    screen.blit(font.render(f"AABB:   {aabb_status}", True, aabb_color), (10, 65))
    screen.blit(font.render(f"OBB:    {obb_status}", True, obb_color), (10, 90))

    angle_text = font.render(f"Angle: {enemy_angle:.0f}  Speed: {current_rot_speed:.0f}", True, (0, 0, 0))
    screen.blit(angle_text, (10, SCREEN_HEIGHT - 35))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
