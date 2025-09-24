import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
from qdialogue import FundInfoDialog
import akshare as ak
import pandas as pd
import shutil
from shutil import Error
from qwidget import CsvGraphWidget


TO_WORKER = "to_worker"
FOUND_PATH = "found"
def get_fund_name(filename):
        """根据六位基金代码返回基金名称，全局"""
        info=ak.fund_individual_basic_info_xq(symbol=filename)
        fund_full_name: str = info[info['item'] == '基金全称']['value'].iloc[0]
        return fund_full_name
def get_fund_info(filename):
        """根据六位基金代码返回基金信息，全局"""
        info=ak.fund_individual_basic_info_xq(symbol=filename)
        return info


class ProjectCard(QFrame):
    """每个加载的项目卡片"""
    visualize_requested = pyqtSignal(str) # 发送文件路径，调用信号

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path#当前to_worker下的文件路径
        self.filename = os.path.splitext(os.path.basename(self.file_path))[0]#文件名
        self.fund_tittle: str = get_fund_name(self.filename)  # 获取基金名称
        
        self.design()


    def design(self):
        # 设置细黑边框
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        
        # 标题，第一层
        title_label = QLabel(f"{self.fund_tittle}")
        title_label.setFont(QFont('微软雅黑', 11))
        title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_label)
        
        # 第二层
        row_layout = QHBoxLayout()
        file_label = QLabel(f"基金代码:{self.filename}")
        file_label.setFont(QFont('微软雅黑', 10))
        file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 替代输入框的按钮
        self.show_button = QPushButton("显示详细信息")
        self.show_button.setFont(QFont('微软雅黑', 10))
        self.show_button.clicked.connect(self.show_fund_info)

        self.discard_button = QPushButton("丢弃")
        self.discard_button.setFont(QFont('微软雅黑', 10))
        self.discard_button.clicked.connect(self.discard)

        self.visualize_button = QPushButton("转到计算")
        self.visualize_button.setFont(QFont('微软雅黑', 10))
        # 将按钮的点击信号连接到一个新的私有方法
        self.visualize_button.clicked.connect(self._emit_visualize_request)

        row_layout.addWidget(file_label, 1)
        row_layout.addWidget(self.show_button, 2)  # 将按钮添加到布局中
        row_layout.addWidget(self.visualize_button, 2)
        row_layout.addWidget(self.discard_button, 2)
        

        
        layout.addLayout(row_layout)

    def show_fund_info(self):
        """显示基金信息对话框"""
        self.info_dialogue = FundInfoDialog(get_fund_info(self.filename))  # 获取基金信息并显示
        result = self.info_dialogue.exec_()
        if result == QDialog.Accepted:
            print("对话框被接受。")
        else:
            print("对话框被拒绝或关闭。")

    def discard(self):
        """丢弃操作：删除 TO_WORKER 文件夹中的文件并刷新卡片"""
        target_path = os.path.join(TO_WORKER, os.path.basename(self.file_path))
        if os.path.exists(target_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("确认操作")
            msg_box.setIcon(QMessageBox.Warning)  # 设置警告图标
            msg_box.setText(f"确定要丢弃文件 '{self.filename}' 吗？")
            msg_box.setInformativeText("后续只能手动恢复")
            # 设置自定义的中文按钮
            ok_button = msg_box.addButton("确定", QMessageBox.AcceptRole)
            cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_button) # 设置“取消”为默认按钮
            reply = msg_box.exec_()
            if msg_box.clickedButton() == ok_button:
                try:
                    os.remove(target_path)
                    print(f"文件 '{self.filename}' 已成功删除")
                    self.deleteLater()
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"删除文件失败: {e}")
        else:
            QMessageBox.warning(self, "警告", f"文件 '{self.filename}' 在 TO_WORKER 文件夹中不存在，无法丢弃。")

    def _emit_visualize_request(self):
            """当按钮点击时，发出 visualize_requested 信号，并传递文件路径"""
            self.visualize_requested.emit(self.file_path)





class ControlPanel(QWidget):
    """控制面板（QWidget），带滚动区域"""
    visualize_requested = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)

        # 顶部水平布局（左上角加号）
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
        
        # 加载完成开始操作
        self.load_projects()


    def add_project(self):
        """只允许在 found 文件夹下选择 CSV，并检查 TO_WORKER 文件夹是否已有该文件"""
        os.makedirs(FOUND_PATH, exist_ok=True)
        # 打开文件选择对话框，选择 CSV 文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", FOUND_PATH, "CSV Files (*.csv)"
        )
        if not file_path:
            return
        os.makedirs(TO_WORKER, exist_ok=True)
        target_path = os.path.join(TO_WORKER, os.path.basename(file_path))
        # 检查 TO_WORKER 文件夹下是否已经有该文件
        if os.path.exists(target_path):
            QMessageBox.warning(self, "警告", "该文件已经存在面板中！")
            return  # 文件已存在，跳过添加卡片
        # 如果文件不存在，则复制文件
        try:
            shutil.copy(file_path, target_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"复制文件失败: {e}")
            return
        # 添加一个项目卡片到滚动区域
        card = ProjectCard(target_path)
        card.visualize_requested.connect(self.visualize_requested.emit)
        self.scroll_layout.addWidget(card)

    def load_projects(self):
        """从 TO_WORKER 文件夹加载项目卡片"""
        # 获取 TO_WORKER 文件夹下的所有文件
        project_files = os.listdir(TO_WORKER)
        # 用于跟踪已加载的项目文件
        loaded_files = set()
        for file_name in project_files:
            file_path = os.path.join(TO_WORKER, file_name)
            
            # 如果项目已经加载过，就跳过
            if file_path in loaded_files:
                continue
            
            # 为每个文件创建一个卡片，并将其添加到滚动区域
            card = ProjectCard(file_path)
            card.visualize_requested.connect(self.visualize_requested.emit)
            self.scroll_layout.addWidget(card)
            # 将该文件路径添加到已加载集合中
            loaded_files.add(file_path)
            
            # 在每次添加卡片后，处理事件，立即更新界面
            QApplication.processEvents()



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 创建并显示主面板
    panel = ControlPanel()
    panel.setWindowTitle("项目控制面板")
    panel.resize(1200, 800)
    panel.show()

    sys.exit(app.exec_())