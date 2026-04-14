"""
약먹은 스네이크 (Crazy Snake)
창의프로그래밍 업무설계 중간과제
작성자: 김도현

[스토리]
  유리병 속에 갇힌 뱀 '스내피'.
  병 안에는 이상한 실험 알약들이 가득하다.
  몸을 키워 병을 가득 채우면... 유리병이 깨지고 탈출할 수 있다!

[클리어 조건]
  뱀 몸통 + 장애물로 맵 전체(160칸)를 채우면 클리어!

[보스 & 목숨]
  알약 10개 먹을 때마다 그리드에 독수리 보스가 출현. 보스 HP는 3.
  보스는 2초마다 랜덤 8방향 투사체를 발사한다.
  처치 방법:
    (A) 상/하/좌/우 4칸을 뱀 몸통/장애물/맵 경계로 모두 막으면 즉사.
    (B) 무기 알약으로 장착한 뱀 포탑이 총알로 HP를 깎아 0 만들면 처치.
  처치 시 +100점. 목숨 3개 — 투사체/보스 접촉 시 -1, 0되면 게임오버.

[조작법]
  방향키 또는 WASD : 뱀 이동 (연속 2번 꺾기 입력 버퍼 지원)
  마우스 커서      : 포탑 조준 (무기 알약 장착 시)
  ESC              : 메뉴로 이동

[특수 알약 종류 - 한 번에 1개만 등장]
  초록 알약  : 일반 성장 (+1칸)
  빨강 알약  : 속도 증가 (5초, +1 성장)
  파랑 알약  : 속도 감소 (5초, +1 성장)
  황금 알약  : 몸통 절반 절단 → 잘린 부위가 장애물로 변함 (+1 성장)
  무지개 알약: 방향 반전 + 사이키델릭 배경 (5초, +1 성장)
  보라 알약  : 벽 통과 능력 부여 (5초, +1 성장)
  무기 알약  : 머리 뒤부터 포탑 영구 장착 (최대 3개, #1→#2→#3 순).
               마우스 커서 방향으로 자동 발사 → 보스 HP 감소. (1/7 비율 등장)

"""

import pygame
import random
import sys
import math
import base64
import io
import os

pygame.init()
pygame.mixer.init()

# ── 에셋 로딩 유틸 ───────────────────────────────────────────────────
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
IMG_DIR   = os.path.join(ASSET_DIR, "images")
SND_DIR   = os.path.join(ASSET_DIR, "sounds")


def load_image(name, size=None):
    """이미지 로드 (없으면 None → 기존 방식 fallback)"""
    path = os.path.join(IMG_DIR, name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    return None


def load_sound(name):
    """사운드 로드 (없으면 None)"""
    path = os.path.join(SND_DIR, name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None


def play_sound(snd, volume=0.5):
    """안전하게 사운드 재생"""
    if snd:
        snd.set_volume(volume)
        snd.play()

# ── 화면 / 그리드 ─────────────────────────────────────────────────────
CELL_SIZE   = 32
GRID_WIDTH  = 16
GRID_HEIGHT = 10
TOTAL_CELLS = GRID_WIDTH * GRID_HEIGHT   # 160칸

HUD_HEIGHT    = 200
BENCH_HEIGHT  = 44                              # 하단 실험실 콘솔
WINDOW_WIDTH  = CELL_SIZE * GRID_WIDTH          # 448
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT + HUD_HEIGHT + BENCH_HEIGHT
FPS           = 60

# 플레이 영역 y 범위 (HUD 아래 ~ 벤치 위)
PLAY_BOTTOM   = HUD_HEIGHT + CELL_SIZE * GRID_HEIGHT

# ── 색상 ──────────────────────────────────────────────────────────────
BG           = (22, 28, 38)       # 실험실 어두운 배경
FLASK_INSIDE = (240, 245, 250)    # 플라스크 내부 (거의 흰색)
FLASK_FLOOR  = (235, 238, 242)    # 플라스크 바닥
GRID_COL     = (210, 215, 225)    # 밝은 배경 위 그리드 (연한 회색)
HUD_BG       = (18, 22, 35)
WHITE        = (255, 255, 255)

# 실험실 벽/콘솔 색상
LAB_WALL_A   = ( 38,  45,  55)  # 패널 베이스
LAB_WALL_B   = ( 28,  34,  44)  # 패널 사이 틈
LAB_PANEL_HL = ( 60,  72,  90)  # 리벳/하이라이트
LAB_HAZARD_Y = (240, 200,  30)  # 위험 스트라이프 노랑
LAB_HAZARD_K = ( 20,  20,  20)  # 위험 스트라이프 검정
LAB_METAL    = ( 90, 100, 115)  # 벤치 금속 상판
LAB_METAL_D  = ( 50,  58,  70)  # 벤치 금속 음영
LED_RED      = (230,  40,  50)
LED_GREEN    = ( 60, 220,  90)
LED_AMBER    = (240, 170,  40)

HEAD_COL      = (100, 255, 120)
BODY_DARK     = (18,  90,  18)
WALL_PASS_COL = (190, 80, 230)

RED           = (225,  60,  60)
BLUE          = ( 60, 110, 225)
GOLD          = (255, 210,   0)
PURPLE        = (175,  50, 225)
SKULL_COL     = (200, 200, 200)
GREEN_APPLE   = ( 50, 200,  50)

OBSTACLE      = ( 95,  72,  52)
OBSTACLE_B    = ( 55,  42,  28)
CRACK_COL     = (220, 220, 255)

# 플라스크 테두리 색상
FLASK_EDGE    = (160, 195, 220)   # 유리 테두리
FLASK_SHINE   = (210, 235, 255)   # 반사광
FLASK_NECK    = (180, 205, 230)   # 목 부분

# ── 사과 타입 ─────────────────────────────────────────────────────────
NORMAL  = "normal"
A_RED   = "red"
A_BLUE  = "blue"
A_GOLD  = "gold"
A_RAIN  = "rainbow"
A_PURP  = "purple"
A_SKULL = "skull"
A_WEAPON = "weapon"   # 무기 장착 알약

WEAPON_COL = (200,  60,  70)   # 무기 알약 대표 빨강
STEEL_COL  = (180, 185, 200)

APPLE_COLOR = {
    NORMAL : GREEN_APPLE,
    A_RED  : RED,
    A_BLUE : BLUE,
    A_GOLD : GOLD,
    A_PURP : PURPLE,
    A_SKULL: SKULL_COL,
    A_WEAPON: WEAPON_COL,
    A_RAIN : None,
}

APPLE_POOL = (
    [NORMAL]   * 33 +
    [A_RED]    * 14 +
    [A_BLUE]   * 12 +
    [A_GOLD]   * 12 +
    [A_RAIN]   *  8 +
    [A_PURP]   *  7 +
    [A_WEAPON] * 14      # ~1/7 비율로 등장
)

RAINBOW_CYCLE = [
    (255, 80,  80), (255,165,   0), (255,230,   0),
    ( 80,220,  80), ( 80,130, 255), (160, 60, 220),
]

# ── 방향 ──────────────────────────────────────────────────────────────
UP    = ( 0, -1); DOWN  = ( 0,  1)
LEFT  = (-1,  0); RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# ── 독수리 스프라이트 ─────────────────────────────────────────────────
# Base64 PNG 원본 (일부 환경에서 libpng 호환성 문제 있음)
SHEET_B64 = "iVBORw0KGgoAAAANSUhEUgAAAR8AAAAVCAYAAAB/u+qfAAAGZUlEQVR4nO1cPWgjRxh9ytk4jZLyamM1iRrZAgWOEHw+DjfBOoghhSGksYs0NjbxEQiGmECwIUJqrrC7gIuDKywnxR3GP9xxgRPIVuOkOAk3aVImrg5f2BT2t/52NLM7M7valbh9YJCs2W/efjPvfTM7soEUKa5Rzueccj7nDFrsFIOJ95ImkKI/UM7nnNWFAoqFLKI2iXI+5xQLWawuFCKPnWJwkZpPihQpEkFqPjEgrmofZT9RbJPSrVYKP4Q2n8P9PaeczznOm7+6fsr5nHO4v/dOTj4SHm1n4pewsJ97sCfkTVZFxfXanfmF3cMm03DQ6AIBm60Kbm4pvsZBFs3WB1YWCJ279rJ073N9zakvLHn6c52K1gqn7MxmKQ/e7udUCxbXhpctd/J3tWPcKg8CREIeurS+kRC5WK7j72QQ++PAj/PvPn+7n9P7o+QnIRcMmkguOcNDouKJTxQ+TSLrPYiHrGgeBDESHLwmQQKKk6004UlwyBwCuYejw8uNLHJutC/DXIoJEo4pjwsvG8KMQjU2/Joi7YOuC37eJrgG7/BhdIKvkzdYFFqsVjPzxC96+HsGdlUkAQGPvGd58/BVqS8vSSWwrDt63CJlIAPNEcgT1pbP64YbJDYMMyJSjaDzcFG2NR+TL4wPA2s5pRkc0336R64opGq0JDw6/QhNFMQxTaHTuh17bzMder4Bk4/7p1z8E6pqv5E15DumQotcqIQLA29cjnvelmWm8aHvbeK+/iatLmLYbvMp70ZH87mp/imoFTzem8XzloZvIpxvT7kCr7k2chIBdonk8GuCDRsc1Eh2O4jZLxS9qNFsXKOdzDhcNrXx2T46lovGbK7oQV4veuN7VCf3ebKzlMQB0rSptISuYJmPtYgsO0BsTUhUcIFjXB40O7pXGbvhuwdHlOBT0wEh3Ev1X/hK36o/x+8/HuLMyiRft277tVUYkA78ZMiAyAA6ZODl0DJIgOrofJz/Uz9oZmjjETzQgXY5iW3HFY8IriC+fjHbCvuFos2qwLTQE82IYfaHxE3UQR/EaLm5bPiqOxUJWyVFH12RALk9NAxoSH16qIIqQBq5YyKK2tIzFaqXrGnEyihXkRozqPmU3obyx64FRGaaJQUYlZk8MZkI0WOKg63DshemI2NxqdW3vCLomzreVNghTaEzGOqpCQ6CC7mc8phwpTlQmpMNRV9ecn8tRg5/7gekKiD9IpPcAsHz3E1SOXnVdI7bn16gQNrFi/4vVCm7VHwOAO9gqg+zlHpsPPOA9rQriGGaPbcpR9lCbJqPIEeielLarHl1+gLzQ6I41bw9EcyACyI1RLDYmHIkfH48w80DUumwFKJ6gqnTN24p8CSpuymNl1UpIvNnL820HAH76/pHbMSf33Y/fAACGR+cz4uDIYkc5UfnpDXED/A0yzqNNlUkGcQTiOYIV80f9m4gmjgel9Nomj0A0uZR99QHoNglbjgTeh/i1DVOushUPFYwnvz0EEKzr2c83lKunoOJjdNwIyAfq8nzbaew9w0Gjg7Wd08z63LhDiSnNTGN4dF56qqATOwqYGGQv+tdBv3Lsd4MUkVQeZYJWmUMYjuJ2iW9tdfKtMh5ZHF1d+23h/AxIedqlO3EokaWZaRw0Hnk+K81Mu214IuOelMOj85nL822Hloj1s3amWLhJJLWJk5OIfuVIY1U/6xZN5ehVXxgkRxJ5lBVTP1MIw5E/P+S5NzUevpUD1Aapo2vOice7Qkf5EDrwqF0HYqLWdk4zazunwOITz40kBRuDjBuDwLFfDZIjiTyqxKcyhCg4XsXOOUDnugDktB5AkymQCfmtmkx1zU926TtAm1stNFv2hw4DDx3z6xeDDNuml7g833boZ31u3AGA9blx52Vt1uGfJc0xijamKOdzDuUi6PAmSo78D4mD+qU2L2uzzvrceE//3lLMR/rfDVKEwiAYZBIgQesYT5KIy3h4f7qGnCJFCkv0e3WP23h4vyoDSnR/niJFinjAhZ/kX/Pzvv8HbYI+3KjHqskAAAAASUVORK5CYII="

# ── 독수리 스프라이트 설정 (데모 코드와 완전히 동일) ──
FRAME_W       = 41
FRAME_H       = 21       # 스프라이트 시트 실제 높이 — 20으로 잘라내면 하단 픽셀 누락
COLS          = 7
DISPLAY_SCALE = 4
FRAME_DELAY   = 150   # ms

# ── 알약 스프라이트 시트 (사용자 제공, 32×32 × 12프레임, 4열 3행) ──
PILL_SHEET_B64 = "iVBORw0KGgoAAAANSUhEUgAAAIAAAABgCAYAAADVenpJAAAACXBIWXMAAAsTAAALEwEAmpwYAAAHQ0lEQVR4nO2dW2gUVxjH/2d3Ltlsom0i7gYTHyRCG/Ig0kVLIS+hPlhQvFCffCj2wUKVPhRakGptbR6qpWArfZTWp0pLS6GQUBIKWqjRFopYL8GUrOKOu15izGVmdy999H+X1fz5nbrLbmdnZ3ZnvhkOzvfDsrs75x8/5z5x51ZBFf1zM7O7uRmtrK5qbmxEIBCBJEn788Ue3p2Z+g+f7LYJhmNclMwE4AvSKQXSSzyk/WhJIyovw4fGPvffmpxmIGBUeHQR88cUkRAR3H5YA2fzPxiCk37y8HAMDs7Cys/H29jaSyST29/eRSCTw4MED/pOwH1QkgGEaUWaAYRjWRfMCMAxDGhaAYQjDAjAMYVgAhiEMC8AwhGEBGIYwLADDEIYFYBjCsABEx8DMKUYhmFYAIYhDAvAMIRhARiGMCwAwxCmIo8E9+HBN0tLS5/3wsgE1eMB2+EvBH4DcPSrVUlZ9AoAAAAASUVORK5CYII="
PILL_FRAME_W, PILL_FRAME_H = 32, 32
PILL_SHEET_COLS = 4
PILL_SHEET_ROWS = 3
PILL_FRAMES_TOTAL = PILL_SHEET_COLS * PILL_SHEET_ROWS   # 12

# 프레임 인덱스 → 알약 타입 매핑 (사용자가 나중에 조정 가능)
# 기본: 시트의 앞 7프레임을 7종 알약에 순서대로 배치
_PILL_FRAME_MAP = {
    "normal":  0,
    "red":     1,
    "blue":    2,
    "gold":    3,
    "rainbow": 4,
    "purple":  5,
    "weapon":  6,
}

EAGLE_DISP_W  = FRAME_W * DISPLAY_SCALE   # 164
EAGLE_DISP_H  = FRAME_H * DISPLAY_SCALE   # 80


def _repair_png_deflate(png_bytes):
    """IDAT 청크를 재압축해 libpng의 'invalid distance too far back' 이슈 우회.
    최신 libpng은 구버전 zlib의 win-size 관련 허용치를 더 엄격히 검사하므로
    현재 Python zlib으로 fresh re-compress 하면 호환됨. 순수 표준 라이브러리."""
    import zlib, struct
    if png_bytes[:8] != b'\x89PNG\r\n\x1a\n':
        return png_bytes

    head_chunks = []   # IDAT 이전 청크들 (IHDR 등)
    tail_chunks = []   # IDAT 이후 청크들 (IEND 등)
    idat_data = b''
    idat_seen = False

    pos = 8
    while pos < len(png_bytes):
        length = struct.unpack('>I', png_bytes[pos:pos+4])[0]
        ctype = png_bytes[pos+4:pos+8]
        cdata = png_bytes[pos+8:pos+8+length]
        pos += 12 + length

        if ctype == b'IDAT':
            idat_data += cdata
            idat_seen = True
        elif not idat_seen:
            head_chunks.append((ctype, cdata))
        else:
            tail_chunks.append((ctype, cdata))

    if not idat_data:
        return png_bytes

    raw = zlib.decompress(idat_data)
    new_idat = zlib.compress(raw, 9)

    def encode_chunk(ctype, cdata):
        crc = zlib.crc32(ctype + cdata) & 0xFFFFFFFF
        return (struct.pack('>I', len(cdata)) + ctype + cdata +
                struct.pack('>I', crc))

    out = b'\x89PNG\r\n\x1a\n'
    for c in head_chunks:
        out += encode_chunk(*c)
    out += encode_chunk(b'IDAT', new_idat)
    for c in tail_chunks:
        out += encode_chunk(*c)
    return out


def load_eagle_frames():
    """base64 PNG → 스프라이트 시트 → 7프레임.
    libpng 호환 이슈 시 zlib re-encode → PIL → procedural 순으로 폴백."""
    sheet_bytes = base64.b64decode(SHEET_B64)
    sheet = None

    # 1차: BytesIO
    try:
        sheet = pygame.image.load(io.BytesIO(sheet_bytes)).convert_alpha()
    except pygame.error:
        pass

    # 2차: tempfile 경유 (일부 환경에서 BytesIO 대비 다른 코드 경로)
    if sheet is None:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                tf.write(sheet_bytes)
                tmp = tf.name
            sheet = pygame.image.load(tmp).convert_alpha()
            os.unlink(tmp)
            print("[Eagle] tempfile 경로로 PNG 로드 성공")
        except Exception:
            try: os.unlink(tmp)
            except Exception: pass

    # 3차: IDAT 재압축
    if sheet is None:
        try:
            repaired = _repair_png_deflate(sheet_bytes)
            sheet = pygame.image.load(io.BytesIO(repaired)).convert_alpha()
            print("[Eagle] PNG IDAT 재압축 복구 성공")
        except Exception:
            pass

    if sheet is None:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(sheet_bytes)).convert("RGBA")
            sheet = pygame.image.fromstring(img.tobytes(), img.size, "RGBA")
            print("[Eagle] PIL 복구 성공")
        except Exception:
            pass

    if sheet is None:
        print("[Eagle] PNG decode failed, using procedural eagle")
        return make_eagle_frames_procedural()

    frames = []
    for i in range(COLS):
        row, col = divmod(i, COLS)
        rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
        frames.append(sheet.subsurface(rect))
    return frames


def make_eagle_frames_procedural():
    """PNG 로드 실패 시 쓰이는 코드 생성 독수리 (41×20 × 7프레임).
    실루엣 위주 고대비 디자인 — 작게 렌더돼도 독수리로 인식되게."""
    BROWN     = ( 50,  32,  20)
    BROWN_MID = ( 85,  55,  32)
    BROWN_LT  = (130,  90,  55)
    BEAK      = (240, 185,  40)
    EYE       = (250, 220,  60)
    BLACK     = ( 10,   6,   4)

    # 날개 끝 Y 오프셋 (중심=10 기준, 음수=위)
    wing_offsets = [-8, -5, -1, 3, 6, 3, -3]

    frames = []
    for fi, wy in enumerate(wing_offsets):
        surf = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
        cx, cy = FRAME_W // 2, FRAME_H // 2   # (20, 10)

        # ── 날개: 베지어 스타일 곡선 삼각형 (5점 다각형) ──
        # 왼쪽 날개
        l_pts = [
            (cx - 2, cy - 2),           # 어깨 위
            (cx - 10, cy - 1 + wy // 3),# 중간 상단
            (0, cy + wy),               # 끝
            (cx - 10, cy + 2 + wy // 3),# 중간 하단
            (cx - 2, cy + 3),           # 어깨 아래
        ]
        pygame.draw.polygon(surf, BROWN_MID, l_pts)
        pygame.draw.polygon(surf, BROWN, l_pts, 1)

        # 오른쪽 날개 (미러)
        r_pts = [
            (cx + 2, cy - 2),
            (cx + 10, cy - 1 + wy // 3),
            (FRAME_W - 1, cy + wy),
            (cx + 10, cy + 2 + wy // 3),
            (cx + 2, cy + 3),
        ]
        pygame.draw.polygon(surf, BROWN_MID, r_pts)
        pygame.draw.polygon(surf, BROWN, r_pts, 1)

        # 깃털 라인 (각 날개 3줄)
        for j in range(3):
            t = 0.3 + j * 0.22
            # 왼쪽
            lx = int(cx - 2 + (0 - (cx - 2)) * t)
            ly = int(cy + wy * t)
            pygame.draw.line(surf, BROWN, (cx - 3, cy), (lx, ly), 1)
            # 오른쪽
            rx = int(cx + 2 + ((FRAME_W - 1) - (cx + 2)) * t)
            ry = int(cy + wy * t)
            pygame.draw.line(surf, BROWN, (cx + 3, cy), (rx, ry), 1)

        # ── 몸통 (세로로 긴 타원) ──
        pygame.draw.ellipse(surf, BROWN, (cx - 4, cy - 4, 8, 10))
        pygame.draw.ellipse(surf, BROWN_LT, (cx - 3, cy - 3, 4, 5))  # 가슴 하이라이트

        # ── 머리 (몸통 위) ──
        pygame.draw.circle(surf, BROWN, (cx, cy - 5), 3)
        pygame.draw.circle(surf, BROWN_MID, (cx - 1, cy - 6), 1)  # 하이라이트
        # 눈
        pygame.draw.circle(surf, EYE, (cx + 1, cy - 5), 1)
        surf.set_at((cx + 1, cy - 5), BLACK)

        # ── 부리 (머리 앞, 아래로 꺾인 후크) ──
        pygame.draw.polygon(surf, BEAK,
                            [(cx + 2, cy - 5), (cx + 5, cy - 4),
                             (cx + 3, cy - 3)])
        pygame.draw.line(surf, BLACK, (cx + 2, cy - 5), (cx + 5, cy - 4), 1)

        # ── 꼬리 (몸통 뒤, 부채꼴) ──
        tail_pts = [(cx - 2, cy + 4), (cx + 2, cy + 4),
                    (cx + 3, cy + 8), (cx, cy + 9), (cx - 3, cy + 8)]
        pygame.draw.polygon(surf, BROWN, tail_pts)
        pygame.draw.line(surf, BROWN_MID, (cx, cy + 4), (cx, cy + 8), 1)

        # ── 발톱 (몸통 아래, 위험감) ──
        pygame.draw.line(surf, BEAK, (cx - 1, cy + 5), (cx - 1, cy + 7), 1)
        pygame.draw.line(surf, BEAK, (cx + 1, cy + 5), (cx + 1, cy + 7), 1)

        frames.append(surf)
    return frames


# ── 알약 스프라이트 코드 생성 (sprite_tool.html 스타일 — asset-as-code) ──
def make_pill_surface(atype, size, rainbow_idx=0):
    """알약(캡슐) 스프라이트를 Surface로 즉석 생성.
    외부 PNG 대신 파이썬 코드로 에셋을 정의한다."""
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 타입별 (좌측 반쪽, 우측 반쪽) 색상
    PILL_COLORS = {
        NORMAL:   ((240, 255, 240), ( 60, 200,  80)),
        A_RED:    ((255, 220, 220), (225,  60,  60)),
        A_BLUE:   ((220, 230, 255), ( 60, 110, 225)),
        A_GOLD:   ((255, 245, 180), (255, 210,   0)),
        A_PURP:   ((235, 210, 255), (175,  50, 225)),
        A_SKULL:  ((235, 235, 235), ( 90,  90,  90)),
        A_WEAPON: (STEEL_COL,       WEAPON_COL),
    }

    if atype == A_RAIN:
        c1 = RAINBOW_CYCLE[rainbow_idx % len(RAINBOW_CYCLE)]
        c2 = RAINBOW_CYCLE[(rainbow_idx + 3) % len(RAINBOW_CYCLE)]
    else:
        c1, c2 = PILL_COLORS.get(atype, ((200, 200, 200), (100, 100, 100)))

    # 캡슐 본체 (가로 눕힘)
    pad_x = 2
    pill_h = int(h * 0.55)
    pill_y = (h - pill_h) // 2
    pill_rect = pygame.Rect(pad_x, pill_y, w - pad_x * 2, pill_h)
    half_w = pill_rect.width // 2
    r_cap = pill_rect.height // 2

    # 왼쪽 반쪽
    pygame.draw.rect(surf, c1, (pill_rect.x + r_cap, pill_rect.y, half_w - r_cap, pill_rect.height))
    pygame.draw.circle(surf, c1, (pill_rect.x + r_cap, pill_rect.centery), r_cap)
    # 오른쪽 반쪽
    pygame.draw.rect(surf, c2, (pill_rect.x + half_w, pill_rect.y, half_w - r_cap, pill_rect.height))
    pygame.draw.circle(surf, c2, (pill_rect.right - r_cap - 1, pill_rect.centery), r_cap)

    # 중앙 구분선
    pygame.draw.line(surf, (20, 20, 20),
                     (pill_rect.x + half_w, pill_rect.y + 1),
                     (pill_rect.x + half_w, pill_rect.bottom - 2), 1)

    # 상단 하이라이트 (광택)
    hl = pygame.Surface((pill_rect.width - 6, max(2, pill_rect.height // 4)), pygame.SRCALPHA)
    pygame.draw.rect(hl, (255, 255, 255, 160), hl.get_rect(), border_radius=2)
    surf.blit(hl, (pill_rect.x + 3, pill_rect.y + 2))

    # 외곽선
    pygame.draw.rect(surf, (40, 40, 40),
                     (pill_rect.x + r_cap, pill_rect.y, half_w * 2 - r_cap * 2, pill_rect.height), 1)
    pygame.draw.circle(surf, (40, 40, 40), (pill_rect.x + r_cap, pill_rect.centery), r_cap, 1)
    pygame.draw.circle(surf, (40, 40, 40), (pill_rect.right - r_cap - 1, pill_rect.centery), r_cap, 1)

    # 해골 알약: 오른쪽 반쪽에 해골 마크
    if atype == A_SKULL:
        cx = pill_rect.x + half_w + half_w // 2
        cy = pill_rect.centery
        pygame.draw.circle(surf, (30, 30, 30), (cx - 2, cy - 1), 1)
        pygame.draw.circle(surf, (30, 30, 30), (cx + 2, cy - 1), 1)
        pygame.draw.line(surf, (30, 30, 30), (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

    # 무기 알약: 가운데 십자 + 총알 자국
    if atype == A_WEAPON:
        cxw = pill_rect.centerx
        cyw = pill_rect.centery
        # 십자 마크
        pygame.draw.line(surf, (20, 20, 20), (cxw - 3, cyw), (cxw + 3, cyw), 1)
        pygame.draw.line(surf, (20, 20, 20), (cxw, cyw - 3), (cxw, cyw + 3), 1)
        # 우측 반쪽에 탄두 포인트
        pygame.draw.circle(surf, (255, 220, 100),
                           (pill_rect.right - 4, cyw), 1)

    return surf


def generate_bgm_sound():
    """사이키델릭 BGM을 코드로 합성 (짧은 루프).
    외부 파일이 없을 때 사용. numpy 없이 wave + struct만 사용."""
    import wave as _wave, struct as _struct, tempfile as _tempfile
    SR = 22050
    # 느리고 몽환적인 8비트 아르페지오
    # C 단조 느낌: C3, Eb3, G3, Bb3, D4, Eb4
    notes_hz = [130.81, 155.56, 196.00, 233.08, 293.66, 311.13, 196.00, 155.56]
    note_dur = 0.28  # 초
    total_samples = int(SR * note_dur * len(notes_hz))

    buf = bytearray()
    for i in range(total_samples):
        note_idx = int(i / (SR * note_dur)) % len(notes_hz)
        f = notes_hz[note_idx]
        t = i / SR
        local_t = (i % int(SR * note_dur)) / (SR * note_dur)
        # 엔벨로프 (attack-release)
        env = math.sin(local_t * math.pi) ** 0.5
        # 주음 + 5도 위 + 약간의 저음
        s1 = math.sin(2 * math.pi * f * t)
        s2 = math.sin(2 * math.pi * f * 1.5 * t) * 0.4
        s3 = math.sin(2 * math.pi * f * 0.5 * t) * 0.3
        # 약간의 비브라토로 몽환감
        vib = math.sin(2 * math.pi * 5 * t) * 0.02
        sample = (s1 + s2 + s3 + vib) * env * 0.22
        v = max(-1.0, min(1.0, sample))
        buf += _struct.pack('<h', int(v * 32000))

    # WAV 헤더 붙여서 in-memory bytes 생성
    bio = io.BytesIO()
    with _wave.open(bio, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(bytes(buf))
    bio.seek(0)
    return pygame.mixer.Sound(file=bio)


# ─────────────────────────────────────────────────────────────────────
# ── 파티클 시스템 ────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
class Particle:
    """사과 먹을 때, 충돌 시 등 시각 이펙트용 파티클"""
    def __init__(self, x, y, color, vx=None, vy=None, life=30, size=3, gravity=0.05):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-2.5, 2.5)
        self.vy = vy if vy is not None else random.uniform(-3.5, -0.5)
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        alpha = max(0, int(255 * self.life / self.max_life))
        s = max(1, int(self.size * self.life / self.max_life))
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (s, s), s)
        screen.blit(surf, (int(self.x) - s, int(self.y) - s))


class ParticleSystem:
    """파티클 관리자"""
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=12, spread=2.5, life=30, size=3):
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread * 1.2, -0.3)
            self.particles.append(
                Particle(x, y, color, vx, vy, life=life,
                         size=random.uniform(size * 0.5, size * 1.5)))

    def emit_ring(self, x, y, color, count=16, speed=2.5, life=25, size=2):
        """원형으로 퍼지는 파티클"""
        for i in range(count):
            angle = (2 * math.pi * i) / count
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(
                Particle(x, y, color, vx, vy, life=life, size=size, gravity=0))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


# ─────────────────────────────────────────────────────────────────────
class Eagle:
    """처음부터 화면 중앙에 나타나는 환각 독수리 (데모 방식 렌더링)"""

    def __init__(self, frames):
        self.frames      = frames   # 원본 41x20 프레임 리스트
        self.frame_idx   = 0
        self.frame_timer = 0
        self.appear_t    = 0.0
        self.active      = True

        w = FRAME_W * DISPLAY_SCALE
        h = FRAME_H * DISPLAY_SCALE
        self.x = WINDOW_WIDTH  // 2 - w // 2
        self.y = HUD_HEIGHT + (CELL_SIZE * GRID_HEIGHT) // 2 - h // 2

    def update(self, dt):
        if not self.active:
            return
        self.appear_t += dt
        self.frame_timer += int(dt * 1000)
        if self.frame_timer >= FRAME_DELAY:
            self.frame_idx   = (self.frame_idx + 1) % len(self.frames)
            self.frame_timer = 0

    def draw(self, screen):
        if not self.active:
            return
        w = FRAME_W * DISPLAY_SCALE
        h = FRAME_H * DISPLAY_SCALE
        pulse = abs(math.sin(self.appear_t * 2.5))

        # 보라 글로우
        glow = pygame.Surface((w + 60, h + 60), pygame.SRCALPHA)
        glow_alpha = int(60 + 100 * pulse)
        pygame.draw.ellipse(glow, (180, 50, 240, glow_alpha),
                            (0, 0, w + 60, h + 60))
        screen.blit(glow, (self.x - 30, self.y - 30))

        # 데모와 동일: transform.scale로 확대 후 blit
        frame_img = pygame.transform.scale(
            self.frames[self.frame_idx],
            (w, h)
        )
        screen.blit(frame_img, (self.x, self.y))

        # 레이블
        fnt = pygame.font.SysFont(None, 22)
        label_alpha = int(120 + 135 * pulse)
        lbl = fnt.render("< hallucination: eagle >", True, (220, 130, 255))
        lbl.set_alpha(label_alpha)
        screen.blit(lbl, (WINDOW_WIDTH // 2 - lbl.get_width() // 2,
                          self.y + h + 8))


# ─────────────────────────────────────────────────────────────────────
class Effect:
    def __init__(self, name, duration, delta=0):
        self.name = name; self.duration = duration
        self.timer = duration; self.delta = delta

    def tick(self):
        self.timer -= 1; return self.timer > 0


class FloatMsg:
    def __init__(self, text, color, cx, cy, life=80):
        self.text = text; self.color = color
        self.x = float(cx); self.y = float(cy)
        self.life = life; self.max_life = life

    def update(self):
        self.y -= 0.8; self.life -= 1; return self.life > 0

    def alpha(self):
        return int(255 * self.life / self.max_life)


# ─────────────────────────────────────────────────────────────────────
class Apple:
    def __init__(self, pos, atype):
        self.pos = pos; self.atype = atype; self._tick = 0

    def update(self): self._tick += 1

    def color(self):
        if self.atype == A_RAIN:
            return RAINBOW_CYCLE[(self._tick // 5) % len(RAINBOW_CYCLE)]
        return APPLE_COLOR[self.atype]


# ─────────────────────────────────────────────────────────────────────
class Projectile:
    """보스가 쏘는 에너지 탄환. 픽셀 좌표로 자유롭게 이동(대각 포함)."""
    SPEED_CPS = 8.0  # 셀/초

    def __init__(self, origin_cell, dx, dy):
        gx, gy = origin_cell
        self.x = gx * CELL_SIZE + CELL_SIZE / 2
        self.y = gy * CELL_SIZE + CELL_SIZE / 2 + HUD_HEIGHT
        self.dx = dx
        self.dy = dy
        self.alive = True
        self.trail = []

    def update(self, dt, game):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 4:
            self.trail.pop(0)

        speed_px = self.SPEED_CPS * CELL_SIZE * dt
        self.x += self.dx * speed_px
        self.y += self.dy * speed_px

        if (self.x < 0 or self.x > WINDOW_WIDTH or
                self.y < HUD_HEIGHT or self.y > PLAY_BOTTOM):
            self.alive = False
            return

        gx = int(self.x // CELL_SIZE)
        gy = int((self.y - HUD_HEIGHT) // CELL_SIZE)

        if (gx, gy) in game.obstacles:
            self.alive = False
            return

        for sx, sy in game.snake.body:
            if sx == gx and sy == gy:
                game._snake_hit()
                self.alive = False
                return

    def draw(self, screen):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(40 + i * 25)
            r = 3 + i
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 80, 80, alpha), (r, r), r)
            screen.blit(surf, (int(tx) - r, int(ty) - r))

        pulse = abs(math.sin(pygame.time.get_ticks() * 0.015))
        core_r = int(5 + 1.5 * pulse)
        glow = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 60, 80, 120), (8, 8), 8)
        screen.blit(glow, (int(self.x) - 8, int(self.y) - 8))
        pygame.draw.circle(screen, (255, 100, 120),
                           (int(self.x), int(self.y)), core_r)
        pygame.draw.circle(screen, (255, 240, 240),
                           (int(self.x), int(self.y)), 2)


# ─────────────────────────────────────────────────────────────────────
class SnakeBullet:
    """뱀 포탑이 발사하는 황금 총알. 보스에 적중 시 HP 감소."""
    SPEED_CPS = 12.0

    def __init__(self, origin_cell, direction):
        gx, gy = origin_cell
        self.x = gx * CELL_SIZE + CELL_SIZE / 2
        self.y = gy * CELL_SIZE + CELL_SIZE / 2 + HUD_HEIGHT
        self.dx, self.dy = direction
        self.alive = True
        self.trail = []

    def update(self, dt, game):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 3:
            self.trail.pop(0)

        speed_px = self.SPEED_CPS * CELL_SIZE * dt
        self.x += self.dx * speed_px
        self.y += self.dy * speed_px

        if (self.x < 0 or self.x > WINDOW_WIDTH or
                self.y < HUD_HEIGHT or self.y > PLAY_BOTTOM):
            self.alive = False
            return

        gx = int(self.x // CELL_SIZE)
        gy = int((self.y - HUD_HEIGHT) // CELL_SIZE)

        if (gx, gy) in game.obstacles:
            self.alive = False
            return

        if game.boss and (gx, gy) == game.boss.pos:
            game._boss_take_damage(1)
            self.alive = False
            return

    def draw(self, screen):
        # 잔상
        for i, (tx, ty) in enumerate(self.trail):
            r = 2 + i
            alpha = 60 + i * 40
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 220, 100, alpha), (r, r), r)
            screen.blit(surf, (int(tx) - r, int(ty) - r))
        # 본체
        pygame.draw.circle(screen, (255, 230, 100),
                           (int(self.x), int(self.y)), 3)
        pygame.draw.circle(screen, (255, 255, 230),
                           (int(self.x), int(self.y)), 1)


class SnakeGun:
    """뱀 몸통에 영구 장착된 포탑. 마우스 방향으로 자동 발사."""
    FIRE_INTERVAL = 0.9

    def __init__(self, slot):
        self.slot = slot              # 몸통 인덱스 (1 = 머리 바로 뒤)
        self.fire_t = 0.2 + 0.2 * slot  # 살짝 엇갈린 첫 발사
        self.recoil = 0.0
        self.aim_dx = 1.0              # 마지막 조준 단위벡터 (그리기용)
        self.aim_dy = 0.0

    def _aim_vector(self, snake, mouse_pos):
        """마우스 위치로 향하는 단위벡터 (마우스가 포탑 위면 뱀 진행 방향)."""
        if self.slot >= len(snake.body):
            return snake.direction
        gx, gy = snake.body[self.slot]
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        mx, my = mouse_pos
        dx = mx - cx; dy = my - cy
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return snake.direction
        return (dx / dist, dy / dist)

    def update(self, dt, game, snake):
        self.fire_t -= dt
        self.recoil = max(0.0, self.recoil - dt * 4.0)
        if self.slot >= len(snake.body):
            return  # 몸통이 짧아지면 이번 틱 발사 생략
        self.aim_dx, self.aim_dy = self._aim_vector(snake, game.mouse_pos)
        if self.fire_t <= 0:
            game.snake_bullets.append(
                SnakeBullet(snake.body[self.slot],
                            (self.aim_dx, self.aim_dy)))
            self.fire_t = self.FIRE_INTERVAL
            self.recoil = 1.0
            play_sound(game.sounds.get("eat_normal"), 0.12)

    def draw(self, screen, snake):
        if self.slot >= len(snake.body):
            return
        gx, gy = snake.body[self.slot]
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        dx, dy = self.aim_dx, self.aim_dy

        # 포탑 본체
        pygame.draw.circle(screen, (70, 75, 90), (cx, cy), 6)
        pygame.draw.circle(screen, (140, 150, 170), (cx, cy), 5)
        pygame.draw.circle(screen, (30, 30, 40), (cx, cy), 6, 1)

        # 총구 (마우스 조준 + 반동)
        recoil_off = int(self.recoil * 2)
        bx = cx + int(dx * (9 - recoil_off))
        by = cy + int(dy * (9 - recoil_off))
        pygame.draw.line(screen, (50, 50, 60), (cx, cy), (bx, by), 3)
        pygame.draw.circle(screen, (255, 200, 80), (bx, by), 2)


# ─────────────────────────────────────────────────────────────────────
class GridBoss:
    """그리드 위의 고정 보스. 주기적으로 8방향 중 랜덤 투사체 발사.
    상/하/좌/우 4칸을 뱀 몸통/장애물/맵 경계로 전부 막으면 처치."""
    SHOOT_INTERVAL = 2.0
    SURROUND_DIRS  = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    DIRS_8 = [(math.cos(i * math.pi / 4), math.sin(i * math.pi / 4))
              for i in range(8)]

    MAX_HP = 3

    def __init__(self, pos, frames=None):
        self.pos = pos
        self.frames = frames
        self.frame_idx = 0
        self.frame_timer = 0
        self.anim_t = 0.0
        self.shoot_t = 0.6
        self.spawn_t = 0.0
        self.hp = self.MAX_HP
        self.hit_flash = 0.0

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 0.3
        return self.hp <= 0

    def update(self, dt, game):
        self.anim_t += dt
        self.spawn_t = min(1.0, self.spawn_t + dt * 3.0)
        self.shoot_t -= dt
        if self.hit_flash > 0:
            self.hit_flash = max(0.0, self.hit_flash - dt)
        # 프레임 애니메이션 (150ms 주기)
        self.frame_timer += int(dt * 1000)
        if self.frames and self.frame_timer >= 150:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self.frame_timer = 0
        if self.shoot_t <= 0:
            self._fire(game)
            self.shoot_t = self.SHOOT_INTERVAL

    def _fire(self, game):
        dx, dy = random.choice(self.DIRS_8)
        game.projectiles.append(Projectile(self.pos, dx, dy))

    def is_surrounded(self, snake_cells, obstacles):
        bx, by = self.pos
        for dx, dy in self.SURROUND_DIRS:
            nx, ny = bx + dx, by + dy
            if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                continue  # 맵 경계는 "이미 막힘"
            if (nx, ny) not in snake_cells and (nx, ny) not in obstacles:
                return False
        return True

    def draw(self, screen):
        gx, gy = self.pos
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT

        pulse = abs(math.sin(self.anim_t * 3.5))

        # 붉은 글로우 광원 (위협감)
        glow_r = int(CELL_SIZE * 1.4 + 8 * pulse)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (220, 40, 80, int(80 + 80 * pulse)),
                           (glow_r, glow_r), glow_r)
        screen.blit(glow, (cx - glow_r, cy - glow_r))

        if self.spawn_t <= 0.02:
            return

        # ── 독수리 스프라이트 (항상 존재) ──
        w = int(CELL_SIZE * 3.2 * self.spawn_t)
        h = int(CELL_SIZE * 1.65 * self.spawn_t)
        if self.frames and w > 0 and h > 0:
            frame = pygame.transform.scale(self.frames[self.frame_idx], (w, h))
            if self.hit_flash > 0:
                # 피격 플래시: 흰색 틴트 오버레이
                flash = frame.copy()
                flash.fill((255, 255, 255, int(200 * self.hit_flash / 0.3)),
                           special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(flash, (cx - w // 2, cy - h // 2))
            else:
                screen.blit(frame, (cx - w // 2, cy - h // 2))

        # HP 바 (보스 상단)
        hp_y = cy - int(h * 0.55) - 8
        for i in range(self.MAX_HP):
            sx = cx - (self.MAX_HP * 10) // 2 + i * 10
            if i < self.hp:
                pygame.draw.rect(screen, (255, 80, 100), (sx, hp_y, 8, 5))
            else:
                pygame.draw.rect(screen, (60, 20, 30), (sx, hp_y, 8, 5))
            pygame.draw.rect(screen, (240, 240, 240), (sx, hp_y, 8, 5), 1)

        # 발사 임박 경고 링
        threat = 1.0 - min(1.0, self.shoot_t / 0.6)
        if threat > 0:
            ring_r = int(CELL_SIZE * 0.9)
            ring_alpha = int(220 * threat)
            ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (255, 60, 80, ring_alpha),
                               (ring_r + 2, ring_r + 2), ring_r, 2)
            screen.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))


# ─────────────────────────────────────────────────────────────────────
class Snake:
    BASE_SPEED = 6

    def __init__(self):
        cx, cy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.body      = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction = RIGHT; self.next_dir = RIGHT
        self.dir_queue = []  # 입력 버퍼 (최대 2개)
        self.effects   = []; self.grow = 0
        self.alive     = True; self.score = 0
        self.speed_mod = 0; self.apple_count = 0

    @property
    def head(self): return self.body[0]

    @property
    def speed(self):
        return max(3.0, min(12.0, self.BASE_SPEED + self.speed_mod +
                            (self.apple_count // 5) * 0.5))

    @property
    def wall_pass(self):
        return any(e.name == "wall_pass" for e in self.effects)

    def set_dir(self, d):
        """빠른 두 번 꺾기 지원 — 최근 의도한 방향 기준으로 판정 후 큐에 추가."""
        last = self.dir_queue[-1] if self.dir_queue else self.next_dir
        # 반대 방향 / 중복 방향은 무시
        if d == OPPOSITE[last] or d == last:
            return
        if len(self.dir_queue) < 2:
            self.dir_queue.append(d)

    def add_effect(self, name, duration, delta=0):
        for e in self.effects:
            if e.name == name: e.timer = duration; return
        self.effects.append(Effect(name, duration, delta))
        self.speed_mod += delta

    def tick_effects(self):
        alive = []
        for e in self.effects:
            if e.tick(): alive.append(e)
            else: self.speed_mod -= e.delta
        self.effects = alive

    def move(self, obstacles):
        # 입력 버퍼에 대기 중인 방향이 있으면 현재 것으로 확정
        if self.dir_queue:
            self.next_dir = self.dir_queue.pop(0)
        self.direction = self.next_dir
        hx, hy = self.head; dx, dy = self.direction
        nx, ny = hx + dx, hy + dy
        if self.wall_pass:
            nx %= GRID_WIDTH; ny %= GRID_HEIGHT
        else:
            if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT): return False
        nh = (nx, ny)
        if nh in self.body[1:] or nh in obstacles: return False
        self.body.insert(0, nh)
        if self.grow > 0: self.grow -= 1
        else: self.body.pop()
        return True

    def cut_half(self):
        if len(self.body) <= 3: return []
        c = len(self.body) // 2
        rem = self.body[c:]; self.body = self.body[:c]; return rem

    def shrink(self, n=2):
        """몸통 축소 - 최소 길이 3 유지"""
        for _ in range(n):
            if len(self.body) > 3: self.body.pop()

    def can_shrink(self):
        """축소 가능 여부 - 몸통 5칸 이상일 때만"""
        return len(self.body) >= 5

    def reverse(self):
        """몸통 순서를 뒤집고 새 머리의 실제 진행 방향을 계산.
        (단순 OPPOSITE[direction]은 꺾인 몸통일 때 body[1]로 직진해 즉사함)"""
        self.body.reverse()
        if len(self.body) >= 2:
            hx, hy = self.body[0]
            bx, by = self.body[1]
            # body[1] → body[0] 벡터가 새 진행 방향 (몸통에서 멀어지는 쪽)
            self.direction = (hx - bx, hy - by)
        else:
            self.direction = OPPOSITE[self.direction]
        self.next_dir = self.direction
        self.dir_queue.clear()


# ─────────────────────────────────────────────────────────────────────
class Game:
    S_MENU  = "menu"
    S_PLAY  = "play"
    S_CLEAR = "clear"
    S_OVER  = "over"

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("약먹은 스네이크")
        self.clock  = pygame.time.Clock()

        cands = ["malgun gothic", "nanum gothic", "applegothic", "gulim", "arial"]
        fn = next((c for c in cands if c in [f.lower() for f in pygame.font.get_fonts()]), None)
        self.fnt_xl = pygame.font.SysFont(fn, 46, bold=True)
        self.fnt_lg = pygame.font.SysFont(fn, 30, bold=True)
        self.fnt_md = pygame.font.SysFont(fn, 22)
        self.fnt_sm = pygame.font.SysFont(fn, 16)

        # 독수리 프레임 로드
        self._eagle_frames = load_eagle_frames()

        # ── 선택적 외부 배경 이미지 ──
        # assets/images/lab_bg.png 가 있으면 실험실 벽 대신 사용한다.
        # 이미지는 창 크기(WINDOW_WIDTH x WINDOW_HEIGHT)로 자동 스케일.
        self.lab_bg = load_image("lab_bg.png", (WINDOW_WIDTH, WINDOW_HEIGHT))

        # ── 알약 스프라이트 (파이썬 코드로 생성한 에셋) ──
        # 기존 사과 PNG → 알약 캡슐 Surface 로 교체
        pill_size = (CELL_SIZE - 2, CELL_SIZE - 2)
        self.pill_size = pill_size
        self.pill_images = {
            NORMAL:  make_pill_surface(NORMAL,  pill_size),
            A_RED:   make_pill_surface(A_RED,   pill_size),
            A_BLUE:  make_pill_surface(A_BLUE,  pill_size),
            A_GOLD:  make_pill_surface(A_GOLD,  pill_size),
            A_PURP:  make_pill_surface(A_PURP,  pill_size),
            A_SKULL: make_pill_surface(A_SKULL, pill_size),
            # 무지개는 매 프레임 색 순환이라 런타임 생성
        }
        # 뱀 머리 (4방향 회전)
        head_img = load_image("snake_head.png", (CELL_SIZE - 2, CELL_SIZE - 2))
        self.head_images = {}
        if head_img:
            self.head_images[RIGHT] = head_img
            self.head_images[UP]    = pygame.transform.rotate(head_img, 90)
            self.head_images[LEFT]  = pygame.transform.rotate(head_img, 180)
            self.head_images[DOWN]  = pygame.transform.rotate(head_img, 270)
        # 장애물
        self.obstacle_img = load_image("obstacle.png", (CELL_SIZE - 2, CELL_SIZE - 2))
        # 사운드
        self.sounds = {
            "eat_normal":  load_sound("eat_normal.wav"),
            "eat_special": load_sound("eat_special.wav"),
            "eat_skull":   load_sound("eat_skull.wav"),
            "eat_gold":    load_sound("eat_gold.wav"),
            "speed_up":    load_sound("speed_up.wav"),
            "speed_down":  load_sound("speed_down.wav"),
            "wall_pass":   load_sound("wall_pass.wav"),
            "reverse":     load_sound("reverse.wav"),
            "game_over":   load_sound("game_over.wav"),
            "clear":       load_sound("clear.wav"),
        }

        # ── BGM: 외부 파일 우선, 없으면 코드로 합성한 루프 사용 ──
        self.bgm = None
        for fname in ("bgm.ogg", "bgm.mp3", "bgm.wav"):
            p = os.path.join(SND_DIR, fname)
            if os.path.exists(p):
                try:
                    pygame.mixer.music.load(p)
                    pygame.mixer.music.set_volume(0.35)
                    pygame.mixer.music.play(-1)
                    self.bgm = "external"
                except pygame.error:
                    pass
                break
        if self.bgm is None:
            try:
                self._synth_bgm = generate_bgm_sound()
                self._synth_bgm.set_volume(0.22)
                self._synth_bgm.play(loops=-1)
                self.bgm = "synth"
            except Exception as e:
                print(f"[BGM] 합성 실패: {e}")

        # 파티클 시스템
        self.particles = ParticleSystem()

        # 화면 흔들림
        self.shake_x = 0
        self.shake_y = 0
        self.shake_timer = 0

        self.state      = self.S_MENU
        self.snake      = Snake()
        self.apple      = None
        self.obstacles  = set()
        self.msgs       = []
        self.move_accum = 0.0
        self.high_score = 0
        self.clear_timer = 0
        self.crack_lines = []
        self.eagle       = None
        self.boss            = None     # 현재 활성 GridBoss (최대 1마리)
        self.projectiles     = []       # 보스 투사체
        self.snake_guns      = []       # 뱀 포탑 목록 (영구)
        self.snake_bullets   = []       # 뱀 총알
        self.mouse_pos       = (WINDOW_WIDTH // 2,
                                HUD_HEIGHT + (CELL_SIZE * GRID_HEIGHT) // 2)
        self.lives           = 3
        self.iframe_timer    = 0.0      # 피격 무적 남은 시간(초)
        self.next_boss_at    = 10       # 다음 보스 스폰할 apple_count 임계값
        self.psyche_timer = 0.0       # 사이키델릭 배경 남은 시간(초)
        self.menu_tick   = 0  # 메뉴 애니메이션용

        # 배경 별 (실험실 느낌의 떠다니는 입자)
        self._bg_particles = []
        for _ in range(25):
            self._bg_particles.append({
                'x': random.uniform(0, WINDOW_WIDTH),
                'y': random.uniform(HUD_HEIGHT, WINDOW_HEIGHT),
                'speed': random.uniform(0.1, 0.4),
                'size': random.uniform(1, 2.5),
                'alpha': random.randint(30, 90),
                'color': random.choice([
                    (100, 200, 100), (100, 150, 255), (200, 100, 255),
                    (255, 200, 80), (150, 150, 180)
                ])
            })

    # ── 리셋 ──────────────────────────────────────────────────────────
    def reset(self):
        self.snake      = Snake()
        self.apple      = None
        self.obstacles  = set()
        self.msgs       = []
        self.move_accum = 0.0
        self.clear_timer = 0
        self.crack_lines = []
        self.particles   = ParticleSystem()
        self.boss         = None
        self.projectiles  = []
        self.snake_guns   = []
        self.snake_bullets = []
        self.lives        = 3
        self.iframe_timer = 0.0
        self.next_boss_at = 10
        self.psyche_timer = 0.0
        # 독수리는 이제 보스 전용 — 상시 환각 Eagle은 제거
        self.eagle = None
        self._spawn_apple()

    # ── 유틸 ──────────────────────────────────────────────────────────
    def filled_cells(self): return len(self.snake.body) + len(self.obstacles)
    def fill_ratio(self):   return self.filled_cells() / TOTAL_CELLS

    def _spawn_apple(self):
        occ  = set(self.snake.body) | self.obstacles
        if self.apple: occ.add(self.apple.pos)
        free = [(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
                if (x, y) not in occ]
        if not free: return
        self.apple = Apple(random.choice(free), random.choice(APPLE_POOL))

    def _init_clear(self):
        self.state = self.S_CLEAR
        self.high_score = max(self.high_score, self.snake.score)
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        self.crack_lines = []
        for _ in range(18):
            a = random.uniform(0, 6.28); l = random.randint(60, 220)
            self.crack_lines.append((cx, cy,
                                     int(cx + l * math.cos(a)),
                                     int(cy + l * math.sin(a))))
        # 클리어 파티클 폭발
        self.particles.emit_ring(cx, cy, GOLD, count=30, speed=4, life=50, size=4)
        self.particles.emit(cx, cy, (255, 255, 255), count=20, spread=4, life=40, size=3)
        play_sound(self.sounds["clear"], 0.6)

    def _msg(self, text, color, gx, gy):
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.msgs.append(FloatMsg(text, color, cx, cy))

    def _shake(self, intensity=5, duration=10):
        """화면 흔들림 효과"""
        self.shake_timer = duration
        self.shake_x = random.uniform(-intensity, intensity)
        self.shake_y = random.uniform(-intensity, intensity)

    def _snake_hit(self):
        """투사체 또는 보스에 피격. 무적 중이면 무시, 아니면 목숨 -1."""
        if self.iframe_timer > 0 or self.state != self.S_PLAY:
            return
        self.lives -= 1
        self.iframe_timer = 1.2

        hx, hy = self.snake.head
        px = hx * CELL_SIZE + CELL_SIZE // 2
        py = hy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.particles.emit_ring(px, py, (255, 80, 100),
                                 count=18, speed=3.2, life=30, size=3)
        self.msgs.append(FloatMsg("-1 LIFE", (255, 90, 120), px, py))
        self._shake(7, 14)
        play_sound(self.sounds.get("game_over"), 0.35)

        if self.lives <= 0:
            self.high_score = max(self.high_score, self.snake.score)
            self.state = self.S_OVER
            self.particles.emit(px, py, RED, count=24, spread=3.5, life=40, size=4)
            play_sound(self.sounds.get("game_over"), 0.65)

    def _spawn_boss(self):
        """알약 10의 배수 도달 시 그리드 빈 칸에 보스 스폰 (머리 근처 회피)."""
        hx, hy = self.snake.head
        occ = set(self.snake.body) | self.obstacles
        if self.apple: occ.add(self.apple.pos)

        safe_cells = []
        far_cells  = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if (x, y) in occ: continue
                dist = abs(x - hx) + abs(y - hy)
                if dist >= 4:
                    safe_cells.append((x, y))
                else:
                    far_cells.append((x, y))
        pool = safe_cells or far_cells
        if not pool:
            return  # 자리 없으면 스킵
        pos = random.choice(pool)
        self.boss = GridBoss(pos, frames=self._eagle_frames)

        # 경고 효과
        self._shake(6, 14)
        px = pos[0] * CELL_SIZE + CELL_SIZE // 2
        py = pos[1] * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.msgs.append(FloatMsg("! WARNING !", (255, 80, 100), px, py, life=120))
        self.particles.emit_ring(px, py, (255, 60, 80),
                                 count=20, speed=2.5, life=30, size=3)
        play_sound(self.sounds.get("eat_skull"), 0.45)

    def _boss_take_damage(self, amount):
        """총알 적중 시 보스 HP 감소. HP 0이 되면 _kill_boss 호출."""
        if not self.boss:
            return
        dead = self.boss.take_damage(amount)
        bx, by = self.boss.pos
        px = bx * CELL_SIZE + CELL_SIZE // 2
        py = by * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.particles.emit(px, py, (255, 220, 100),
                            count=10, spread=2.5, life=20, size=2)
        self._shake(4, 8)
        if dead:
            self._kill_boss()

    def _kill_boss(self):
        """보스 처치 (포위 완성 or HP 0). 투사체도 일괄 소멸."""
        if not self.boss:
            return
        bx, by = self.boss.pos
        px = bx * CELL_SIZE + CELL_SIZE // 2
        py = by * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT

        self.snake.score += 100
        self.msgs.append(FloatMsg("보스 처치! +100", (255, 200, 80), px, py, life=120))
        self.particles.emit_ring(px, py, (255, 120, 60),
                                 count=36, speed=4.5, life=55, size=4)
        self.particles.emit_ring(px, py, (255, 220, 120),
                                 count=24, speed=2.5, life=40, size=3)
        self.particles.emit(px, py, (255, 255, 255),
                            count=18, spread=3.5, life=35, size=3)
        self._shake(9, 22)

        self.boss = None
        self.projectiles.clear()
        self.snake_bullets.clear()
        play_sound(self.sounds.get("clear"), 0.45)

    def _emit_apple_particles(self, gx, gy, color, count=10):
        """사과 위치에서 파티클 발사"""
        px = gx * CELL_SIZE + CELL_SIZE // 2
        py = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.particles.emit(px, py, color, count=count)

    # ── 이벤트 ────────────────────────────────────────────────────────
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if self.state == self.S_MENU:
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = self.S_PLAY; self.reset()
                elif self.state == self.S_PLAY:
                    dirs = {pygame.K_UP: UP, pygame.K_w: UP,
                            pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
                            pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
                            pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT}
                    if k in dirs: self.snake.set_dir(dirs[k])
                    elif k == pygame.K_ESCAPE: self.state = self.S_MENU
                elif self.state in (self.S_CLEAR, self.S_OVER):
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = self.S_PLAY; self.reset()
                    elif k == pygame.K_ESCAPE: self.state = self.S_MENU

    # ── 업데이트 ──────────────────────────────────────────────────────
    def update(self, dt):
        # 마우스 위치는 모든 상태에서 갱신 (조준용)
        self.mouse_pos = pygame.mouse.get_pos()
        # 파티클은 항상 업데이트
        self.particles.update()

        # 배경 입자 업데이트
        for bp in self._bg_particles:
            bp['y'] -= bp['speed']
            if bp['y'] < HUD_HEIGHT:
                bp['y'] = WINDOW_HEIGHT
                bp['x'] = random.uniform(0, WINDOW_WIDTH)

        # 화면 흔들림 감쇠
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_x *= 0.8
            self.shake_y *= 0.8
        else:
            self.shake_x = 0
            self.shake_y = 0

        if self.state == self.S_MENU:
            self.menu_tick += 1
            return
        if self.state == self.S_CLEAR: self.clear_timer += 1; return
        if self.state != self.S_PLAY:  return

        self.snake.tick_effects()
        if self.apple:  self.apple.update()
        if self.eagle:  self.eagle.update(dt)
        if self.psyche_timer > 0:
            self.psyche_timer = max(0.0, self.psyche_timer - dt)
        if self.iframe_timer > 0:
            self.iframe_timer = max(0.0, self.iframe_timer - dt)
        self.msgs = [m for m in self.msgs if m.update()]

        # 보스 업데이트 + 포위 판정 + 머리 접촉
        if self.boss:
            self.boss.update(dt, self)
            snake_cells = set(self.snake.body)
            if self.boss.is_surrounded(snake_cells, self.obstacles):
                self._kill_boss()
            elif self.boss and self.snake.head == self.boss.pos:
                self._snake_hit()

        # 투사체 업데이트 & 정리
        for p in self.projectiles:
            p.update(dt, self)
        if self.projectiles:
            self.projectiles = [p for p in self.projectiles if p.alive]

        # 뱀 포탑 업데이트 (영구 장착 — 제거 없음)
        for g in self.snake_guns:
            g.update(dt, self, self.snake)
        # 뱀 총알 업데이트 & 정리
        for b in self.snake_bullets:
            b.update(dt, self)
        if self.snake_bullets:
            self.snake_bullets = [b for b in self.snake_bullets if b.alive]

        self.move_accum += self.snake.speed * dt
        while self.move_accum >= 1.0:
            self.move_accum -= 1.0
            if not self.snake.move(self.obstacles):
                self.high_score = max(self.high_score, self.snake.score)
                self.state = self.S_OVER
                self._shake(8, 15)  # 사망 시 화면 흔들림
                # 사망 파티클
                hx, hy = self.snake.head
                px = hx * CELL_SIZE + CELL_SIZE // 2
                py = hy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
                self.particles.emit(px, py, RED, count=20, spread=3, life=35, size=4)
                play_sound(self.sounds["game_over"], 0.6)
                return
            if self.apple and self.snake.head == self.apple.pos:
                self._apply(self.apple)
                self.apple = None; self.snake.apple_count += 1
                self._spawn_apple()
                # 알약 10개마다 보스 스폰 (기존 보스 없을 때만)
                if (self.boss is None and
                        self.snake.apple_count >= self.next_boss_at):
                    self._spawn_boss()
                    self.next_boss_at += 10
            if self.filled_cells() >= TOTAL_CELLS:
                self._init_clear(); return

    def _apply(self, a):
        t = a.atype; ax, ay = a.pos
        if t == NORMAL:
            self.snake.grow += 1; self.snake.score += 10
            self._msg("+1 성장", GREEN_APPLE, ax, ay)
            self._emit_apple_particles(ax, ay, GREEN_APPLE)
            play_sound(self.sounds["eat_normal"], 0.5)
        elif t == A_RED:
            self.snake.grow += 1; self.snake.score += 10
            self.snake.add_effect("speed_up", 5*FPS, delta=+3)
            self._msg("속도 UP!", RED, ax, ay)
            self._emit_apple_particles(ax, ay, RED, 15)
            self._shake(3, 8)
            play_sound(self.sounds["eat_special"], 0.5)
            play_sound(self.sounds["speed_up"], 0.4)
        elif t == A_BLUE:
            self.snake.grow += 1; self.snake.score += 10
            self.snake.add_effect("slow_down", 5*FPS, delta=-3)
            self._msg("속도 DOWN...", BLUE, ax, ay)
            self._emit_apple_particles(ax, ay, BLUE)
            play_sound(self.sounds["eat_special"], 0.5)
            play_sound(self.sounds["speed_down"], 0.4)
        elif t == A_GOLD:
            self.snake.grow += 1; self.snake.score += 25
            cut = self.snake.cut_half()
            for seg in cut: self.obstacles.add(seg)
            if self.apple and self.apple.pos in self.obstacles: self.apple = None
            self._msg(f"절단! +{len(cut)}장애물", GOLD, ax, ay)
            self._emit_apple_particles(ax, ay, GOLD, 20)
            self._shake(6, 12)  # 절단 시 강한 흔들림
            play_sound(self.sounds["eat_gold"], 0.6)
        elif t == A_RAIN:
            self.snake.grow += 1; self.snake.score += 5
            self.snake.reverse()
            # 반전 직후 꼬리(=새 머리)가 맵 가장자리면 즉사 방지:
            # 2초 동안 벽 통과 효과로 안전 유예
            self.snake.add_effect("wall_pass", 2 * FPS)
            self._msg("방향 반전!", (200, 100, 255), ax, ay)
            for c in RAINBOW_CYCLE:
                self._emit_apple_particles(ax, ay, c, 3)
            self.psyche_timer = 5.0
            play_sound(self.sounds["reverse"], 0.5)
        elif t == A_PURP:
            self.snake.grow += 1; self.snake.score += 10
            self.snake.add_effect("wall_pass", 5*FPS)
            self._msg("벽 통과!", PURPLE, ax, ay)
            self._emit_apple_particles(ax, ay, PURPLE, 15)
            play_sound(self.sounds["wall_pass"], 0.5)
        elif t == A_WEAPON:
            self.snake.grow += 1; self.snake.score += 10
            # 빈 슬롯(1→3 순)에 포탑 영구 장착
            used = {g.slot for g in self.snake_guns}
            for slot in (1, 2, 3):
                if slot not in used:
                    self.snake_guns.append(SnakeGun(slot))
                    self._msg(f"포탑 #{slot} 장착!", (255, 200, 80), ax, ay)
                    break
            else:
                # 슬롯 3개 가득 — 보너스 점수만
                self.snake.score += 20
                self._msg("+20 (포탑 MAX)", (255, 200, 80), ax, ay)
            self._emit_apple_particles(ax, ay, WEAPON_COL, 15)
            self._shake(3, 8)
            play_sound(self.sounds.get("eat_gold"), 0.4)
        elif t == A_SKULL:
            # ★ 해골 사과 밸런스 개선: 몸통 5칸 이상일 때만 축소
            if self.snake.can_shrink():
                self.snake.shrink(2)
                self.snake.score += 15   # 보상 점수 증가 (3 → 15)
                self._msg("축소! +15점", SKULL_COL, ax, ay)
                self._emit_apple_particles(ax, ay, SKULL_COL)
                self._shake(2, 6)
            else:
                # 몸통이 짧으면 무효 → 오히려 보너스 점수
                self.snake.score += 20
                self.snake.grow += 1
                self._msg("저항 성공! +20점", (150, 255, 150), ax, ay)
                self._emit_apple_particles(ax, ay, (150, 255, 150), 8)
            play_sound(self.sounds["eat_skull"], 0.5)

    # ── 그리기 ────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(BG)

        if self.state == self.S_MENU:
            self._draw_menu()
        else:
            self._draw_hud()
            # 무지개 알약 효과 중엔 사이키델릭 배경으로 대체
            if self.psyche_timer > 0:
                self._draw_psychedelic_bg()
            else:
                self._draw_flask_background()  # 플라스크 내부 (흰 바닥)
            self._draw_grid()
            self._draw_bg_particles()      # 떠다니는 약 입자
            self._draw_obstacles()
            if self.apple:  self._draw_apple()
            if self.boss:   self.boss.draw(self.screen)
            self._draw_snake()
            # 뱀 포탑 (몸통 위 렌더)
            for g in self.snake_guns:
                g.draw(self.screen, self.snake)
            # 투사체 (보스 → 뱀, 뱀 포탑 → 보스)
            for p in self.projectiles:
                p.draw(self.screen)
            for b in self.snake_bullets:
                b.draw(self.screen)
            if self.eagle:  self.eagle.draw(self.screen)
            self._draw_flask_border()      # 플라스크 유리 테두리 (위에 그림)
            self._draw_lab_bench()         # 바닥 실험실 콘솔
            self.particles.draw(self.screen)
            self._draw_msgs()
            if self.state == self.S_OVER:    self._draw_overlay_over()
            elif self.state == self.S_CLEAR: self._draw_overlay_clear()
        pygame.display.flip()

    def _draw_psychedelic_bg(self):
        """무지개 알약 효과 중 배경 — 빨려들어가는 무지개 회오리.
        가벼운 draw.circle 링 쌓기로 60fps 유지."""
        gy = HUD_HEIGHT
        gw = WINDOW_WIDTH
        gh = CELL_SIZE * GRID_HEIGHT
        t  = pygame.time.get_ticks() * 0.001

        # 효과 끝자락 0.6초 동안 서서히 옅어짐
        fade = 1.0 if self.psyche_timer > 0.6 else (self.psyche_timer / 0.6)

        surf = pygame.Surface((gw, gh))
        cx, cy = gw // 2, gh // 2
        max_r = int(math.hypot(gw, gh)) + 20
        ring_w = 14
        offset = int((t * 50) % ring_w)

        # 바깥에서 안쪽으로 동심 링 (두께로 채움 → fill 불필요)
        r = max_r + offset
        i = 0
        while r > 0:
            color_idx = (i + int(t * 3.0)) % len(RAINBOW_CYCLE)
            pygame.draw.circle(surf, RAINBOW_CYCLE[color_idx],
                               (cx, cy), r, ring_w + 1)
            r -= ring_w
            i += 1
        # 중심 원
        pygame.draw.circle(surf,
                           RAINBOW_CYCLE[int(t * 4) % len(RAINBOW_CYCLE)],
                           (cx, cy), ring_w)

        # 중앙 화이트 스파크 (맥동)
        pulse = abs(math.sin(t * 5))
        sp = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(sp, (255, 255, 255, int(120 * pulse)),
                           (15, 15), int(6 + 4 * pulse))
        surf.blit(sp, (cx - 15, cy - 15))

        if fade < 1.0:
            surf.set_alpha(int(255 * fade))
        self.screen.blit(surf, (0, gy))

    # ── 실험실 배경 요소 ────────────────────────────────────────────────
    def _draw_lab_wall(self, rect):
        """연구실 벽: 외부 이미지(lab_bg.png) 우선, 없으면 코드 생성 패턴.
        rect: 채울 화면 영역 (HUD 또는 메뉴 전체)."""
        # 외부 이미지가 있으면 해당 영역을 잘라서 사용
        if self.lab_bg is not None:
            bg_w, bg_h = self.lab_bg.get_size()
            # rect가 이미지 범위 안이면 subsurface로 복사, 아니면 스케일
            if (0 <= rect.x and 0 <= rect.y and
                    rect.right <= bg_w and rect.bottom <= bg_h):
                sub = self.lab_bg.subsurface(rect)
                self.screen.blit(sub, (rect.x, rect.y))
            else:
                scaled = pygame.transform.scale(self.lab_bg,
                                                (rect.width, rect.height))
                self.screen.blit(scaled, (rect.x, rect.y))
            # 상태 LED만 이미지 위에 덧칠 (살아있는 느낌)
            self._draw_lab_wall_leds(rect)
            return

        # 코드 생성 기본 패턴
        pygame.draw.rect(self.screen, LAB_WALL_A, rect)

        # 패널 그리드 (가로 3×세로 2)
        pcols = 3
        prows = 2
        pw = rect.width  // pcols
        ph = rect.height // prows
        for i in range(1, pcols):
            x = rect.x + i * pw
            pygame.draw.line(self.screen, LAB_WALL_B, (x, rect.y + 2),
                             (x, rect.bottom - 2), 2)
            pygame.draw.line(self.screen, LAB_PANEL_HL, (x + 1, rect.y + 2),
                             (x + 1, rect.bottom - 10), 1)
        for j in range(1, prows):
            y = rect.y + j * ph
            pygame.draw.line(self.screen, LAB_WALL_B, (rect.x + 2, y),
                             (rect.right - 2, y), 2)
            pygame.draw.line(self.screen, LAB_PANEL_HL, (rect.x + 2, y + 1),
                             (rect.right - 10, y + 1), 1)

        # 패널 리벳 (네 귀퉁이)
        for i in range(pcols):
            for j in range(prows):
                px = rect.x + i * pw
                py = rect.y + j * ph
                for cx, cy in ((px + 6, py + 6),
                               (px + pw - 6, py + 6),
                               (px + 6, py + ph - 6),
                               (px + pw - 6, py + ph - 6)):
                    pygame.draw.circle(self.screen, LAB_PANEL_HL, (cx, cy), 2)
                    pygame.draw.circle(self.screen, (20, 24, 32), (cx, cy), 1)

        # 상단 위험 스트라이프
        stripe_h = 8
        stripe_y = rect.y
        sw = 18
        for i, sx in enumerate(range(rect.x - sw, rect.right + sw, sw)):
            col = LAB_HAZARD_Y if i % 2 == 0 else LAB_HAZARD_K
            pts = [(sx, stripe_y),
                   (sx + sw, stripe_y),
                   (sx + sw - stripe_h, stripe_y + stripe_h),
                   (sx - stripe_h, stripe_y + stripe_h)]
            pygame.draw.polygon(self.screen, col, pts)
        pygame.draw.line(self.screen, (10, 10, 10),
                         (rect.x, stripe_y + stripe_h),
                         (rect.right, stripe_y + stripe_h), 1)

        # 상태 LED + 환풍구 (외부 이미지에도 덧칠되는 살아있는 요소)
        self._draw_lab_wall_leds(rect)

    def _draw_lab_wall_leds(self, rect):
        """실험실 벽의 LED 맥동 + 환풍구만 별도 렌더 (이미지 배경 위에도 덧그림)."""
        t = pygame.time.get_ticks() * 0.003
        leds = [
            (rect.x + 10, rect.bottom - 14, LED_GREEN, 0.0),
            (rect.x + 26, rect.bottom - 14, LED_AMBER, 1.0),
            (rect.x + 42, rect.bottom - 14, LED_RED,   2.0),
        ]
        for cx, cy, col, phase in leds:
            pulse = 0.4 + 0.6 * abs(math.sin(t + phase))
            glow = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, int(120 * pulse)), (8, 8), 8)
            self.screen.blit(glow, (cx - 8, cy - 8))
            pygame.draw.circle(self.screen, col, (cx, cy), 3)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (cx - 1, cy - 1), 1)

        # 배기 격자
        vent_x, vent_y = rect.x + 70, rect.bottom - 22
        pygame.draw.rect(self.screen, (22, 26, 34), (vent_x, vent_y, 44, 14), border_radius=2)
        for i in range(5):
            yy = vent_y + 3 + i * 2
            pygame.draw.line(self.screen, LAB_PANEL_HL,
                             (vent_x + 3, yy), (vent_x + 41, yy), 1)

    def _draw_lab_bench(self):
        """화면 최하단 실험실 콘솔 벤치 — 금속 상판 + 버튼/다이얼/키."""
        y = PLAY_BOTTOM
        h = BENCH_HEIGHT
        w = WINDOW_WIDTH
        sx, sy = int(self.shake_x), int(self.shake_y)

        # 상판 금속 (그라데이션)
        for i in range(h):
            t = i / h
            r = int(LAB_METAL[0] * (1 - t) + LAB_METAL_D[0] * t)
            g = int(LAB_METAL[1] * (1 - t) + LAB_METAL_D[1] * t)
            b = int(LAB_METAL[2] * (1 - t) + LAB_METAL_D[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (sx, y + i + sy),
                             (w + sx, y + i + sy))

        # 상판 엣지 하이라이트
        pygame.draw.line(self.screen, (180, 190, 205),
                         (sx, y + sy), (w + sx, y + sy), 1)
        pygame.draw.line(self.screen, (25, 30, 40),
                         (sx, y + 3 + sy), (w + sx, y + 3 + sy), 1)

        # 빨강/노랑/초록 큰 버튼 3개
        btn_y = y + h // 2 + sy + 2
        for i, col in enumerate([LED_RED, LED_AMBER, LED_GREEN]):
            cx = 24 + i * 28 + sx
            pygame.draw.circle(self.screen, (25, 28, 35), (cx, btn_y + 2), 9)
            pygame.draw.circle(self.screen, col, (cx, btn_y), 8)
            pygame.draw.circle(self.screen,
                               (min(255, col[0] + 60), min(255, col[1] + 60), min(255, col[2] + 60)),
                               (cx - 2, btn_y - 2), 3)
            pygame.draw.circle(self.screen, (15, 15, 15), (cx, btn_y), 8, 1)

        # 다이얼 2개 (가운데)
        t = pygame.time.get_ticks() * 0.0015
        for i in range(2):
            dx = 130 + i * 40 + sx
            dy = y + h // 2 + sy + 2
            pygame.draw.circle(self.screen, (28, 32, 40), (dx, dy), 11)
            pygame.draw.circle(self.screen, (160, 170, 185), (dx, dy), 10, 1)
            angle = (math.sin(t + i * 0.7) * 2.0 - math.pi / 2)
            nx = dx + int(math.cos(angle) * 7)
            ny = dy + int(math.sin(angle) * 7)
            pygame.draw.line(self.screen, LED_AMBER, (dx, dy), (nx, ny), 2)
            pygame.draw.circle(self.screen, (40, 40, 50), (dx, dy), 2)

        # 7-세그먼트 스타일 디스플레이 (점수 미러)
        disp_x = 220 + sx
        disp_y = y + 8 + sy
        pygame.draw.rect(self.screen, (10, 20, 10),
                         (disp_x, disp_y, 90, 26), border_radius=2)
        pygame.draw.rect(self.screen, (60, 100, 60),
                         (disp_x, disp_y, 90, 26), 1, border_radius=2)
        seg_font = pygame.font.SysFont("consolas", 20, bold=True)
        score_val = self.snake.score if self.state == self.S_PLAY else 0
        seg_text = seg_font.render(f"{score_val:>5}", True, (120, 255, 140))
        self.screen.blit(seg_text, (disp_x + 8, disp_y + 4))

        # 키패드 (작은 사각 4×2)
        kx0, ky0 = 330 + sx, y + 8 + sy
        for r in range(2):
            for c in range(4):
                rx = kx0 + c * 18
                ry = ky0 + r * 14
                pygame.draw.rect(self.screen, (45, 50, 62), (rx, ry, 14, 10), border_radius=2)
                pygame.draw.rect(self.screen, (90, 100, 120), (rx, ry, 14, 10), 1, border_radius=2)

        # 우측 깜빡이는 "REC" LED
        rec_x, rec_y = w - 18 + sx, y + 10 + sy
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink:
            pygame.draw.circle(self.screen, LED_RED, (rec_x, rec_y), 4)
        else:
            pygame.draw.circle(self.screen, (80, 20, 20), (rec_x, rec_y), 4)
        rec_txt = self.fnt_sm.render("REC", True, (220, 220, 220))
        self.screen.blit(rec_txt, (rec_x - 32, rec_y - 6))

    def _draw_lab_clamps(self):
        """플라스크 좌우를 붙잡고 있는 실험실 클램프(고정대)."""
        gy = HUD_HEIGHT
        gh = CELL_SIZE * GRID_HEIGHT
        sx, sy = int(self.shake_x), int(self.shake_y)
        clamp_y = gy + gh // 2 + sy

        # 폴 세로 길이 (클램프 아래~벤치까지)
        pole_top = clamp_y
        pole_h   = PLAY_BOTTOM - pole_top - 1

        # 좌측 클램프
        pygame.draw.rect(self.screen, (80, 85, 95),
                         (3 + sx, pole_top, 4, pole_h))
        pygame.draw.rect(self.screen, (150, 160, 175),
                         (3 + sx, pole_top, 1, pole_h))
        pygame.draw.rect(self.screen, (90, 95, 105), (3 + sx, clamp_y - 6, 20, 12), border_radius=3)
        pygame.draw.rect(self.screen, (40, 42, 50), (3 + sx, clamp_y - 6, 20, 12), 1, border_radius=3)
        pygame.draw.circle(self.screen, (200, 170, 60), (13 + sx, clamp_y), 3)
        pygame.draw.circle(self.screen, (20, 20, 20), (13 + sx, clamp_y), 3, 1)
        pygame.draw.line(self.screen, (20, 20, 20),
                         (11 + sx, clamp_y), (15 + sx, clamp_y), 1)

        # 우측 클램프 (미러)
        rx = WINDOW_WIDTH - 7 + sx
        pygame.draw.rect(self.screen, (80, 85, 95),
                         (rx, pole_top, 4, pole_h))
        pygame.draw.rect(self.screen, (150, 160, 175),
                         (rx, pole_top, 1, pole_h))
        pygame.draw.rect(self.screen, (90, 95, 105),
                         (rx - 19, clamp_y - 6, 20, 12), border_radius=3)
        pygame.draw.rect(self.screen, (40, 42, 50),
                         (rx - 19, clamp_y - 6, 20, 12), 1, border_radius=3)
        pygame.draw.circle(self.screen, (200, 170, 60), (rx - 9, clamp_y), 3)
        pygame.draw.circle(self.screen, (20, 20, 20), (rx - 9, clamp_y), 3, 1)
        pygame.draw.line(self.screen, (20, 20, 20),
                         (rx - 11, clamp_y), (rx - 7, clamp_y), 1)

    def _gr(self, gx, gy, shrink=2):
        return pygame.Rect(
            gx*CELL_SIZE + shrink + int(self.shake_x),
            gy*CELL_SIZE + shrink + HUD_HEIGHT + int(self.shake_y),
            CELL_SIZE - shrink*2,
            CELL_SIZE - shrink*2)

    def _draw_bg_particles(self):
        """배경에 떠다니는 실험실 약 입자"""
        for bp in self._bg_particles:
            surf = pygame.Surface((int(bp['size']*2), int(bp['size']*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*bp['color'], bp['alpha']),
                               (int(bp['size']), int(bp['size'])), int(bp['size']))
            self.screen.blit(surf, (int(bp['x']), int(bp['y'])))

    def _draw_flask_background(self):
        """플라스크 내부 배경 — 흰색 바닥 + 둥근 하단"""
        gy = HUD_HEIGHT
        gw = WINDOW_WIDTH
        gh = CELL_SIZE * GRID_HEIGHT

        # 플라스크 내부 전체를 밝은 색으로 채우기
        flask_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)

        # 메인 내부 (거의 흰색)
        pygame.draw.rect(flask_surf, FLASK_INSIDE, (0, 0, gw, gh))

        # 바닥 부분 둥글게 + 약간 더 어두운 색
        bottom_h = 30
        pygame.draw.ellipse(flask_surf, FLASK_FLOOR,
                            (-10, gh - bottom_h, gw + 20, bottom_h * 2))

        # 바닥에 미세한 그라디언트 (아래로 갈수록 살짝 어두움)
        for i in range(15):
            alpha = int(8 - i * 0.5)
            if alpha <= 0: break
            y = gh - 15 + i
            pygame.draw.line(flask_surf, (200, 205, 215, alpha), (0, y), (gw, y))

        # 액체 느낌 — 하단에 살짝 초록 빛 (약 성분)
        liquid_surf = pygame.Surface((gw, 20), pygame.SRCALPHA)
        for i in range(20):
            alpha = int(15 - i * 0.7)
            if alpha <= 0: break
            pygame.draw.line(liquid_surf, (120, 220, 140, alpha), (0, 19 - i), (gw, 19 - i))
        flask_surf.blit(liquid_surf, (0, gh - 20))

        self.screen.blit(flask_surf, (0, gy))

    def _draw_flask_border(self):
        """플라스크 유리 테두리 — 둥근 바닥 + 좁은 목"""
        gy = HUD_HEIGHT
        gw = WINDOW_WIDTH
        gh = CELL_SIZE * GRID_HEIGHT
        sx, sy = int(self.shake_x), int(self.shake_y)

        border_surf = pygame.Surface((gw + 40, gh + 60), pygame.SRCALPHA)
        ox, oy = 20, 10  # 오프셋 (넓은 서피스 안에서 그리기)

        # ─── 플라스크 목 (상단, 좁은 부분) ───
        neck_w = gw // 3
        neck_h = 18
        neck_x = ox + gw // 2 - neck_w // 2
        # 목 좌우 벽
        for i in range(3):
            a = max(0, 100 - i * 25)
            pygame.draw.line(border_surf, (FLASK_EDGE[0], FLASK_EDGE[1], FLASK_EDGE[2], a),
                             (neck_x - i, oy), (neck_x - i, oy + neck_h))
            pygame.draw.line(border_surf, (FLASK_EDGE[0], FLASK_EDGE[1], FLASK_EDGE[2], a),
                             (neck_x + neck_w + i, oy), (neck_x + neck_w + i, oy + neck_h))
        # 목 상단 가로선 (뚜껑 없음 — 열린 플라스크)
        pygame.draw.line(border_surf, (*FLASK_EDGE, 120),
                         (neck_x, oy), (neck_x + neck_w, oy), 2)

        # ─── 목 → 몸통 연결 (어깨, 곡선) ───
        # 왼쪽 어깨
        for t_i in range(10):
            t = t_i / 9.0
            x1 = neck_x + int((ox - neck_x) * t)
            y1 = oy + neck_h + int((25) * t)
            pygame.draw.circle(border_surf, (*FLASK_EDGE, 90), (x1, y1), 2)
        # 오른쪽 어깨
        for t_i in range(10):
            t = t_i / 9.0
            x1 = neck_x + neck_w + int((ox + gw - neck_x - neck_w) * t)
            y1 = oy + neck_h + int((25) * t)
            pygame.draw.circle(border_surf, (*FLASK_EDGE, 90), (x1, y1), 2)

        # ─── 몸통 좌우 벽 ───
        body_top = oy + neck_h + 25
        body_bot = oy + gh - 15
        for i in range(4):
            a = max(0, 110 - i * 25)
            pygame.draw.line(border_surf, (*FLASK_EDGE, a),
                             (ox - i, body_top), (ox - i, body_bot))
            pygame.draw.line(border_surf, (*FLASK_EDGE, a),
                             (ox + gw + i, body_top), (ox + gw + i, body_bot))

        # ─── 둥근 바닥 ───
        pygame.draw.arc(border_surf, (*FLASK_EDGE, 110),
                        (ox - 5, body_bot - 20, gw + 10, 50),
                        3.14, 6.28, 3)

        # ─── 유리 반사광 (왼쪽 상단 세로줄) ───
        for i in range(8):
            a = max(0, 50 - i * 6)
            pygame.draw.line(border_surf, (*FLASK_SHINE, a),
                             (ox + 4 + i, body_top + 5),
                             (ox + 4 + i, body_top + gh // 2))

        # ─── 유리 반사광 (오른쪽 짧은 줄) ───
        for i in range(5):
            a = max(0, 30 - i * 5)
            pygame.draw.line(border_surf, (*FLASK_SHINE, a),
                             (ox + gw - 6 - i, body_bot - 60),
                             (ox + gw - 6 - i, body_bot - 20))

        self.screen.blit(border_surf, (-20 + sx, gy - 10 + sy))

    def _draw_hud(self):
        # 평범한 검정 배경 → 실험실 벽면 패널
        self._draw_lab_wall(pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT))
        # HUD 하단 경계 — 벤치 상판처럼 두꺼운 금속 라인
        pygame.draw.line(self.screen, (140, 150, 170),
                         (0, HUD_HEIGHT - 1), (WINDOW_WIDTH, HUD_HEIGHT - 1), 2)
        pygame.draw.line(self.screen, (20, 24, 32),
                         (0, HUD_HEIGHT + 1), (WINDOW_WIDTH, HUD_HEIGHT + 1), 1)

        # 점수 (글로우 효과)
        score_text = f"점수  {self.snake.score}"
        glow_surf = self.fnt_lg.render(score_text, True, (100, 255, 100))
        glow_surf.set_alpha(40)
        self.screen.blit(glow_surf, (12, 10))
        self.screen.blit(self.fnt_lg.render(score_text, True, WHITE), (10, 8))

        self.screen.blit(self.fnt_sm.render(
            f"속도 {self.snake.speed:.1f}  길이 {len(self.snake.body)}", True, (160,160,200)), (10, 42))
        self.screen.blit(self.fnt_sm.render(f"최고 {self.high_score}", True, GOLD), (WINDOW_WIDTH-110, 8))

        # 채우기 바
        bx, by, bw, bh = WINDOW_WIDTH//2 - 70, 8, 140, 16
        ratio = self.fill_ratio()
        pygame.draw.rect(self.screen, (30, 30, 50), (bx, by, bw, bh), border_radius=6)
        r = int(50 + 205*(ratio/0.5)) if ratio < 0.5 else 255
        g = 200 if ratio < 0.5 else int(200*(1-(ratio-0.5)/0.5))
        fw = int(bw*ratio)
        if fw > 0:
            bar_surf = pygame.Surface((fw, bh), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (r, g, 50), (0, 0, fw, bh), border_radius=6)
            pygame.draw.rect(bar_surf, (min(255, r+40), min(255, g+40), 80, 80),
                             (0, 0, fw, bh//2), border_radius=6)
            self.screen.blit(bar_surf, (bx, by))
        pygame.draw.rect(self.screen, (100,100,140), (bx, by, bw, bh), 1, border_radius=6)
        pct = self.fnt_sm.render(f"{int(ratio*100)}%  채우기", True, WHITE)
        self.screen.blit(pct, (bx + bw//2 - pct.get_width()//2, by + 1))

        # 효과 바
        ex, ey = WINDOW_WIDTH//2 - 55, 30
        cmap = {"speed_up": RED, "slow_down": BLUE, "wall_pass": PURPLE}
        lmap = {"speed_up": "속도UP", "slow_down": "속도DN", "wall_pass": "벽통과"}
        for e in self.snake.effects:
            col = cmap.get(e.name, WHITE); lbl = lmap.get(e.name, e.name)
            w = int(110 * e.timer / e.duration)
            pygame.draw.rect(self.screen, (30, 30, 48), (ex, ey, 110, 13), border_radius=4)
            if w > 0:
                eff_surf = pygame.Surface((w, 13), pygame.SRCALPHA)
                pygame.draw.rect(eff_surf, (*col, 180), (0, 0, w, 13), border_radius=4)
                self.screen.blit(eff_surf, (ex, ey))
            self.screen.blit(self.fnt_sm.render(f"{lbl} {e.timer//FPS}s", True, WHITE), (ex+3, ey))
            ey += 16

        # 사과 범례 (HUD 하단)
        self._draw_hud_legend()
        # 목숨 아이콘
        self._draw_lives()

    def _draw_lives(self):
        """HUD 우상단 — '최고' 점수 아래에 목숨 하트 3개."""
        base_x = WINDOW_WIDTH - 80
        base_y = 28
        for i in range(3):
            cx = base_x + i * 22
            cy = base_y
            alive = i < self.lives
            # 무적 중이면 남은 목숨 맥동
            if alive and self.iframe_timer > 0:
                pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() * 0.02))
                col = (255, int(60 + 100 * pulse), int(80 + 100 * pulse))
            elif alive:
                col = (230, 60, 90)
            else:
                col = (70, 40, 50)
            # 하트 = 두 원 + 삼각형
            pygame.draw.circle(self.screen, col, (cx - 4, cy), 5)
            pygame.draw.circle(self.screen, col, (cx + 4, cy), 5)
            pts = [(cx - 8, cy + 2), (cx + 8, cy + 2), (cx, cy + 10)]
            pygame.draw.polygon(self.screen, col, pts)
            if not alive:
                # 잃은 목숨 — 대각선 슬래시
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (cx - 8, cy - 6), (cx + 8, cy + 10), 1)

    def _draw_hud_legend(self):
        """HUD 하단에 알약 범례 표시"""
        y_base = 62
        items = [
            ("초록", GREEN_APPLE, "+1 성장"),
            ("빨강", RED,        "속도UP 5s"),
            ("파랑", BLUE,       "속도DN 5s"),
            ("황금", GOLD,       "몸통절단→장애물"),
            ("무지개", None,     "방향반전"),
            ("보라", PURPLE,     "벽통과 5s"),
            ("무기", WEAPON_COL, "포탑 영구·마우스조준"),
        ]
        col1_x = 10
        col2_x = WINDOW_WIDTH // 2 + 5
        for i, (name, color, desc) in enumerate(items):
            x = col1_x if i < 4 else col2_x
            y = y_base + (i if i < 4 else i - 4) * 32

            if color is None:
                rc = RAINBOW_CYCLE[(pygame.time.get_ticks() // 80) % len(RAINBOW_CYCLE)]
                pygame.draw.circle(self.screen, rc, (x + 8, y + 8), 6)
            else:
                pygame.draw.circle(self.screen, color, (x + 8, y + 8), 6)
            pygame.draw.circle(self.screen, (255, 255, 255), (x + 6, y + 5), 2)
            self.screen.blit(self.fnt_sm.render(f"{name}: {desc}", True, (180, 180, 200)),
                             (x + 18, y))

    def _draw_grid(self):
        """교차점에 작은 점으로 그리드 표시"""
        for x in range(0, WINDOW_WIDTH + 1, CELL_SIZE):
            for y in range(HUD_HEIGHT, WINDOW_HEIGHT + 1, CELL_SIZE):
                px = x + int(self.shake_x)
                py = y + int(self.shake_y)
                pygame.draw.circle(self.screen, (30, 34, 55), (px, py), 1)

    def _draw_obstacles(self):
        for gx, gy in self.obstacles:
            r = self._gr(gx, gy, 1)
            if self.obstacle_img:
                self.screen.blit(self.obstacle_img, (r.x, r.y))
            else:
                pygame.draw.rect(self.screen, OBSTACLE, r, border_radius=4)
                pygame.draw.rect(self.screen, OBSTACLE_B, r, 2, border_radius=4)
                mx, my = r.centerx, r.centery; s = 5
                pygame.draw.line(self.screen, (70, 50, 30), (mx-s,my-s),(mx+s,my+s), 2)
                pygame.draw.line(self.screen, (70, 50, 30), (mx+s,my-s),(mx-s,my+s), 2)

    def _draw_apple(self):
        """알약(캡슐) 렌더링 — 파이썬 코드로 생성한 스프라이트 사용."""
        gx, gy = self.apple.pos; col = self.apple.color()
        r = self._gr(gx, gy, 1)

        # 글로우
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
        glow_size = int(6 + 4 * pulse)
        glow_surf = pygame.Surface((r.w + glow_size*2, r.h + glow_size*2), pygame.SRCALPHA)
        glow_alpha = int(40 + 30 * pulse)
        pygame.draw.ellipse(glow_surf, (*col[:3], glow_alpha),
                            (0, 0, r.w + glow_size*2, r.h + glow_size*2))
        self.screen.blit(glow_surf, (r.x - glow_size, r.y - glow_size))

        # 바운스
        bounce = int(2 * math.sin(pygame.time.get_ticks() * 0.004))

        # 무지개 알약: 매 프레임 색 순환, 나머지는 캐시된 Surface 사용
        if self.apple.atype == A_RAIN:
            rainbow_idx = (pygame.time.get_ticks() // 80) % len(RAINBOW_CYCLE)
            img = make_pill_surface(A_RAIN, self.pill_size, rainbow_idx)
        else:
            img = self.pill_images.get(self.apple.atype)

        if img:
            self.screen.blit(img, (r.x, r.y + bounce))

    def _draw_snake_connector(self, gx1, gy1, gx2, gy2, col):
        """인접한 두 몸통 사이를 연결하는 브릿지"""
        dx = gx2 - gx1; dy = gy2 - gy1
        if abs(dx) > 1 or abs(dy) > 1:
            return
        sx = int(self.shake_x); sy = int(self.shake_y)
        if dx != 0:
            x = min(gx1, gx2) * CELL_SIZE + CELL_SIZE - 1 + sx
            y = min(gy1, gy2) * CELL_SIZE + 3 + HUD_HEIGHT + sy
            pygame.draw.rect(self.screen, col, (x, y, 4, CELL_SIZE - 6), border_radius=2)
        elif dy != 0:
            x = min(gx1, gx2) * CELL_SIZE + 3 + sx
            y = min(gy1, gy2) * CELL_SIZE + CELL_SIZE - 1 + HUD_HEIGHT + sy
            pygame.draw.rect(self.screen, col, (x, y, CELL_SIZE - 6, 4), border_radius=2)

    def _draw_snake(self):
        # 무적 프레임 동안은 10Hz 주기로 깜빡이며 한 프레임 건너뜀
        if self.iframe_timer > 0:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return
        n = len(self.snake.body); wp = self.snake.wall_pass

        # 1단계: 몸통 연결선 먼저 그리기
        for i in range(len(self.snake.body) - 1):
            gx1, gy1 = self.snake.body[i]
            gx2, gy2 = self.snake.body[i+1]
            t = i / max(n-1, 1)
            if wp:
                conn_col = (int(WALL_PASS_COL[0]*(1-t)+60*t),
                            int(WALL_PASS_COL[1]*(1-t)+20*t),
                            int(WALL_PASS_COL[2]*(1-t)+80*t))
            else:
                conn_col = (int(HEAD_COL[0]*(1-t)+BODY_DARK[0]*t),
                            int(HEAD_COL[1]*(1-t)+BODY_DARK[1]*t),
                            int(HEAD_COL[2]*(1-t)+BODY_DARK[2]*t))
            self._draw_snake_connector(gx1, gy1, gx2, gy2, conn_col)

        # 2단계: 몸통 셀 그리기 (뒤에서부터)
        for i, (gx, gy) in enumerate(reversed(self.snake.body)):
            idx = n - 1 - i
            r = self._gr(gx, gy, 1)

            if idx == 0:
                col = WALL_PASS_COL if wp else HEAD_COL

                # 머리 글로우
                glow_surf = pygame.Surface((r.w + 16, r.h + 16), pygame.SRCALPHA)
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.004))
                glow_alpha = int(35 + 30 * pulse)
                pygame.draw.ellipse(glow_surf, (*col, glow_alpha),
                                    (0, 0, r.w + 16, r.h + 16))
                self.screen.blit(glow_surf, (r.x - 8, r.y - 8))

                # 머리 본체 (스프라이트 or fallback)
                head_img = self.head_images.get(self.snake.direction) if not wp else None
                if head_img:
                    self.screen.blit(head_img, (r.x, r.y))
                else:
                    pygame.draw.rect(self.screen, col, r, border_radius=8)
                    # 머리 하이라이트
                    hl_r = pygame.Rect(r.x + 3, r.y + 2, r.w - 6, r.h // 2 - 1)
                    hl_surf = pygame.Surface((hl_r.w, hl_r.h), pygame.SRCALPHA)
                    lighter = (min(255, col[0]+60), min(255, col[1]+60), min(255, col[2]+60), 70)
                    pygame.draw.rect(hl_surf, lighter, (0, 0, hl_r.w, hl_r.h), border_radius=5)
                    self.screen.blit(hl_surf, (hl_r.x, hl_r.y))

                # 눈
                d = self.snake.direction
                ssx = int(self.shake_x); ssy = int(self.shake_y)
                cx = gx * CELL_SIZE + CELL_SIZE // 2 + ssx
                cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT + ssy

                if d == RIGHT:
                    eyes = [(cx + 5, cy - 5), (cx + 5, cy + 5)]
                elif d == LEFT:
                    eyes = [(cx - 5, cy - 5), (cx - 5, cy + 5)]
                elif d == UP:
                    eyes = [(cx - 5, cy - 5), (cx + 5, cy - 5)]
                else:
                    eyes = [(cx - 5, cy + 5), (cx + 5, cy + 5)]

                for exx, eyy in eyes:
                    pygame.draw.circle(self.screen, WHITE, (exx, eyy), 4)
                    ddx, ddy = d
                    pygame.draw.circle(self.screen, (15, 15, 15),
                                       (exx + ddx, eyy + ddy), 2)

                # 혀
                tongue_show = (pygame.time.get_ticks() // 300) % 3 == 0
                if tongue_show:
                    ddx, ddy = d
                    tx = cx + ddx * (CELL_SIZE // 2 + 2)
                    ty = cy + ddy * (CELL_SIZE // 2 + 2)
                    pygame.draw.line(self.screen, RED, (cx + ddx * 11, cy + ddy * 11),
                                     (tx, ty), 2)
                    if ddx != 0:
                        pygame.draw.line(self.screen, RED, (tx, ty), (tx + ddx*3, ty - 2), 1)
                        pygame.draw.line(self.screen, RED, (tx, ty), (tx + ddx*3, ty + 2), 1)
                    else:
                        pygame.draw.line(self.screen, RED, (tx, ty), (tx - 2, ty + ddy*3), 1)
                        pygame.draw.line(self.screen, RED, (tx, ty), (tx + 2, ty + ddy*3), 1)

            else:
                t = idx / max(n-1, 1)
                if wp:
                    col = (int(WALL_PASS_COL[0]*(1-t)+60*t),
                           int(WALL_PASS_COL[1]*(1-t)+20*t),
                           int(WALL_PASS_COL[2]*(1-t)+80*t))
                else:
                    col = (int(HEAD_COL[0]*(1-t)+BODY_DARK[0]*t),
                           int(HEAD_COL[1]*(1-t)+BODY_DARK[1]*t),
                           int(HEAD_COL[2]*(1-t)+BODY_DARK[2]*t))

                pygame.draw.rect(self.screen, col, r, border_radius=6)

                # 비늘 패턴
                if idx % 2 == 0:
                    scale_col = (max(0, col[0]-25), max(0, col[1]-25), max(0, col[2]-25))
                    inner = pygame.Rect(r.x + 3, r.y + 3, r.w - 6, r.h - 6)
                    pygame.draw.rect(self.screen, scale_col, inner, 1, border_radius=3)

                # 몸통 하이라이트
                hl = pygame.Surface((r.w - 4, r.h//3), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 25), (0, 0, r.w - 4, r.h//3),
                                 border_radius=4)
                self.screen.blit(hl, (r.x + 2, r.y + 1))

                # 꼬리 끝
                if idx == n - 1 and n > 3:
                    tail_shrink = 3
                    tail_r = pygame.Rect(r.x + tail_shrink, r.y + tail_shrink,
                                         r.w - tail_shrink*2, r.h - tail_shrink*2)
                    darker = (max(0, col[0]-30), max(0, col[1]-30), max(0, col[2]-30))
                    pygame.draw.rect(self.screen, darker, tail_r, border_radius=8)

    def _draw_msgs(self):
        for m in self.msgs:
            s = self.fnt_md.render(m.text, True, m.color)
            s.set_alpha(m.alpha())
            self.screen.blit(s, (int(m.x)-s.get_width()//2, int(m.y)))

    def _draw_menu(self):
        self.menu_tick += 1
        # 메뉴 배경: 화면 전체에 실험실 벽 패턴
        self._draw_lab_wall(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        self._draw_bg_particles()

        # 제목 (글로우)
        title_text = "약먹은 스네이크"
        glow = self.fnt_xl.render(title_text, True, (50, 180, 50))
        glow.set_alpha(int(40 + 20 * abs(math.sin(self.menu_tick * 0.03))))
        self.screen.blit(glow, (WINDOW_WIDTH//2 - glow.get_width()//2 + 2, 40))
        title = self.fnt_xl.render(title_text, True, HEAD_COL)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 38))

        # 유리병 아이콘
        bottle_pulse = abs(math.sin(self.menu_tick * 0.02))
        bottle_alpha = int(60 + 40 * bottle_pulse)
        bottle_surf = pygame.Surface((WINDOW_WIDTH, 60), pygame.SRCALPHA)
        pygame.draw.rect(bottle_surf, (140, 180, 220, bottle_alpha),
                         (WINDOW_WIDTH//2 - 160, 0, 320, 55), border_radius=10)
        pygame.draw.rect(bottle_surf, (180, 210, 240, bottle_alpha + 20),
                         (WINDOW_WIDTH//2 - 160, 0, 320, 55), 2, border_radius=10)
        self.screen.blit(bottle_surf, (0, 28))

        story = self.fnt_sm.render("유리병 속에 갇힌 뱀. 몸을 키워 병을 가득 채우면 탈출!",
                                   True, (180, 180, 220))
        self.screen.blit(story, (WINDOW_WIDTH//2 - story.get_width()//2, 98))
        goal = self.fnt_md.render(f"맵 {TOTAL_CELLS}칸을 모두 채우면 클리어!", True, GOLD)
        self.screen.blit(goal, (WINDOW_WIDTH//2 - goal.get_width()//2, 122))

        pygame.draw.line(self.screen, (50, 50, 80), (30,152),(WINDOW_WIDTH-30,152), 1)
        line_glow = pygame.Surface((WINDOW_WIDTH - 60, 3), pygame.SRCALPHA)
        pygame.draw.rect(line_glow, (100, 150, 200, 30), (0, 0, WINDOW_WIDTH-60, 3))
        self.screen.blit(line_glow, (30, 151))

        hdr = self.fnt_sm.render("── 특수 알약 (한 번에 1개 등장) ──", True, (160,160,210))
        self.screen.blit(hdr, (WINDOW_WIDTH//2 - hdr.get_width()//2, 162))

        info = [
            ("초록","일반 성장 +1",GREEN_APPLE),
            ("빨강","속도 증가 5초",RED),
            ("파랑","속도 감소 5초",BLUE),
            ("황금","몸통 절반→장애물",GOLD),
            ("무지개","방향 180도 반전 + 사이키델릭",(200,100,255)),
            ("보라","벽 통과 5초",PURPLE),
            ("무기","머리 뒤 포탑 영구장착 — 마우스 방향 자동발사",WEAPON_COL),
        ]
        iy = 184
        for em, desc, col in info:
            icon_x = WINDOW_WIDTH//2 - 170
            if em == "무지개":
                rc = RAINBOW_CYCLE[(self.menu_tick // 5) % len(RAINBOW_CYCLE)]
                pygame.draw.circle(self.screen, rc, (icon_x, iy + 8), 5)
            else:
                pygame.draw.circle(self.screen, col, (icon_x, iy + 8), 5)
                pygame.draw.circle(self.screen, (255, 255, 255), (icon_x - 1, iy + 6), 1)
            self.screen.blit(self.fnt_sm.render(em, True, col), (icon_x + 10, iy))
            self.screen.blit(self.fnt_sm.render(desc, True, (210,210,210)),
                             (WINDOW_WIDTH//2 - 80, iy))
            iy += 23

        # 보스/목숨 안내
        boss_info = self.fnt_sm.render(
            "알약 10개 → 보스 출현  |  4방향 포위로 처치  |  목숨 ♥×3",
            True, (255, 130, 140))
        self.screen.blit(boss_info,
                         (WINDOW_WIDTH // 2 - boss_info.get_width() // 2, iy + 4))
        iy += 20

        if (pygame.time.get_ticks()//500) % 2 == 0:
            start_text = "SPACE / ENTER 로 시작"
            sg = self.fnt_md.render(start_text, True, (200, 180, 40))
            sg.set_alpha(50)
            self.screen.blit(sg, (WINDOW_WIDTH//2 - sg.get_width()//2 + 1, iy + 12))
            st = self.fnt_md.render(start_text, True, (255,230,80))
            self.screen.blit(st, (WINDOW_WIDTH//2 - st.get_width()//2, iy + 10))

    def _draw_overlay_over(self):
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155)); self.screen.blit(ov, (0,0))

        go_glow = self.fnt_xl.render("GAME OVER", True, (150, 30, 30))
        go_glow.set_alpha(60)
        self.screen.blit(go_glow, (WINDOW_WIDTH//2 - go_glow.get_width()//2 + 2,
                                    WINDOW_HEIGHT//2 - 88))
        go = self.fnt_xl.render("GAME OVER", True, RED)
        self.screen.blit(go, (WINDOW_WIDTH//2 - go.get_width()//2, WINDOW_HEIGHT//2 - 90))

        for i, (txt, col) in enumerate([
            (f"점수: {self.snake.score}", WHITE),
            (f"최고 점수: {self.high_score}", GOLD),
            (f"채우기: {int(self.fill_ratio()*100)}%  ({self.filled_cells()}/{TOTAL_CELLS}칸)",
             (180,180,180)),
        ]):
            s = self.fnt_md.render(txt, True, col)
            self.screen.blit(s, (WINDOW_WIDTH//2 - s.get_width()//2, WINDOW_HEIGHT//2 - 32 + i*30))
        hint = self.fnt_sm.render("SPACE: 재시작   ESC: 메뉴", True, (200,200,100))
        self.screen.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, WINDOW_HEIGHT//2 + 70))

    def _draw_overlay_clear(self):
        t = self.clear_timer
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((255, 255, 255, min(180, t*3)//6)); self.screen.blit(ov, (0,0))

        if t > 10:
            prog = min(1.0, (t-10)/40)
            cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
            for x1,y1,x2,y2 in self.crack_lines:
                ex2 = int(x1+(x2-x1)*prog); ey2 = int(y1+(y2-y1)*prog)
                glow_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (200, 220, 255, 40), (x1,y1),(ex2,ey2), 5)
                self.screen.blit(glow_surf, (0, 0))
                pygame.draw.line(self.screen, CRACK_COL, (x1,y1),(ex2,ey2), 2)

        if t > 35:
            a = min(255, (t-35)*8)
            title_surf = self.fnt_xl.render("탈출 성공!", True, (255,230,80))
            title_surf.set_alpha(a)
            self.screen.blit(title_surf,
                             (WINDOW_WIDTH//2-title_surf.get_width()//2, WINDOW_HEIGHT//2-80))
        if t > 45:
            a = min(255, (t-45)*6)
            for i, (txt, col) in enumerate([
                ("유리병을 가득 채워 자유를 찾았다!", WHITE),
                (f"최종 점수: {self.snake.score}", GOLD),
            ]):
                s = self.fnt_md.render(txt, True, col); s.set_alpha(a)
                self.screen.blit(s, (WINDOW_WIDTH//2-s.get_width()//2, WINDOW_HEIGHT//2-25+i*35))
        if t > 80:
            a = min(255, (t-80)*6)
            h = self.fnt_sm.render("SPACE: 다시 도전   ESC: 메뉴", True, (200,200,100))
            h.set_alpha(a)
            self.screen.blit(h, (WINDOW_WIDTH//2-h.get_width()//2, WINDOW_HEIGHT//2+60))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events(); self.update(dt); self.draw()


if __name__ == "__main__":
    Game().run()
