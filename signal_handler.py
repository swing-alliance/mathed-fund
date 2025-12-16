from PyQt5.QtCore import pyqtSignal, QObject

class SignalEmitter(QObject):
    """一个用于发出自定义信号的单例类。"""
    
    # 定义一个无参数的信号，用于通知 UI 刷新
    refresh_ui_signal = pyqtSignal()




class HistorySignalEmitter(QObject):
    """一个用于发出历史记录相关信号的单例类。"""
    
    # 定义一个信号，用于通知加载上一个中心部件
    load_previous_widget_signal = pyqtSignal()

# 创建一个全局可访问的实例
signal_emitter = SignalEmitter()
history_signal_emitter = HistorySignalEmitter()