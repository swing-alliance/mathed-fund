from PyQt5.QtCore import QThread, pyqtSignal

class SimulationThread(QThread):
    # 定义一个信号，传递 (日期字符串, 账户余额)
    update_signal = pyqtSignal(str, float)
    # 定义结束信号
    finished_signal = pyqtSignal(float)

    def __init__(self, simulater):
        super().__init__()
        self.simulater = simulater

    def run(self):
        # 1. 重新定义 simulater 的数据回传逻辑
        # 我们通过一个临时函数钩子，把信号发射出去
        def signal_bridge(date_str, balance):
            self.update_signal.emit(date_str, balance)

        # 2. 启动模拟器
        # 修改你的 start 方法，让它调用这个 bridge 而不是直接操作 canvas
        try:
            self.simulater.start(callback=signal_bridge)
            final_balance = self.simulater.get_account_balance()
            self.finished_signal.emit(final_balance)
        except Exception as e:
            print(f"子线程运行出错: {e}")