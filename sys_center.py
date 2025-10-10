from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QApplication,
    QHBoxLayout, QMainWindow, QAction
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize
import os

balanced_path = os.path.join(os.getcwd(), 'types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'types','Equity')
index_path = os.path.join(os.getcwd(), 'types','Index')
Qdii_path = os.path.join(os.getcwd(), 'types','Qdii')
to_worker_path = os.path.join(os.getcwd(), 'to_worker')

# --- 1. QScrollArea (保持不变) ---
class CustomScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

# --- 新增：计划面板占位符 (模拟 ControlPanel) ---
class PlanPannel(QWidget):
    """用于替换 SysCentral 的新界面占位符 (模拟 ControlPanel)"""
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #E6E6E6;") # 浅灰色背景以便区分
        layout = QVBoxLayout(self)
        
        # 记录实例ID，用于演示复用
        self.instance_id = id(self) 
        
        self.label = QLabel("")
        self.label.setFont(QFont("微软雅黑", 20))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # 初始设置路径
        self.set_path(path)

    def set_path(self, path):
        """复用实例时，更新其显示内容和状态"""
        self.path = path
        # 标签内容现在包含实例ID，证明它是同一个对象
        self.label.setText(f"计划面板已加载 (ID: {self.instance_id}):\n路径参数: {path}\n（此面板已被复用，未删除）")

# --- 2. 滚动内容区域 ---
class SysCentral(QWidget):
    # 接受 parent_window 参数，用于访问主窗口的槽函数
    def __init__(self, parent_window, parent=None): 
        super().__init__(parent)

        self.parent_window = parent_window  # 存储父窗口引用
        
        # 定义 index_path 属性
        self.index_path = "/path/to/index/data" 

        self.setMinimumSize(600, 400)
        self.setWindowTitle("Scroll Area 始终显示按钮示例")
        
        # --- 设置 SysCentral 的样式表（黑色系悬停边框） ---
        self.setStyleSheet("""
            /* 1. 按钮默认样式：仅文字，透明背景，无边框 */
            QPushButton {
                padding: 10px 30px;
                font-weight: bold;
                color: #000000; 
                background-color: transparent; 
                border: 2px solid transparent; 
                border-radius: 20px;
            }
            /* 2. 按钮悬停样式：显示边框和浅背景 */
            QPushButton:hover {
                border: 2px solid #333333; 
                background-color: #F0F0F0; 
            }
            /* 3. 保持滚动区域背景和标签透明，确保样式干净 */
            QScrollArea { border: none; background: transparent; }
            QScrollArea QWidget#qt_scrollarea_viewport { background: transparent; }
            QLabel { background-color: transparent; }
        """)

        self.scroll_area = CustomScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.viewport().setObjectName("qt_scrollarea_viewport")

        # --- 滚动内容容器 ---
        scroll_content = QWidget()
        scroll_content.setMinimumHeight(1000) 
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        
        inner_scroll_layout = QVBoxLayout(scroll_content)
        inner_scroll_layout.setContentsMargins(50, 250, 50, 50) 

        self.welcome_label = QLabel("欢迎, 这是系统主页")
        self.welcome_label.setFont(QFont("微软雅黑", 24))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        inner_scroll_layout.addWidget(self.welcome_label)
        
        inner_scroll_layout.addStretch(1) 
        
        # --- 按钮区域 (二级布局: 水平布局) ---
        inner_scroll_h_layout = QHBoxLayout()
        
        # 初始化按钮
        self.mix_button = QPushButton("从混合型开始")
        self.stock_button = QPushButton("从股票型开始")
        self.index_button = QPushButton("从指数型开始")
        self.alternative_button = QPushButton("从Qdii或另类开始")
        
        # 统一处理按钮属性
        self.buttons = [self.stock_button, self.mix_button, self.index_button, self.alternative_button]
        for btn in self.buttons:
            btn.setFont(QFont("微软雅黑", 14))
            btn.setVisible(False) 
        
        # 建立核心连接：调用父窗口的 load_plan_pannel
        self.index_button.clicked.connect(lambda: self.parent_window.load_plan_pannel(base_path=index_path))
        self.stock_button.clicked.connect(lambda: self.parent_window.load_plan_pannel(base_path=Equity_path))
        self.mix_button.clicked.connect(lambda: self.parent_window.load_plan_pannel(base_path=balanced_path))
        self.alternative_button.clicked.connect(lambda: self.parent_window.load_plan_pannel(base_path=Qdii_path))
        
        # 将按钮添加到水平布局
        inner_scroll_h_layout.addStretch(1) 
        inner_scroll_h_layout.addWidget(self.mix_button)
        inner_scroll_h_layout.addWidget(self.stock_button)
        inner_scroll_h_layout.addWidget(self.index_button) 
        inner_scroll_h_layout.addWidget(self.alternative_button)
        inner_scroll_h_layout.addStretch(1) 
        
        inner_scroll_layout.addLayout(inner_scroll_h_layout)
        inner_scroll_layout.addSpacing(50) 
        
        self.scroll_area.setWidget(scroll_content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        
        self._toggle_buttons_visibility(True)

    def _toggle_buttons_visibility(self, visible):
        """控制所有按钮的可见性"""
        for btn in self.buttons:
            btn.setVisible(visible)
