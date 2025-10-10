import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication,QMenu,QAction,QProgressDialog
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
import pandas as pd
import shutil
from projectcard import ProjectCard
TO_WORKER = "to_worker"
FOUND_PATH = "found"

balanced_path = os.path.join(os.getcwd(), 'types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'types','Equity')
index_path = os.path.join(os.getcwd(), 'types','Index')
Qdii_path = os.path.join(os.getcwd(), 'types','Qdii')
to_worker_path = os.path.join(os.getcwd(), 'to_worker')


class ControlPanel(QWidget):
    """控制面板（QWidget），带滚动区域"""
    visualize_requested = pyqtSignal(str)
    def __init__(self, parent=None,base_path=None):
        super().__init__(parent)
        self.loaded_cards = {}#用于缓存已加载的卡片
        self.base_path = base_path 
        self.file_nums = len(os.listdir(base_path))
        main_layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setFont(QFont('微软雅黑', 20))
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_project_from_found)
        self.index_label=self.what_label_now()
        top_bar.addWidget(self.add_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch(1)  
        top_bar.addWidget(self.index_label, alignment=Qt.AlignRight)
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

        self.load_projects_from_path(base_path)

    def add_project_from_found(self):
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




    def load_projects_from_path(self, path):
        """从 types 文件夹加载项目卡片，并将实例缓存起来。"""
        def load_files_from_path(directory_path):
            """加载指定路径下的文件并更新进度框"""
            project_files = os.listdir(directory_path)
            self.file_nums = len(project_files)
            if not project_files:
                print(f"路径 {directory_path} 中没有文件！")
                return
            
            progress_dialog = QProgressDialog("正在加载文件...", "取消", 0, len(project_files), self)
            progress_dialog.setWindowModality(Qt.WindowModal)  # 设置为模态对话框，防止其他操作
            progress_dialog.setCancelButton(None)  # 禁用取消按钮
            progress_dialog.setFont(QFont('微软雅黑', 10))
            progress_dialog.resize(600, 50)
            progress_dialog.show()  # 显示进度框
            for index, file_name in enumerate(project_files):
                if file_name not in self.loaded_cards:
                    file_path = os.path.join(directory_path, file_name)
                    card = ProjectCard(file_path)
                    card.visualize_requested.connect(self.visualize_requested.emit)
                    self.scroll_layout.addWidget(card)
                    self.loaded_cards[file_name] = card
                    progress_dialog.setValue(index + 1)
                    QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        break
        if path == balanced_path:
            load_files_from_path(balanced_path)
        elif path == Equity_path:
            load_files_from_path(Equity_path)
        elif path == index_path:
            load_files_from_path(index_path)
        elif path == Qdii_path:
            load_files_from_path(Qdii_path)

       

    def what_label_now(self):
        """用于显示当前所关注的项目类"""
        qlabel = QLabel()
        qlabel.setFont(QFont('微软雅黑', 12))
        if self.base_path == balanced_path:
            qlabel.setText(f"混合型{self.file_nums}个")
        elif self.base_path == Equity_path:
            qlabel.setText(f"股票型{self.file_nums}个")
        elif self.base_path == index_path:
            qlabel.setText(f"指数型{self.file_nums}个")
        elif self.base_path == Qdii_path:
            qlabel.setText(f"QDII或另类{self.file_nums}个")
        return qlabel




if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    control_panel = ControlPanel()
    control_panel.show()
    sys.exit(app.exec_())

