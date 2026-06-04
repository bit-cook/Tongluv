"""桌宠头顶倒计时浮窗。
两种模式:
  - 纯显示(interactive=False,默认):番茄钟浮窗用 —— 鼠标穿透、无图标,行为同旧版。
  - 可交互(interactive=True):快捷倒计时用 —— 右侧带 [暂停/继续] [移除] 两个小图标,
    可点击;点击分别发出 toggle_clicked / reset_clicked 信号通知外部。
随桌宠移动(update_position)。配色取自 status_panel 设计 token,与现有界面一致。
"""
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import (QPainter, QColor, QFont, QFontMetrics,
                         QPainterPath, QBrush, QPen)
from src.status_panel import CARD, TB, T1

_DESIGN_H = 1440


class CountdownFloat(QWidget):
    toggle_clicked = pyqtSignal()   # 点「暂停/继续」图标
    reset_clicked  = pyqtSignal()   # 点「移除」图标

    def __init__(self, parent=None, interactive=False):
        super().__init__(parent)
        self._interactive = interactive
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if not interactive:
            flags |= Qt.WindowTransparentForInput   # 纯显示:鼠标穿透
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        scr = QApplication.primaryScreen()
        self._scale = min(1.0, scr.geometry().height() / _DESIGN_H) if scr else 1.0
        self._font_sz = max(8, round(11 * self._scale))
        self._text = ""
        self._paused = False
        self._visible = False
        # 可交互模式下右侧两个图标的度量
        self._icon_sz  = round(20 * self._scale)
        self._icon_gap = round(6 * self._scale)
        self._pad      = round(12 * self._scale)
        self._pause_rect = QRect()
        self._reset_rect = QRect()

    def _icons_w(self) -> int:
        """右侧图标区总宽(含与文字的间隔);非交互为 0。"""
        if not self._interactive:
            return 0
        return self._icon_gap + self._icon_sz * 2 + self._icon_gap

    def set_text(self, text: str):
        """设置文字(如 '⏰ 喝水 04:59');空串隐藏整条。"""
        if text == self._text and self._visible == bool(text):
            return
        self._text = text
        if not text:
            self._visible = False
            self.hide()
            return
        fm = QFontMetrics(QFont("Microsoft YaHei", self._font_sz, QFont.Bold))
        tw = fm.horizontalAdvance(text) + round(28 * self._scale) + self._icons_w()
        th = max(fm.height() + round(12 * self._scale),
                 self._icon_sz + round(10 * self._scale))
        self.setFixedSize(max(tw, round(72 * self._scale)), th)
        self._visible = True
        self.show()
        self.update()

    def set_paused(self, paused: bool):
        """仅可交互模式有意义:切换暂停(▶)/继续(⏸)图标。"""
        if paused != self._paused:
            self._paused = paused
            self.update()

    def update_position(self, pet_x, pet_y, pet_w):
        bx = int(pet_x + pet_w / 2 - self.width() / 2)
        by = int(pet_y - self.height() - round(2 * self._scale))
        if by < 0:
            by = int(pet_y + pet_w + round(2 * self._scale))
        self.move(bx, by)

    def mousePressEvent(self, e):
        if not self._interactive or e.button() != Qt.LeftButton:
            return
        pos = e.pos()
        if self._reset_rect.contains(pos):
            self.reset_clicked.emit()
        elif self._pause_rect.contains(pos):
            self.toggle_clicked.emit()

    def paintEvent(self, _):
        if not self._visible or not self._text:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        rad = r.height() / 2.0
        path = QPainterPath()
        path.addRoundedRect(float(r.x()), float(r.y()),
                            float(r.width()), float(r.height()), rad, rad)
        p.setBrush(QBrush(QColor(CARD)))
        p.setPen(QPen(QColor(TB), max(1.0, 1.5 * self._scale)))
        p.drawPath(path)

        if not self._interactive:
            p.setPen(QColor(T1))
            p.setFont(QFont("Microsoft YaHei", self._font_sz, QFont.Bold))
            p.drawText(r, Qt.AlignCenter, self._text)
            return

        # 可交互:文字左对齐,右侧依次画 [暂停/继续] [移除]
        p.setPen(QColor(T1))
        p.setFont(QFont("Microsoft YaHei", self._font_sz, QFont.Bold))
        text_rect = QRect(r.x() + self._pad, r.y(),
                          r.width() - self._pad - self._icons_w(), r.height())
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._text)

        icon_y  = r.y() + (r.height() - self._icon_sz) // 2
        reset_x = r.right() - self._pad - self._icon_sz
        pause_x = reset_x - self._icon_gap - self._icon_sz
        self._pause_rect = QRect(int(pause_x), int(icon_y), self._icon_sz, self._icon_sz)
        self._reset_rect = QRect(int(reset_x), int(icon_y), self._icon_sz, self._icon_sz)
        p.setFont(QFont("Segoe UI Emoji", max(8, round(10 * self._scale))))
        p.drawText(self._pause_rect, Qt.AlignCenter, "▶" if self._paused else "⏸")
        p.drawText(self._reset_rect, Qt.AlignCenter, "✕")
