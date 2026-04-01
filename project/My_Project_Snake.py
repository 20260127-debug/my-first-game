"""
약먹은 스네이크 (Crazy Snake)
창의프로그래밍 업무설계 중간과제
작성자: 김도현
 
[스토리]
  유리병 속에 갇힌 뱀 '스내피'.
  병 안에는 이상한 약사과들이 가득하다.
  몸을 키워 병을 가득 채우면... 유리병이 깨지고 탈출할 수 있다!
 
[클리어 조건]
  뱀 몸통 + 장애물로 맵 전체(300칸)를 채우면 클리어!
 
[조작법]
  방향키 또는 WASD : 뱀 이동
  ESC              : 메뉴로 이동
 
[특수 사과 종류 - 한 번에 1개만 등장]
  초록 사과  : 일반 성장 (+1칸)
  빨간 사과  : 속도 증가 (5초)
  파란 사과  : 속도 감소 (5초)
  황금 사과  : 몸통 절반 절단 → 잘린 부위가 장애물로 변함
  무지개 사과: 진행 방향 반전
  보라 사과  : 벽 통과 능력 부여 (5초)
  해골 사과  : 몸통 2칸 축소
"""
 
import pygame
import random
import sys
 
pygame.init()
 
# ── 화면 / 그리드 ─────────────────────────────────────────────────────
CELL_SIZE   = 28
GRID_WIDTH  = 16          # 가로 칸 수
GRID_HEIGHT = 10          # 세로 칸 수
TOTAL_CELLS = GRID_WIDTH * GRID_HEIGHT   # 160칸
 
HUD_HEIGHT    = 64
WINDOW_WIDTH  = CELL_SIZE * GRID_WIDTH          # 448
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT + HUD_HEIGHT  # 344
FPS           = 60
 
# ── 색상 ──────────────────────────────────────────────────────────────
BG         = (14, 14, 28)
GRID_COL   = (24, 24, 44)
HUD_BG     = (8,  8,  18)
WHITE      = (255, 255, 255)
 
HEAD_COL   = (130, 255, 130)
BODY_DARK  = (22,  110,  22)
WALL_PASS_COL = (190, 80, 230)
 
RED        = (225,  60,  60)
BLUE       = ( 60, 110, 225)
GOLD       = (255, 210,   0)
PURPLE     = (175,  50, 225)
SKULL_COL  = (200, 200, 200)
GREEN_APPLE= ( 50, 200,  50)
 
OBSTACLE   = ( 95,  72,  52)
OBSTACLE_B = ( 55,  42,  28)
 
CRACK_COL  = (220, 220, 255)   # 클리어 연출 균열 색
 
# ── 사과 타입 ─────────────────────────────────────────────────────────
NORMAL  = "normal"
A_RED   = "red"
A_BLUE  = "blue"
A_GOLD  = "gold"
A_RAIN  = "rainbow"
A_PURP  = "purple"
A_SKULL = "skull"
 
APPLE_COLOR = {
    NORMAL : GREEN_APPLE,
    A_RED  : RED,
    A_BLUE : BLUE,
    A_GOLD : GOLD,
    A_PURP : PURPLE,
    A_SKULL: SKULL_COL,
    A_RAIN : None,
}
 
# 등장 가중치 (합=100)
APPLE_POOL = (
    [NORMAL]  * 35 +
    [A_RED]   * 15 +
    [A_BLUE]  * 13 +
    [A_GOLD]  * 13 +
    [A_RAIN]  * 10 +
    [A_PURP]  *  7 +
    [A_SKULL] *  7
)
 
RAINBOW_CYCLE = [
    (255, 80,  80),
    (255,165,   0),
    (255,230,   0),
    ( 80,220,  80),
    ( 80,130, 255),
    (160, 60, 220),
]
 
# ── 방향 ──────────────────────────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
 
 
# ─────────────────────────────────────────────────────────────────────
class Effect:
    def __init__(self, name, duration, delta=0):
        self.name     = name
        self.duration = duration
        self.timer    = duration
        self.delta    = delta
 
    def tick(self):
        self.timer -= 1
        return self.timer > 0
 
 
class FloatMsg:
    def __init__(self, text, color, cx, cy, life=80):
        self.text  = text
        self.color = color
        self.x     = float(cx)
        self.y     = float(cy)
        self.life  = life
        self.max_life = life
 
    def update(self):
        self.y    -= 0.8
        self.life -= 1
        return self.life > 0
 
    def alpha(self):
        return int(255 * self.life / self.max_life)
 
 
# ─────────────────────────────────────────────────────────────────────
class Apple:
    def __init__(self, pos, atype):
        self.pos   = pos
        self.atype = atype
        self._tick = 0
 
    def update(self):
        self._tick += 1
 
    def color(self):
        if self.atype == A_RAIN:
            return RAINBOW_CYCLE[(self._tick // 5) % len(RAINBOW_CYCLE)]
        return APPLE_COLOR[self.atype]
 
 
# ─────────────────────────────────────────────────────────────────────
class Snake:
    BASE_SPEED = 6
 
    def __init__(self):
        cx, cy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.body      = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.effects   = []
        self.grow      = 0
        self.alive     = True
        self.score     = 0
        self.speed_mod = 0
        self.apple_count = 0   # 먹은 사과 수 (난이도용)
 
    @property
    def head(self):
        return self.body[0]
 
    @property
    def speed(self):
        # 사과 5개마다 +0.5, 최대 12
        level_bonus = (self.apple_count // 5) * 0.5
        return max(3.0, min(12.0, self.BASE_SPEED + self.speed_mod + level_bonus))
 
    @property
    def wall_pass(self):
        return any(e.name == "wall_pass" for e in self.effects)
 
    def set_dir(self, d):
        if d != OPPOSITE[self.direction]:
            self.next_dir = d
 
    def add_effect(self, name, duration, delta=0):
        for e in self.effects:
            if e.name == name:
                e.timer = duration
                return
        self.effects.append(Effect(name, duration, delta))
        self.speed_mod += delta
 
    def tick_effects(self):
        alive = []
        for e in self.effects:
            if e.tick():
                alive.append(e)
            else:
                self.speed_mod -= e.delta
        self.effects = alive
 
    def move(self, obstacles):
        self.direction = self.next_dir
        hx, hy = self.head
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy
 
        if self.wall_pass:
            nx %= GRID_WIDTH
            ny %= GRID_HEIGHT
        else:
            if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                return False
 
        new_head = (nx, ny)
        if new_head in self.body[1:] or new_head in obstacles:
            return False
 
        self.body.insert(0, new_head)
        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()
        return True
 
    def cut_half(self):
        if len(self.body) <= 3:
            return []
        cut = len(self.body) // 2
        removed = self.body[cut:]
        self.body = self.body[:cut]
        return removed
 
    def shrink(self, n=2):
        for _ in range(n):
            if len(self.body) > 2:
                self.body.pop()
 
    def reverse(self):
        self.body.reverse()
        self.direction = OPPOSITE[self.direction]
        self.next_dir  = self.direction
 
 
# ─────────────────────────────────────────────────────────────────────
class Game:
    S_MENU  = "menu"
    S_PLAY  = "play"
    S_CLEAR = "clear"
    S_OVER  = "over"
 
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🐍 약먹은 스네이크")
        self.clock  = pygame.time.Clock()
 
        candidates = ["malgun gothic", "nanum gothic", "applegothic", "gulim", "arial"]
        font_name  = None
        for c in candidates:
            if c in [f.lower() for f in pygame.font.get_fonts()]:
                font_name = c
                break
 
        self.fnt_xl = pygame.font.SysFont(font_name, 46, bold=True)
        self.fnt_lg = pygame.font.SysFont(font_name, 30, bold=True)
        self.fnt_md = pygame.font.SysFont(font_name, 22)
        self.fnt_sm = pygame.font.SysFont(font_name, 16)
 
        self.state      = self.S_MENU
        self.snake      = Snake()
        self.apple      = None      # 사과는 항상 1개
        self.obstacles  = set()
        self.msgs       = []
        self.move_accum = 0.0
        self.high_score = 0
 
        # 클리어 연출용
        self.clear_timer  = 0
        self.crack_lines  = []   # [(x1,y1,x2,y2), ...]
 
    # ── 리셋 ────────────────────────────────────────────────────────
    def reset(self):
        self.snake      = Snake()
        self.apple      = None
        self.obstacles  = set()
        self.msgs       = []
        self.move_accum = 0.0
        self.clear_timer= 0
        self.crack_lines= []
        self._spawn_apple()
 
    # ── 채워진 칸 수 ─────────────────────────────────────────────────
    def filled_cells(self):
        return len(self.snake.body) + len(self.obstacles)
 
    def fill_ratio(self):
        return self.filled_cells() / TOTAL_CELLS
 
    # ── 사과 스폰 (1개만) ────────────────────────────────────────────
    def _spawn_apple(self):
        occ  = set(self.snake.body) | self.obstacles
        if self.apple:
            occ.add(self.apple.pos)
        free = [(x, y) for x in range(GRID_WIDTH)
                       for y in range(GRID_HEIGHT)
                       if (x, y) not in occ]
        if not free:
            return
        pos   = random.choice(free)
        atype = random.choice(APPLE_POOL)
        self.apple = Apple(pos, atype)
 
    # ── 클리어 연출 ──────────────────────────────────────────────────
    def _init_clear(self):
        self.state       = self.S_CLEAR
        self.clear_timer = 0
        self.high_score  = max(self.high_score, self.snake.score)
        # 균열선 랜덤 생성
        self.crack_lines = []
        cx = WINDOW_WIDTH  // 2
        cy = WINDOW_HEIGHT // 2
        for _ in range(18):
            angle  = random.uniform(0, 6.28)
            length = random.randint(60, 220)
            x2 = int(cx + length * __import__('math').cos(angle))
            y2 = int(cy + length * __import__('math').sin(angle))
            self.crack_lines.append((cx, cy, x2, y2))
 
    # ── 플로팅 메시지 ────────────────────────────────────────────────
    def _msg(self, text, color, gx, gy):
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + HUD_HEIGHT
        self.msgs.append(FloatMsg(text, color, cx, cy))
 
    # ── 이벤트 ──────────────────────────────────────────────────────
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if self.state == self.S_MENU:
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = self.S_PLAY
                        self.reset()
 
                elif self.state == self.S_PLAY:
                    if   k in (pygame.K_UP,    pygame.K_w): self.snake.set_dir(UP)
                    elif k in (pygame.K_DOWN,  pygame.K_s): self.snake.set_dir(DOWN)
                    elif k in (pygame.K_LEFT,  pygame.K_a): self.snake.set_dir(LEFT)
                    elif k in (pygame.K_RIGHT, pygame.K_d): self.snake.set_dir(RIGHT)
                    elif k == pygame.K_ESCAPE: self.state = self.S_MENU
 
                elif self.state in (self.S_CLEAR, self.S_OVER):
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = self.S_PLAY
                        self.reset()
                    elif k == pygame.K_ESCAPE:
                        self.state = self.S_MENU
 
    # ── 업데이트 ─────────────────────────────────────────────────────
    def update(self, dt):
        if self.state == self.S_CLEAR:
            self.clear_timer += 1
            return
 
        if self.state != self.S_PLAY:
            return
 
        self.snake.tick_effects()
 
        if self.apple:
            self.apple.update()
 
        self.msgs = [m for m in self.msgs if m.update()]
 
        self.move_accum += self.snake.speed * dt
        while self.move_accum >= 1.0:
            self.move_accum -= 1.0
            if not self.snake.move(self.obstacles):
                self.high_score = max(self.high_score, self.snake.score)
                self.state = self.S_OVER
                return
            self._check_apple()
            self._check_clear()
 
    def _check_apple(self):
        if self.apple and self.snake.head == self.apple.pos:
            self._apply(self.apple)
            self.apple = None
            self.snake.apple_count += 1
            self._spawn_apple()
 
    def _check_clear(self):
        if self.filled_cells() >= TOTAL_CELLS:
            self._init_clear()
 
    def _apply(self, a):
        t  = a.atype
        ax, ay = a.pos
 
        if t == NORMAL:
            self.snake.grow += 1
            self.snake.score += 10
            self._msg("+1 성장", GREEN_APPLE, ax, ay)
 
        elif t == A_RED:
            self.snake.grow += 1
            self.snake.score += 10
            self.snake.add_effect("speed_up", 5*FPS, delta=+3)
            self._msg("🍎 속도 UP!", RED, ax, ay)
 
        elif t == A_BLUE:
            self.snake.grow += 1
            self.snake.score += 10
            self.snake.add_effect("slow_down", 5*FPS, delta=-3)
            self._msg("🔵 속도 DOWN...", BLUE, ax, ay)
 
        elif t == A_GOLD:
            self.snake.score += 25
            cut = self.snake.cut_half()
            for seg in cut:
                self.obstacles.add(seg)
            # 장애물과 겹친 사과 제거
            if self.apple and self.apple.pos in self.obstacles:
                self.apple = None
            self._msg(f"✂️ 절단! +{len(cut)}장애물", GOLD, ax, ay)
 
        elif t == A_RAIN:
            self.snake.score += 5
            self.snake.reverse()
            self._msg("🌀 방향 반전!", (200, 100, 255), ax, ay)
 
        elif t == A_PURP:
            self.snake.grow += 1
            self.snake.score += 10
            self.snake.add_effect("wall_pass", 5*FPS)
            self._msg("💜 벽 통과!", PURPLE, ax, ay)
 
        elif t == A_SKULL:
            self.snake.score += 3
            self.snake.shrink(2)
            self._msg("💀 몸통 축소", SKULL_COL, ax, ay)
 
    # ── 그리기 ───────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(BG)
 
        if self.state == self.S_MENU:
            self._draw_menu()
        elif self.state in (self.S_PLAY, self.S_OVER, self.S_CLEAR):
            self._draw_hud()
            self._draw_grid()
            self._draw_obstacles()
            if self.apple:
                self._draw_apple()
            self._draw_snake()
            self._draw_msgs()
 
            if self.state == self.S_OVER:
                self._draw_overlay_over()
            elif self.state == self.S_CLEAR:
                self._draw_overlay_clear()
 
        pygame.display.flip()
 
    # 그리드 좌표 → 픽셀 Rect
    def _gr(self, gx, gy, shrink=2):
        return pygame.Rect(
            gx * CELL_SIZE + shrink,
            gy * CELL_SIZE + shrink + HUD_HEIGHT,
            CELL_SIZE - shrink*2,
            CELL_SIZE - shrink*2,
        )
 
    # HUD ────────────────────────────────────────────────────────────
    def _draw_hud(self):
        pygame.draw.rect(self.screen, HUD_BG, (0, 0, WINDOW_WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, (40,40,70), (0, HUD_HEIGHT), (WINDOW_WIDTH, HUD_HEIGHT), 1)
 
        # 점수
        self.screen.blit(
            self.fnt_lg.render(f"점수  {self.snake.score}", True, WHITE), (10, 8))
 
        # 속도 / 길이
        self.screen.blit(
            self.fnt_sm.render(f"속도 {self.snake.speed:.1f}  길이 {len(self.snake.body)}", True, (160,160,200)),
            (10, 42))
 
        # 최고 점수
        self.screen.blit(
            self.fnt_sm.render(f"최고 {self.high_score}", True, GOLD),
            (WINDOW_WIDTH - 110, 8))
 
        # ── 채우기 진행 바 ──────────────────────────────────────────
        bar_x, bar_y, bar_w, bar_h = WINDOW_WIDTH//2 - 70, 8, 140, 14
        ratio = self.fill_ratio()
        # 배경
        pygame.draw.rect(self.screen, (40,40,60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        # 채워진 부분 (비율에 따라 색 변화: 초록→노랑→빨강)
        if ratio < 0.5:
            r = int(50  + 205 * (ratio / 0.5))
            g = 200
        else:
            r = 255
            g = int(200 * (1 - (ratio - 0.5) / 0.5))
        bar_color = (r, g, 50)
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, bar_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, (100,100,140), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        # 텍스트
        pct = self.fnt_sm.render(f"{int(ratio*100)}%  채우기", True, WHITE)
        self.screen.blit(pct, (bar_x + bar_w//2 - pct.get_width()//2, bar_y))
 
        # 활성 효과 바
        ex, ey = WINDOW_WIDTH//2 - 55, 28
        color_map = {"speed_up": RED, "slow_down": BLUE, "wall_pass": PURPLE}
        label_map = {"speed_up": "속도UP", "slow_down": "속도DN", "wall_pass": "벽통과"}
        for e in self.snake.effects:
            col = color_map.get(e.name, WHITE)
            lbl = label_map.get(e.name, e.name)
            w   = int(110 * e.timer / e.duration)
            pygame.draw.rect(self.screen, (35,35,55), (ex, ey, 110, 12), border_radius=3)
            if w > 0:
                pygame.draw.rect(self.screen, col, (ex, ey, w, 12), border_radius=3)
            t = self.fnt_sm.render(f"{lbl} {e.timer//FPS}s", True, WHITE)
            self.screen.blit(t, (ex+2, ey-1))
            ey += 15
 
    # 격자 ────────────────────────────────────────────────────────────
    def _draw_grid(self):
        for x in range(0, WINDOW_WIDTH+1, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COL, (x, HUD_HEIGHT), (x, WINDOW_HEIGHT))
        for y in range(HUD_HEIGHT, WINDOW_HEIGHT+1, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (WINDOW_WIDTH, y))
 
    # 장애물 ──────────────────────────────────────────────────────────
    def _draw_obstacles(self):
        for gx, gy in self.obstacles:
            r = self._gr(gx, gy, 1)
            pygame.draw.rect(self.screen, OBSTACLE,   r, border_radius=3)
            pygame.draw.rect(self.screen, OBSTACLE_B, r, 2, border_radius=3)
            mx, my = r.centerx, r.centery
            s = 4
            pygame.draw.line(self.screen, OBSTACLE_B, (mx-s,my-s),(mx+s,my+s), 2)
            pygame.draw.line(self.screen, OBSTACLE_B, (mx+s,my-s),(mx-s,my+s), 2)
 
    # 사과 (1개) ──────────────────────────────────────────────────────
    def _draw_apple(self):
        gx, gy = self.apple.pos
        col = self.apple.color()
        r   = self._gr(gx, gy, 3)
        pygame.draw.ellipse(self.screen, col, r)
        shine = pygame.Rect(r.x + r.w//4, r.y+2, r.w//3, r.h//4)
        pygame.draw.ellipse(self.screen, WHITE, shine)
 
    # 뱀 ──────────────────────────────────────────────────────────────
    def _draw_snake(self):
        n  = len(self.snake.body)
        wp = self.snake.wall_pass
        for i, (gx, gy) in enumerate(self.snake.body):
            r = self._gr(gx, gy, 1)
            if i == 0:
                col = WALL_PASS_COL if wp else HEAD_COL
            else:
                t = i / max(n-1, 1)
                if wp:
                    col = (
                        int(WALL_PASS_COL[0]*(1-t) + 60*t),
                        int(WALL_PASS_COL[1]*(1-t) + 20*t),
                        int(WALL_PASS_COL[2]*(1-t) + 80*t),
                    )
                else:
                    col = (
                        int(HEAD_COL[0]*(1-t) + BODY_DARK[0]*t),
                        int(HEAD_COL[1]*(1-t) + BODY_DARK[1]*t),
                        int(HEAD_COL[2]*(1-t) + BODY_DARK[2]*t),
                    )
            pygame.draw.rect(self.screen, col, r, border_radius=5)
 
            if i == 0:
                e_off = {
                    RIGHT: ((17,5),(17,16)), LEFT: ((4,5),(4,16)),
                    UP:    ((5,4),(16, 4)), DOWN: ((5,18),(16,18)),
                }
                for ex2, ey2 in e_off.get(self.snake.direction, []):
                    pygame.draw.circle(self.screen, WHITE,
                        (gx*CELL_SIZE+ex2, gy*CELL_SIZE+ey2+HUD_HEIGHT), 3)
 
    # 플로팅 메시지 ───────────────────────────────────────────────────
    def _draw_msgs(self):
        for m in self.msgs:
            s = self.fnt_md.render(m.text, True, m.color)
            s.set_alpha(m.alpha())
            self.screen.blit(s, (int(m.x)-s.get_width()//2, int(m.y)))
 
    # 메뉴 ────────────────────────────────────────────────────────────
    def _draw_menu(self):
        title = self.fnt_xl.render("🐍 약먹은 스네이크", True, HEAD_COL)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 38))
 
        story = self.fnt_sm.render(
            "유리병 속에 갇힌 뱀. 몸을 키워 병을 가득 채우면 탈출할 수 있다!", True, (180,180,220))
        self.screen.blit(story, (WINDOW_WIDTH//2 - story.get_width()//2, 95))
 
        # 채우기 조건 강조
        goal = self.fnt_md.render(f"▶  맵 {TOTAL_CELLS}칸을 모두 채우면 클리어!", True, GOLD)
        self.screen.blit(goal, (WINDOW_WIDTH//2 - goal.get_width()//2, 122))
 
        # 구분선
        pygame.draw.line(self.screen, (50,50,80),
                         (30, 156), (WINDOW_WIDTH-30, 156), 1)
 
        # 사과 목록
        hdr = self.fnt_sm.render("── 특수 사과 (한 번에 1개 등장) ──", True, (160,160,210))
        self.screen.blit(hdr, (WINDOW_WIDTH//2 - hdr.get_width()//2, 164))
 
        info = [
            ("🍏 초록", "일반 성장 +1",          GREEN_APPLE),
            ("🍎 빨강", "속도 증가 5초",          RED),
            ("🔵 파랑", "속도 감소 5초",          BLUE),
            ("✂  황금", "몸통 절반 → 장애물",     GOLD),
            ("🌀 무지개","방향 180° 반전",         (200,100,255)),
            ("💜 보라", "벽 통과 5초",            PURPLE),
            ("💀 해골", "몸통 2칸 축소",          SKULL_COL),
        ]
        iy = 188
        for em, desc, col in info:
            nm = self.fnt_sm.render(em,   True, col)
            dc = self.fnt_sm.render(desc, True, (210,210,210))
            self.screen.blit(nm, (WINDOW_WIDTH//2 - 160, iy))
            self.screen.blit(dc, (WINDOW_WIDTH//2 - 50,  iy))
            iy += 24
 
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            st = self.fnt_md.render("SPACE / ENTER 로 시작", True, (255,230,80))
            self.screen.blit(st, (WINDOW_WIDTH//2 - st.get_width()//2, iy+10))
 
    # 게임 오버 오버레이 ──────────────────────────────────────────────
    def _draw_overlay_over(self):
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        self.screen.blit(ov, (0,0))
 
        go = self.fnt_xl.render("GAME OVER", True, RED)
        self.screen.blit(go, (WINDOW_WIDTH//2 - go.get_width()//2, WINDOW_HEIGHT//2 - 90))
 
        for i, (txt, col) in enumerate([
            (f"점수: {self.snake.score}", WHITE),
            (f"최고 점수: {self.high_score}", GOLD),
            (f"채우기: {int(self.fill_ratio()*100)}%  ({self.filled_cells()}/{TOTAL_CELLS}칸)", (180,180,180)),
        ]):
            s = self.fnt_md.render(txt, True, col)
            self.screen.blit(s, (WINDOW_WIDTH//2 - s.get_width()//2, WINDOW_HEIGHT//2 - 32 + i*30))
 
        hint = self.fnt_sm.render("SPACE: 재시작   ESC: 메뉴", True, (200,200,100))
        self.screen.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, WINDOW_HEIGHT//2 + 70))
 
    # 클리어 오버레이 ─────────────────────────────────────────────────
    def _draw_overlay_clear(self):
        t = self.clear_timer
 
        # 배경 페이드인
        alpha = min(180, t * 3)
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((255, 255, 255, alpha // 6))
        self.screen.blit(ov, (0,0))
 
        # 균열선 (점점 길어짐)
        if t > 10:
            prog = min(1.0, (t - 10) / 40)
            cx   = WINDOW_WIDTH  // 2
            cy   = WINDOW_HEIGHT // 2
            for x1, y1, x2, y2 in self.crack_lines:
                ex2 = int(x1 + (x2-x1)*prog)
                ey2 = int(y1 + (y2-y1)*prog)
                pygame.draw.line(self.screen, CRACK_COL, (x1,y1),(ex2,ey2), 2)
 
        # 텍스트 등장
        if t > 35:
            a2 = min(255, (t-35)*8)
 
            title_surf = self.fnt_xl.render("🎉 탈출 성공!", True, (255,230,80))
            title_surf.set_alpha(a2)
            self.screen.blit(title_surf,
                (WINDOW_WIDTH//2 - title_surf.get_width()//2, WINDOW_HEIGHT//2 - 80))
 
            sub = self.fnt_md.render("유리병을 가득 채워 자유를 찾았다!", True, WHITE)
            sub.set_alpha(a2)
            self.screen.blit(sub,
                (WINDOW_WIDTH//2 - sub.get_width()//2, WINDOW_HEIGHT//2 - 28))
 
            sc = self.fnt_md.render(f"최종 점수: {self.snake.score}", True, GOLD)
            sc.set_alpha(a2)
            self.screen.blit(sc,
                (WINDOW_WIDTH//2 - sc.get_width()//2, WINDOW_HEIGHT//2 + 10))
 
        if t > 80:
            a3 = min(255, (t-80)*6)
            hint = self.fnt_sm.render("SPACE: 다시 도전   ESC: 메뉴", True, (200,200,100))
            hint.set_alpha(a3)
            self.screen.blit(hint,
                (WINDOW_WIDTH//2 - hint.get_width()//2, WINDOW_HEIGHT//2 + 60))
 
    # ── 메인 루프 ────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
 
 
if __name__ == "__main__":
    game = Game()
    game.run()
 