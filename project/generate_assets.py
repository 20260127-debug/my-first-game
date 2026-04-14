"""
에셋 생성 스크립트
pygame으로 픽셀아트 이미지를 생성하고, wave 모듈로 효과음을 합성합니다.
실행하면 assets/ 폴더에 모든 PNG + WAV 파일이 생성됩니다.

사용법: python generate_assets.py
"""

import os
import sys
import math
import struct
import wave
import random

# pygame headless 모드 (화면 없이 Surface만 사용)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
# dummy display for convert_alpha
pygame.display.set_mode((1, 1))

# ── 경로 설정 ────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "assets", "images")
SND_DIR   = os.path.join(BASE_DIR, "assets", "sounds")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(SND_DIR, exist_ok=True)

CELL = 28  # 셀 크기


# =====================================================================
# 이미지 생성 함수들
# =====================================================================

def make_surface(size=CELL):
    """투명 배경 서피스 생성"""
    return pygame.Surface((size, size), pygame.SRCALPHA)


def draw_apple_base(surf, color, cx=None, cy=None, r=None):
    """사과 기본 형태: 원 + 하이라이트 + 줄기"""
    if cx is None: cx = surf.get_width() // 2
    if cy is None: cy = surf.get_height() // 2 + 1
    if r is None:  r = surf.get_width() // 2 - 3

    # 본체
    pygame.draw.circle(surf, color, (cx, cy), r)
    # 하이라이트
    hl_color = (min(255, color[0]+80), min(255, color[1]+80), min(255, color[2]+80), 140)
    hl_surf = pygame.Surface((r, r//2), pygame.SRCALPHA)
    pygame.draw.ellipse(hl_surf, hl_color, (0, 0, r, r//2))
    surf.blit(hl_surf, (cx - r//2, cy - r + 2))
    # 줄기
    pygame.draw.line(surf, (90, 60, 30), (cx, cy - r), (cx + 1, cy - r - 4), 2)
    # 잎
    leaf_pts = [(cx + 2, cy - r - 2), (cx + 6, cy - r - 5), (cx + 4, cy - r)]
    pygame.draw.polygon(surf, (50, 180, 50), leaf_pts)


def gen_apple_green():
    surf = make_surface()
    draw_apple_base(surf, (50, 200, 50))
    return surf


def gen_apple_red():
    surf = make_surface()
    draw_apple_base(surf, (225, 60, 60))
    # 속도 표시: 작은 번개 마크
    cx, cy = CELL // 2, CELL // 2 + 1
    pts = [(cx + 2, cy - 4), (cx - 1, cy + 1), (cx + 2, cy - 1), (cx - 1, cy + 5)]
    pygame.draw.lines(surf, (255, 255, 100), False, pts, 2)
    return surf


def gen_apple_blue():
    surf = make_surface()
    draw_apple_base(surf, (60, 110, 225))
    # 얼음 결정 마크
    cx, cy = CELL // 2, CELL // 2 + 1
    for angle in [0, 60, 120]:
        rad = math.radians(angle)
        dx = int(3 * math.cos(rad))
        dy = int(3 * math.sin(rad))
        pygame.draw.line(surf, (200, 230, 255), (cx - dx, cy - dy), (cx + dx, cy + dy), 1)
    return surf


def gen_apple_gold():
    surf = make_surface()
    draw_apple_base(surf, (255, 210, 0))
    # 절단선 마크
    cx, cy = CELL // 2, CELL // 2 + 1
    pygame.draw.line(surf, (180, 130, 0), (cx - 4, cy + 2), (cx + 4, cy + 2), 2)
    # 반짝임
    for dx, dy in [(-3, -3), (4, -2), (3, 4)]:
        pygame.draw.circle(surf, (255, 255, 200, 180), (cx + dx, cy + dy), 1)
    return surf


def gen_apple_purple():
    surf = make_surface()
    draw_apple_base(surf, (175, 50, 225))
    # 유령 효과: 반투명 외곽
    cx, cy = CELL // 2, CELL // 2 + 1
    ghost_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.circle(ghost_surf, (200, 100, 255, 60), (cx, cy), CELL // 2 - 1)
    surf.blit(ghost_surf, (0, 0))
    return surf


def gen_apple_skull():
    surf = make_surface()
    draw_apple_base(surf, (200, 200, 200))
    # 해골 얼굴
    cx, cy = CELL // 2, CELL // 2 + 1
    pygame.draw.circle(surf, (60, 60, 60), (cx - 3, cy - 1), 2)
    pygame.draw.circle(surf, (60, 60, 60), (cx + 3, cy - 1), 2)
    pygame.draw.line(surf, (60, 60, 60), (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
    return surf


def gen_snake_head():
    """뱀 머리 (오른쪽 방향 기본)"""
    surf = make_surface()
    cx, cy = CELL // 2, CELL // 2

    # 머리 본체 (둥근 사각형)
    body_rect = pygame.Rect(2, 2, CELL - 4, CELL - 4)
    pygame.draw.rect(surf, (100, 255, 120), body_rect, border_radius=8)

    # 하이라이트
    hl_surf = pygame.Surface((CELL - 8, (CELL - 4) // 2), pygame.SRCALPHA)
    pygame.draw.rect(hl_surf, (160, 255, 180, 70), (0, 0, CELL - 8, (CELL - 4) // 2),
                     border_radius=5)
    surf.blit(hl_surf, (4, 3))

    # 눈 (오른쪽 방향)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 5, cy - 5), 4)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 5, cy + 5), 4)
    pygame.draw.circle(surf, (15, 15, 15), (cx + 6, cy - 5), 2)
    pygame.draw.circle(surf, (15, 15, 15), (cx + 6, cy + 5), 2)

    return surf


def gen_obstacle():
    """장애물 블록"""
    surf = make_surface()
    r = pygame.Rect(1, 1, CELL - 2, CELL - 2)

    # 갈색 블록
    pygame.draw.rect(surf, (95, 72, 52), r, border_radius=4)
    pygame.draw.rect(surf, (55, 42, 28), r, 2, border_radius=4)

    # X 마크
    mx, my = CELL // 2, CELL // 2
    s = 5
    pygame.draw.line(surf, (70, 50, 30), (mx - s, my - s), (mx + s, my + s), 2)
    pygame.draw.line(surf, (70, 50, 30), (mx + s, my - s), (mx - s, my + s), 2)

    return surf


# =====================================================================
# 사운드 생성 함수들 (wave + struct)
# =====================================================================

SAMPLE_RATE = 22050


def save_wav(filename, samples):
    """16bit mono WAV 저장"""
    path = os.path.join(SND_DIR, filename)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16bit
        w.setframerate(SAMPLE_RATE)
        data = b''
        for s in samples:
            clamped = max(-32767, min(32767, int(s)))
            data += struct.pack('<h', clamped)
        w.writeframes(data)
    print(f"  [SND] {filename} ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.2f}s)")


def sine_wave(freq, duration, volume=0.8, fade_out=True):
    """사인파 생성"""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        val = math.sin(2 * math.pi * freq * t) * 32767 * volume
        if fade_out:
            env = 1.0 - (i / n)
            val *= env
        samples.append(val)
    return samples


def noise_burst(duration, volume=0.3, fade_out=True):
    """노이즈 버스트"""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        val = random.uniform(-1, 1) * 32767 * volume
        if fade_out:
            env = 1.0 - (i / n)
            val *= env
        samples.append(val)
    return samples


def freq_sweep(f_start, f_end, duration, volume=0.7, fade_out=True):
    """주파수 스윕"""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = f_start + (f_end - f_start) * progress
        val = math.sin(2 * math.pi * freq * t) * 32767 * volume
        if fade_out:
            env = 1.0 - progress
            val *= env
        samples.append(val)
    return samples


def mix_samples(*sample_lists):
    """여러 샘플 리스트 합성"""
    max_len = max(len(s) for s in sample_lists)
    result = [0.0] * max_len
    for sl in sample_lists:
        for i, v in enumerate(sl):
            result[i] += v
    # 클리핑 방지를 위한 정규화
    peak = max(abs(v) for v in result) if result else 1
    if peak > 32767:
        scale = 32767 / peak
        result = [v * scale for v in result]
    return result


def gen_eat_normal():
    """일반 사과 먹기: 짧은 pop"""
    s1 = sine_wave(880, 0.05, volume=0.6, fade_out=True)
    s2 = sine_wave(1200, 0.08, volume=0.4, fade_out=True)
    return mix_samples(s1, s2)


def gen_eat_special():
    """특수 사과 먹기: 반짝 차임"""
    s1 = sine_wave(660, 0.1, volume=0.5)
    s2 = sine_wave(880, 0.1, volume=0.5)
    s3 = sine_wave(1100, 0.15, volume=0.4)
    # 순차적으로 배치
    gap = int(SAMPLE_RATE * 0.08)
    result = s1 + [0] * gap + s2 + [0] * gap + s3
    return result


def gen_eat_skull():
    """해골 사과: 불길한 하강음"""
    return freq_sweep(400, 100, 0.4, volume=0.6)


def gen_eat_gold():
    """황금 사과: 금속성 절단음"""
    s1 = sine_wave(1500, 0.05, volume=0.8, fade_out=False)
    s2 = noise_burst(0.15, volume=0.5)
    s3 = sine_wave(300, 0.2, volume=0.4)
    return mix_samples(s1 + s2, s3)


def gen_speed_up():
    """속도 증가: 상승 whoosh"""
    return freq_sweep(200, 1200, 0.2, volume=0.5)


def gen_speed_down():
    """속도 감소: 하강 whoosh"""
    return freq_sweep(1000, 200, 0.25, volume=0.5)


def gen_wall_pass():
    """벽 통과: 영묘한 두 음"""
    s1 = sine_wave(440, 0.4, volume=0.3)
    s2 = sine_wave(445, 0.4, volume=0.3)  # 약간 디튜닝
    s3 = sine_wave(660, 0.3, volume=0.2)
    return mix_samples(s1, s2, s3)


def gen_reverse():
    """방향 반전: 빠른 주파수 진동"""
    n = int(SAMPLE_RATE * 0.3)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = 400 + 600 * abs(math.sin(progress * math.pi * 6))
        val = math.sin(2 * math.pi * freq * t) * 32767 * 0.5
        env = 1.0 - progress
        samples.append(val * env)
    return samples


def gen_game_over():
    """게임오버: 충돌 + 하강"""
    s1 = noise_burst(0.15, volume=0.7, fade_out=False)
    s2 = freq_sweep(500, 80, 0.6, volume=0.6)
    s3 = sine_wave(120, 0.5, volume=0.3)
    return mix_samples(s1 + [0] * int(SAMPLE_RATE * 0.05) + list(s2), s3)


def gen_clear():
    """클리어: C-E-G 아르페지오"""
    gap = int(SAMPLE_RATE * 0.05)
    c = sine_wave(523, 0.25, volume=0.5)  # C5
    e = sine_wave(659, 0.25, volume=0.5)  # E5
    g = sine_wave(784, 0.35, volume=0.5)  # G5
    high_c = sine_wave(1047, 0.5, volume=0.4)  # C6
    return c + [0] * gap + e + [0] * gap + g + [0] * gap + high_c


# =====================================================================
# 메인 실행
# =====================================================================

def main():
    print("=== 에셋 생성 시작 ===\n")

    # ── 이미지 생성 ──
    print("[이미지 생성]")
    images = {
        "apple_green.png":  gen_apple_green(),
        "apple_red.png":    gen_apple_red(),
        "apple_blue.png":   gen_apple_blue(),
        "apple_gold.png":   gen_apple_gold(),
        "apple_purple.png": gen_apple_purple(),
        "apple_skull.png":  gen_apple_skull(),
        "snake_head.png":   gen_snake_head(),
        "obstacle.png":     gen_obstacle(),
    }
    for fname, surf in images.items():
        path = os.path.join(IMG_DIR, fname)
        pygame.image.save(surf, path)
        print(f"  [IMG] {fname} ({surf.get_width()}x{surf.get_height()})")

    # ── 사운드 생성 ──
    print("\n[사운드 생성]")
    sounds = {
        "eat_normal.wav":  gen_eat_normal(),
        "eat_special.wav": gen_eat_special(),
        "eat_skull.wav":   gen_eat_skull(),
        "eat_gold.wav":    gen_eat_gold(),
        "speed_up.wav":    gen_speed_up(),
        "speed_down.wav":  gen_speed_down(),
        "wall_pass.wav":   gen_wall_pass(),
        "reverse.wav":     gen_reverse(),
        "game_over.wav":   gen_game_over(),
        "clear.wav":       gen_clear(),
    }
    for fname, samples in sounds.items():
        save_wav(fname, samples)

    print(f"\n=== 완료! ===")
    print(f"이미지: {IMG_DIR} ({len(images)}개)")
    print(f"사운드: {SND_DIR} ({len(sounds)}개)")


if __name__ == "__main__":
    main()
    pygame.quit()
