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
    """自动化提交逻辑函数"""
    print("--- 自动化执行器已启动 ---")
    # 1. 识别中心组件（只在启动时打印一次，用于调试）
    central = main_window.centralWidget()
    main_window.ischecked = check_update()
    if central:
        print(f"当前监控中心组件类型: {central.__class__.__name__}")
    main_window.auto_timer = QTimer(main_window)
    def monitor_loop():
        central = main_window.centralWidget()
        if not central:
            "跳过，未找到中心组件"
            return
        if not main_window.ischecked:
            run_external_job(main_window)
            main_window.reload_mapping()
            main_window.ischecked = True
            return
        if isinstance(central,SysCentral):
            print(f"从系统中心开始自动化")
            time.sleep(1)
            central.stock_button.click()
        if isinstance(central, ControlPanel):
            print(f"控制面板")
            if "股票" in central.index_label.text():
                QTimer.singleShot(500,main_window.group_sort_by_largest_sharpe_60days)
                main_window.cal_sharpe = True
                return
            if "当前计划60天夏普" in central.index_label.text() and main_window.cal_sharpe:
                main_window.export_batch_analysis()
                main_window.return_market_index()
                main_window.auto_timer.stop()
                print("--- 自动化执行器已完成任务并停止 ---")
        return
    main_window.auto_timer.timeout.connect(monitor_loop)
    main_window.auto_timer.start(4000)  # 每4秒检查一次


def run_external_job(main_window):
    """运行独立的更新器窗口"""
    if not hasattr(main_window, 'update_win'):
        main_window.update_win = Update_MainWindow()

    main_window.update_win.show()
    # 触发你之前写的代码层面的自动化（勾选并开始）
    QTimer.singleShot(1000, main_window.update_win.start_auto_logic)



def check_update():
    """检查Equity目录下是否有文件在过去两小时内被更新过"""
    for file in os.listdir(equity_path)[:500]:
        if file.endswith('.csv'):
            file_path = os.path.join(equity_path, file)
            modified_time = os.path.getmtime(file_path)
            current_time = time.time()
            if current_time - modified_time > 6*3600:
                return False
    return True



