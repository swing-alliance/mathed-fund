from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QThread, Signal, Qt,pyqtSignal,QObject,QTimer
from PyQt5.QtGui import QFont
import pandas as pd
from decision import decison_maker
import os
class SortWorker(QThread):
    """工作线程，实际计算的任务"""
    finished_signal = Signal(list)
    def __init__(self, cards,job=None):
        super().__init__()
        self.cards = cards
        self._is_running = True
        self.job=job
    def run(self):
        scored_items = []
        if self.job =="过滤低点":
            for card in self.cards:
                if not self._is_running:
                    return # 终止任务
                score = card.return_decision().is_consider_lowpoint()
                if score:
                    scored_items.append(card)
            if self._is_running:
                self.finished_signal.emit(scored_items)
            return
        for card in self.cards:
            if not self._is_running:
                return # 终止任务
            if self.job=='60天夏普比率':
                score = card.return_decision().max_sharp_ratio_for_days(period_days=60)
            elif self.job=='365天夏普比率':
                score = card.return_decision().max_sharp_ratio_for_days(period_days=365)
            elif self.job =="365天年化收益率":
                score = card.return_decision().year_rate_since_start_this(expected_interval_days=365)
            elif self.job=='80天年化收益率':
                score = card.return_decision().year_rate_since_start_this(expected_interval_days=80)
            elif self.job=="30天年化收益率":
                score = card.return_decision().year_rate_since_start_this(expected_interval_days=30)
            elif self.job=="14天年化收益率":
                score = card.return_decision().year_rate_since_start_this(expected_interval_days=14)
            elif self.job=="3天年化收益率":
                score = card.return_decision().year_rate_since_start_this(expected_interval_days=3)
            elif self.job=='波动率':
                score = card.return_decision().get_max_annualized_volatility()
            scored_items.append((score, card))
        scored_items.sort(key=lambda x: x[0], reverse=True)
        if self._is_running:
            result = [item[1] for item in scored_items]
            self.finished_signal.emit(result)
    def stop(self):
        self._is_running = False




class LoadingDialog(QDialog):
    def __init__(self, parent=None,job=None):
        super().__init__(parent)
        self.job=job
        self.setWindowTitle("计算中")
        self.setFixedSize(200, 80)
        self.setWindowModality(Qt.WindowModal) # 阻塞主窗口
        self.setFont(QFont("微软雅黑", 10))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"正在计算{job}"))
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.close)
        layout.addWidget(self.btn_cancel)




from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject, pyqtSlot
class WorkerSignals(QObject):
    finished = pyqtSignal(object, dict)

class CardWorker(QRunnable):
    def __init__(self, card):
        super().__init__()
        self.card = card
        self.signals = WorkerSignals(parent=None)  # parent=None 即可

        # 不要加这行！保持默认 True
        # self.setAutoDelete(False)

    @pyqtSlot()
    def run(self):
        try:
            result = self.card.show_fund_holding(only_assuming_required=True)
            self.signals.finished.emit(self.card, result)
        except Exception as e:
            import traceback
            print(f"Worker error: {traceback.format_exc()}")

class AssumingManager(QObject):
    card_finished = pyqtSignal(object, dict)
    all_finished = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threadpool = QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(8)
        self.completed = 0
        self.total = 0
        self.all_finished.connect(self._show_done_message)

    def start_batch(self, cards, max_count=500):
        cards_to_process = list(cards)[:max_count]
        self.total = len(cards_to_process)
        self.completed = 0
        
        if self.total == 0:
            self.all_finished.emit(0)
            return

        self.remaining_cards = cards_to_process
        self.submit_timer = QTimer(self)
        self.submit_timer.timeout.connect(self._submit_next_worker)
        self.submit_timer.start(1000)

    def _submit_next_worker(self):
        if not self.remaining_cards:
            self.submit_timer.stop()
            return
            
        card = self.remaining_cards.pop(0)
        worker = CardWorker(card)
        worker.signals.finished.connect(self.on_one_card_finished)
        self.threadpool.start(worker)



    @pyqtSlot(object, dict)
    def on_one_card_finished(self, card, result):
        # 此时这个方法会在 AssumingManager 所属的线程（主线程）中安全执行
        self.completed += 1
        self.card_finished.emit(card, result)
        if self.completed >= self.total:
            self.all_finished.emit(self.completed)

    def _show_done_message(self, count):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(None, "任务完成", f"任务已结束！\n处理数量:{count}")


from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import QApplication



def read_df(key,path):
    """通过path读取df，生成key和df的键值对"""
    if not os.path.exists(path):
        print(f"[警告] CSV 文件不存在: {path}")
        return {key: None}

    try:
        df = pd.read_csv(
            path,
            encoding='utf-8',        # 常见中文文件用 utf-8
            dtype=str,               # 可选：全部读成字符串，避免类型推断错误
        )
        df.dropna(how='all', inplace=True)
        df.dropna(how='all', axis=1, inplace=True)
        print(f"[成功] 读取 CSV: {key} <- {path}  ({df.shape[0]} 行 × {df.shape[1]} 列)")
        return {key: df}
    except Exception as e:
        print(f"[错误] 读取 CSV 失败 {key} ({path}): {e}")
        return {key: None}
                     
def multithread_read_file(cards):
    """多线程暴力加速读取文件"""
    future_store=[]
    results=[]
    with ThreadPoolExecutor(max_workers=16) as executor:
        for card in cards:
            future = executor.submit(read_df, card.filename, card.file_path)
            future_store.append(future)
        for future in as_completed(future_store):
            result = future.result()
            results.append(result)
        return results
    
def calculate_sharp(cards):
    """计算夏普比率,多线程优化"""
    store =multithread_read_file(cards)
    for single in store:
        for key, df in single.items():
            decision=decison_maker(fund_code=None,path=None,df=df)
            print(decision.max_sharp_ratio_for_days(60))

