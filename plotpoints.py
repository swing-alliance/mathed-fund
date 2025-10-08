from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class MplCanvas(FigureCanvas):
    """一个自适应的 Matplotlib 画布，用于绘制图形。"""
    def __init__(self, parent=None, dpi=100):
        self.fig = Figure(figsize=(10, 7.5), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes: Axes = self.fig.add_subplot(111)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()
        # 绑定鼠标滚轮事件，实现放大缩小
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        # 绑定鼠标点击和释放事件，用于双击还原和拖动
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        # 用于记录拖动状态和初始位置
        self.press = None
        
    def on_scroll(self, event):
        """处理鼠标滚轮事件以实现放大和缩小。"""
        if event.xdata is None or event.ydata is None:
            return
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        scale_factor = 1.2
        if event.button == 'up':
            x_min_new = event.xdata - (event.xdata - x_min) / scale_factor
            x_max_new = event.xdata + (x_max - event.xdata) / scale_factor
            y_min_new = event.ydata - (event.ydata - y_min) / scale_factor
            y_max_new = event.ydata + (y_max - event.ydata) / scale_factor
        elif event.button == 'down':
            x_min_new = event.xdata - (event.xdata - x_min) * scale_factor
            x_max_new = event.xdata + (x_max - event.xdata) * scale_factor
            y_min_new = event.ydata - (event.ydata - y_min) * scale_factor
            y_max_new = event.ydata + (y_max - event.ydata) * scale_factor
        else:
            return
        self.axes.set_xlim(x_min_new, x_max_new)
        self.axes.set_ylim(y_min_new, y_max_new)
        self.fig.canvas.draw_idle()

    def on_press(self, event):
        """处理鼠标按下事件，用于双击还原和记录拖动起始点。"""
        if event.button == 1 and event.dblclick:
            self.axes.autoscale(enable=True, axis='both', tight=True)
            self.axes.figure.autofmt_xdate()
            self.draw_idle()
            return
        if event.button == 1 and event.inaxes:
            self.press = event.xdata, event.ydata

    def on_motion(self, event):
        """处理鼠标移动事件，用于拖动。"""
        if self.press is None or event.inaxes is None or event.button != 1:
            return
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        dx = event.xdata - self.press[0]
        dy = event.ydata - self.press[1]
        self.axes.set_xlim(x_min - dx, x_max - dx)
        self.axes.set_ylim(y_min - dy, y_max - dy)
        self.draw_idle()

    def on_release(self, event):
        """处理鼠标释放事件，结束拖动。"""
        self.press = None




