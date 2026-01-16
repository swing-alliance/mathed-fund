"""此处用于写自动化执行的逻辑"""
from PyQt5.QtWidgets import  QMainWindow
from PyQt5.QtCore import QTimer
from pannel_plan import ControlPanel
from sys_center import SysCentral
from PyQt5.QtWidgets import QApplication
from advanced_updatetool import Update_MainWindow
import sys
import os
import time

equity_path = os.path.join(os.getcwd(), 'my_types','Equity')

def auto_submit(main_window: QMainWindow):
    print("--- 自动化执行器已启动 ---")
    main_window.auto_timer = QTimer(main_window)
    if not hasattr(main_window, 'ischecked'):
        main_window.ischecked = check_update()
    if not hasattr(main_window, 'auto_locker'):
        main_window.auto_locker = False
    if not hasattr(main_window, 'cal_sharpe'):
        main_window.cal_sharpe = False
    def monitor_loop():
        # 如果锁是 True，直接跳过本次循环
        if main_window.auto_locker:
            return
        central = main_window.centralWidget()
        if not central: return
        if not main_window.ischecked:
            print("检测到数据过旧，启动更新器...")
            main_window.auto_locker = True # 锁定
            run_external_job(main_window)
            
            # 注意：不要在这里设 auto_locker = False！
            # 必须等更新器窗口关闭后，通过信号来解锁。
            return
        if isinstance(central, SysCentral):
            main_window.auto_locker = True
            QTimer.singleShot(1000, lambda: (central.stock_button.click(), setattr(main_window, 'auto_locker', False)))
            return
        if isinstance(central, ControlPanel):
            if "股票" in central.index_label.text() and not getattr(main_window, 'cal_sharpe', False):
                main_window.auto_locker = True # 锁定，防止重复弹窗
                print("准备排序...")
                QTimer.singleShot(500, main_window.group_sort_by_largest_sharpe_60days)
                QTimer.singleShot(10000, lambda: setattr(main_window, 'auto_locker', False))
                main_window.cal_sharpe = True
                return
            if "当前计划60天夏普" in central.index_label.text() and main_window.cal_sharpe:
                main_window.auto_timer.stop()
                main_window.auto_locker = True
                main_window.export_batch_analysis()
                main_window.return_market_index()
                print("--- 任务圆满完成 ---")
    main_window.auto_timer.timeout.connect(monitor_loop)
    main_window.auto_timer.start(4000)




def run_external_job(main_window):
    """运行独立的更新器窗口并绑定解锁信号"""
    if not hasattr(main_window, 'update_win') or main_window.update_win is None:
        from PyQt5.QtCore import Qt
        main_window.update_win = Update_MainWindow()
        main_window.update_win.setAttribute(Qt.WA_DeleteOnClose)
        def on_update_finished():
            print("更新窗口已关闭，正在解锁...")
            main_window.auto_locker = False
            main_window.ischecked = True # 更新状态位，让 monitor_loop 下次进入新场景
            main_window.update_win = None # 清空引用
        main_window.update_win.destroyed.connect(on_update_finished)
    main_window.update_win.show()
    QTimer.singleShot(1000, main_window.update_win.start_auto_logic)


def check_update():
    """检查Equity目录下是否有文件在过去两小时内被更新过"""
    for file in os.listdir(equity_path)[:500]:
        if file.endswith('.csv'):
            file_path = os.path.join(equity_path, file)
            modified_time = os.path.getmtime(file_path)
            current_time = time.time()
            if current_time - modified_time > 5*3600:
                return False
    return True



