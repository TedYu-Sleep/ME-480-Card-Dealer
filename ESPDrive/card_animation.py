# ============================================================
#  card_animation.py
#  旋转纸牌动画 - 可导入的 Class 封装
#  MicroPython · ESP32 + SSD1306 128x64 I2C OLED
#
#  用法示例见文件末尾 __main__ 块
# ============================================================
 
import math
import time
 
 
# ════════════════════════════════════════════════════════════
#  CardAnimation
# ════════════════════════════════════════════════════════════
class CardAnimation:
    """
    在 SSD1306 OLED 上渲染旋转纸牌动画。
 
    参数
    ----
    oled        : ssd1306.SSD1306_I2C 实例（必须）
    card_w      : 纸牌宽度像素，默认 36
    card_h      : 纸牌高度像素，默认 52
    total_frames: 旋转一圈的帧数，默认 36（值越大越慢越流畅）
    frame_delay : 帧间隔秒数，默认 0.03（≈30 fps）
    suits       : 花色列表，默认 ['S','H','D','C']
    ranks       : 牌面列表，默认 ['A','K','Q','J']
    corner_r    : 切角半径，默认 3
    shadow      : 是否启用阴影，默认 True
    cx / cy     : 动画中心坐标，默认屏幕中心
 
    公开方法
    --------
    step()          — 渲染并显示下一帧，返回当前帧号
    run()           — 无限循环（阻塞）
    run_n(n)        — 运行 n 帧后返回
    reset()         — 重置到第 0 帧
    set_card(suit, rank) — 锁定显示指定牌面（传 None 恢复自动轮换）
    """
 
    # ── 3×5 点阵字体 ────────────────────────────────────────
    _FONT3 = {
        'A': [0b111, 0b101, 0b111, 0b101, 0b101],
        'K': [0b101, 0b110, 0b100, 0b110, 0b101],
        'Q': [0b111, 0b101, 0b101, 0b111, 0b011],
        'J': [0b011, 0b001, 0b001, 0b101, 0b111],
        '2': [0b111, 0b001, 0b111, 0b100, 0b111],
        '3': [0b111, 0b001, 0b111, 0b001, 0b111],
        '4': [0b101, 0b101, 0b111, 0b001, 0b001],
        '5': [0b111, 0b100, 0b111, 0b001, 0b111],
        '6': [0b111, 0b100, 0b111, 0b101, 0b111],
        '7': [0b111, 0b001, 0b001, 0b001, 0b001],
        '8': [0b111, 0b101, 0b111, 0b101, 0b111],
        '9': [0b111, 0b101, 0b111, 0b001, 0b111],
        '0': [0b111, 0b101, 0b101, 0b101, 0b111],
        'T': [0b111, 0b010, 0b010, 0b010, 0b010],  # 10 用 T
    }
 
    def __init__(self, oled,
                 card_w=36, card_h=52,
                 total_frames=36, frame_delay=0.01,
                 suits=None, ranks=None,
                 corner_r=3, shadow=True,
                 cx=None, cy=None):
 
        self._oled = oled
        self._W = oled.width
        self._H = oled.height
        self._CX = cx if cx is not None else self._W // 2
        self._CY = cy if cy is not None else self._H // 2
 
        self.card_w       = card_w
        self.card_h       = card_h
        self.total_frames = total_frames
        self.frame_delay  = frame_delay
        self.corner_r     = corner_r
        self.shadow       = shadow
 
        self._suits = suits if suits is not None else ['S', 'H', 'D', 'C']
        self._ranks = ranks if ranks is not None else ['A', 'K', 'Q', 'J']
 
        self._frame    = 0
        self._suit_idx = 0
        self._fixed_suit = None   # None = 自动轮换
        self._fixed_rank = None
 
    # ── 公开接口 ─────────────────────────────────────────────
 
    def reset(self):
        """重置动画到第 0 帧。"""
        self._frame    = 0
        self._suit_idx = 0
 
    def set_card(self, suit=None, rank=None):
        """
        锁定显示指定牌面。
        suit/rank 传 None 则恢复自动轮换。
        示例: anim.set_card('H', 'K')
        """
        self._fixed_suit = suit
        self._fixed_rank = rank
 
    def step(self):
        """渲染并显示下一帧，返回当前帧号。"""
        f = self._frame
        angle = (f % self.total_frames) / self.total_frames * 2 * math.pi
 
        suit = self._fixed_suit if self._fixed_suit else \
               self._suits[self._suit_idx % len(self._suits)]
        rank = self._fixed_rank if self._fixed_rank else \
               self._ranks[self._suit_idx % len(self._ranks)]
 
        cos_a = abs(math.cos(angle))
        vis_w = max(2, int(self.card_w * cos_a))
        vis_h = self.card_h + int(4 * abs(math.sin(angle * 2)))
 
        self._oled.fill(0)
 
        if self.shadow:
            self._draw_shadow(vis_w + 2, vis_h + 2)
 
        self._draw_card_outline(vis_w, vis_h)
 
        if cos_a > 0.25:
            self._draw_face(rank, suit, vis_w, vis_h, cos_a)
        else:
            self._draw_back(vis_w, vis_h)
 
        self._oled.show()
 
        self._frame += 1
        if self._fixed_suit is None and self._frame % self.total_frames == 0:
            self._suit_idx += 1
 
        return self._frame - 1
 
    def run(self):
        """无限循环播放动画（阻塞）。按 KeyboardInterrupt 停止。"""
        while True:
            self.step()
            time.sleep(self.frame_delay)
 
    def run_n(self, n):
        """运行 n 帧后返回。"""
        for _ in range(n):
            self.step()
            time.sleep(self.frame_delay)
 
    # ── 私有绘图方法 ─────────────────────────────────────────
 
    def _px(self, x, y, c=1):
        if 0 <= x < self._W and 0 <= y < self._H:
            self._oled.pixel(x, y, c)
 
    def _line(self, x0, y0, x1, y1, c=1):
        """Bresenham 直线，自动裁剪到屏幕范围。"""
        dx = abs(x1 - x0); dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        W, H = self._W, self._H
        fb = self._oled
        while True:
            if 0 <= x0 < W and 0 <= y0 < H:
                fb.pixel(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; x0 += sx
            if e2 < dx:
                err += dx; y0 += sy
 
    def _rot(self, px, py):
        """将局部坐标（相对 CX,CY）转为屏幕坐标（无旋转，已含偏移）。"""
        return px + self._CX, py + self._CY
 
    @staticmethod
    def _rotate_pt(lx, ly, angle):
        """将局部点绕原点旋转 angle 弧度，返回整数坐标。"""
        c = math.cos(angle); s = math.sin(angle)
        return int(lx * c - ly * s + 0.5), int(lx * s + ly * c + 0.5)
 
    def _outline_pts(self, w, h, ox=0, oy=0):
        """生成带切角的纸牌轮廓点（屏幕坐标，无旋转）。"""
        hw, hh, r = w // 2, h // 2, self.corner_r
        local = [
            (-hw+r, -hh), ( hw-r, -hh),
            ( hw,  -hh+r), ( hw,   hh-r),
            ( hw-r,  hh), (-hw+r,  hh),
            (-hw,   hh-r), (-hw,  -hh+r),
        ]
        return [(lx + self._CX + ox, ly + self._CY + oy) for lx, ly in local]
 
    def _draw_polygon(self, pts, c=1):
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            self._line(x0, y0, x1, y1, c)
 
    def _draw_card_outline(self, w, h):
        self._draw_polygon(self._outline_pts(w, h))
 
    def _draw_shadow(self, w, h):
        off = 3
        pts = self._outline_pts(w, h, ox=off, oy=off)
        # 虚线阴影（每隔一像素）
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            dx = x1 - x0; dy = y1 - y0
            steps = max(abs(dx), abs(dy))
            if steps == 0:
                continue
            for s in range(0, steps, 2):
                fx = x0 + dx * s // steps
                fy = y0 + dy * s // steps
                self._px(fx, fy)
 
    def _draw_char(self, px, py, ch):
        """在 (px,py) 处绘制 3×5 点阵字符（屏幕坐标）。"""
        bitmap = self._FONT3.get(ch, self._FONT3['A'])
        for row, bits in enumerate(bitmap):
            for col in range(3):
                if bits & (1 << (2 - col)):
                    self._px(px + col, py + row)
 
    def _draw_face(self, rank, suit, vis_w, vis_h, cos_a):
        CX, CY = self._CX, self._CY
        # 左上角 rank
        self._draw_char(CX - vis_w // 2 + 2, CY - vis_h // 2 + 2, rank)
        # 右下角 rank
        self._draw_char(CX + vis_w // 2 - 5, CY + vis_h // 2 - 7, rank)
        # 中心花色
        self._draw_center_suit(suit, CX, CY, max(3, int(5 * cos_a)))
 
    def _draw_back(self, vis_w, vis_h):
        CX, CY = self._CX, self._CY
        for yy in range(CY - vis_h // 2 + 3, CY + vis_h // 2 - 2, 4):
            self._line(CX - vis_w // 2 + 2, yy,
                       CX + vis_w // 2 - 2, yy)
 
    def _draw_center_suit(self, suit, cx, cy, size):
        """在 (cx, cy) 绘制花色图标。"""
        if suit == 'D':
            s = size
            pts = [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy), (cx, cy-s)]
            for i in range(4):
                self._line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])
 
        elif suit == 'S':
            s = size
            self._line(cx,    cy-s,   cx+s,  cy+s)
            self._line(cx+s,  cy+s,   cx-s,  cy+s)
            self._line(cx-s,  cy+s,   cx,    cy-s)
            self._line(cx,    cy+s,   cx,    cy+s+2)
 
        elif suit == 'H':
            r2 = size * 0.7
            for ox in [-size // 2, size // 2]:
                for deg in range(0, 361, 15):
                    a0 = math.radians(deg)
                    a1 = math.radians(deg + 15)
                    x0 = int(cx + ox + r2 * math.cos(a0))
                    y0 = int(cy - size // 3 + r2 * math.sin(a0))
                    x1 = int(cx + ox + r2 * math.cos(a1))
                    y1 = int(cy - size // 3 + r2 * math.sin(a1))
                    self._line(x0, y0, x1, y1)
            self._line(cx - size, cy, cx,        cy + size)
            self._line(cx + size, cy, cx,        cy + size)
 
        elif suit == 'C':
            r2 = max(2, size // 2)
            for ox, oy in [(-r2, r2 // 2), (r2, r2 // 2), (0, -r2)]:
                for deg in range(0, 360, 20):
                    a0 = math.radians(deg)
                    a1 = math.radians(deg + 20)
                    x0 = cx + ox + int(r2 * math.cos(a0))
                    y0 = cy + oy + int(r2 * math.sin(a0))
                    x1 = cx + ox + int(r2 * math.cos(a1))
                    y1 = cy + oy + int(r2 * math.sin(a1))
                    self._line(x0, y0, x1, y1)
            self._line(cx, cy + r2, cx,      cy + size)
            self._line(cx - r2, cy + size, cx + r2, cy + size)