from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import QPoint, Qt

class virtualcanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = [] 
        self.max_points = 100   # 增加点数显示，让曲线更平滑
        self.setMinimumSize(400, 300)
        # 将背景设置为白色，方便看清黑色线条
        self.setStyleSheet("background-color: white;")

    def update_data(self, time_str, value):
        clean_time = str(time_str)[:10]
        self.data_points.append((clean_time, value))
        
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
            
        # 优化：不要在这里处理复杂逻辑，只触发重绘
        self.update()

    def paintEvent(self, event):
        if len(self.data_points) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        padding = 50 

        # --- 1. 预计算范围 (尽量轻量) ---
        vals = [p[1] for p in self.data_points]
        v_min, v_max = min(vals), max(vals)
        val_range = (v_max - v_min) if v_max != v_min else 1.0

        # --- 2. 绘制坐标轴 (黑色) ---
        black_pen = QPen(Qt.black, 1)
        painter.setPen(black_pen)
        painter.drawLine(padding, h - padding, w - padding, h - padding) # X
        painter.drawLine(padding, padding, padding, h - padding)         # Y

        # --- 3. 绘制折线 (黑色) ---
        line_pen = QPen(Qt.black, 2)
        painter.setPen(line_pen)
        
        # 绘制路径
        prev_pt = None
        for i, (t, val) in enumerate(self.data_points):
            # 计算当前点坐标
            x = padding + (i / (self.max_points - 1)) * (w - 2 * padding)
            y = (h - padding) - ((val - v_min) / val_range) * (h - 2 * padding)
            curr_pt = QPoint(int(x), int(y))
            
            if prev_pt:
                painter.drawLine(prev_pt, curr_pt)
            prev_pt = curr_pt

        # --- 4. 绘制文字 (黑色) ---
        painter.setFont(QFont("Microsoft YaHei", 10))
        last_time, last_val = self.data_points[-1]
        painter.drawText(padding, h - 20, f"日期: {last_time}")
        painter.drawText(padding, 30, f"当前价值: {last_val:.2f}")