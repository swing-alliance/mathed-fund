from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QThread, Signal, Qt
from PyQt5.QtGui import QFont
class SortWorker(QThread):
    # 信号：计算完成传回排序后的列表
    finished_signal = Signal(list)
    def __init__(self, cards):
        super().__init__()
        self.cards = cards
        self._is_running = True

    def run(self):
        scored_items = []
        for card in self.cards:
            if not self._is_running:
                return # 终止任务
            score = card.return_decision().max_sharp_ratio_for_days(period_days=60)
            scored_items.append((score, card))
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        if self._is_running:
            result = [item[1] for item in scored_items]
            self.finished_signal.emit(result)

    def stop(self):
        self._is_running = False

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("计算中")
        self.setFixedSize(200, 80)
        self.setWindowModality(Qt.WindowModal) # 阻塞主窗口
        self.setFont(QFont("微软雅黑", 10))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("正在计算夏普比率..."))
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.close)
        layout.addWidget(self.btn_cancel)

