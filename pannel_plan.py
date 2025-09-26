import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication,QMenu,QAction
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
import pandas as pd
import shutil
from projectcard import ProjectCard
TO_WORKER = "to_worker"
FOUND_PATH = "found"


class ControlPanel(QWidget):
    """控制面板（QWidget），带滚动区域"""
    visualize_requested = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_cards = {}#用于缓存已加载的卡片
        main_layout = QVBoxLayout(self)
        top_bar = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setFont(QFont('微软雅黑', 20))
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_project)

        top_bar.addWidget(self.add_btn, alignment=Qt.AlignLeft)
        top_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(top_bar)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 自动扩展
        main_layout.addWidget(self.scroll_area)

        # 滚动内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)  # 卡片从上往下排
        self.scroll_area.setWidget(self.scroll_content)

        self.load_projects()

    def add_project(self):
        """只允许在 found 文件夹下选择 CSV，并检查 TO_WORKER 文件夹是否已有该文件"""
        os.makedirs(FOUND_PATH, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", FOUND_PATH, "CSV Files (*.csv)"
        )
        if not file_path:
            return
        os.makedirs(TO_WORKER, exist_ok=True)
        target_path = os.path.join(TO_WORKER, os.path.basename(file_path))
        if os.path.exists(target_path):
            QMessageBox.warning(self, "警告", "该文件已经存在面板中！")
            return 
        try:
            shutil.copy(file_path, target_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"复制文件失败: {e}")
            return
        card = ProjectCard(target_path)
        card.visualize_requested.connect(self.visualize_requested.emit)
        self.scroll_layout.addWidget(card)

    def load_projects(self):
            """从 TO_WORKER 文件夹加载项目卡片，并将实例缓存起来。"""
            project_files = os.listdir(TO_WORKER)
            # 这里不再需要 loaded_files 集合，直接用实例缓存的键即可
            for file_name in project_files:
                # 只有当卡片不在缓存中时才创建
                if file_name not in self.loaded_cards:
                    file_path = os.path.join(TO_WORKER, file_name)
                    card = ProjectCard(file_path)
                    card.visualize_requested.connect(self.visualize_requested.emit)
                    self.scroll_layout.addWidget(card)
                    # 将新创建的卡片实例缓存起来
                    self.loaded_cards[file_name] = card
                    QApplication.processEvents()

    def reload_projects(self):
        """重新加载项目卡片，通过哈希表，采用高效的增量更新方式。"""
        current_files = set(os.listdir(TO_WORKER))
        removed_files = set(self.loaded_cards.keys()) - current_files
        for file_name in removed_files:
            card_to_remove = self.loaded_cards.pop(file_name)
            self.scroll_layout.removeWidget(card_to_remove)
            card_to_remove.deleteLater()
        new_files = current_files - set(self.loaded_cards.keys())
        for file_name in new_files:
            file_path = os.path.join(TO_WORKER, file_name)
            card = ProjectCard(file_path)
            card.visualize_requested.connect(self.visualize_requested.emit)
            self.scroll_layout.addWidget(card)
            self.loaded_cards[file_name] = card
        QApplication.processEvents()




if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    control_panel = ControlPanel()
    control_panel.show()
    sys.exit(app.exec_())

