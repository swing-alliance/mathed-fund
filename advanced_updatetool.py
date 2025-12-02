from PyQt5.QtWidgets import (QApplication, QPushButton, QProgressDialog, 
                             QVBoxLayout, QWidget, QCheckBox, QHBoxLayout, 
                             QGroupBox, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont 
from PyQt5.QtWidgets import QDesktopWidget
import time
import os
import akshare as ak
import pandas as pd
import threading
from PyQt5.QtWidgets import QSpinBox
from concurrent.futures import ThreadPoolExecutor, as_completed, FIRST_COMPLETED, wait

# 路径定义
qdii_path = os.path.join(os.getcwd(), 'my_types', 'Qdii')
equity_path = os.path.join(os.getcwd(), 'my_types', 'Equity')
index_path = os.path.join(os.getcwd(), 'my_types', 'Index')
balanced_path = os.path.join(os.getcwd(), 'my_types', 'Balanced')
mapping_latestdate_path = os.path.join(os.getcwd(), 'mapping', 'mapping_latestdate.csv')

class FastWorkerThread(QThread):
    progress = pyqtSignal(int, int, str)  # 当前, 总数, 当前处理的基金类型
    finished = pyqtSignal()
    def __init__(self, paths, max_workers=10):
        """
        paths: 要处理的路径列表，如 [qdii_path, equity_path]
        """
        super().__init__()
        self.paths = paths
        self.max_workers = max_workers
        self.df_lock = threading.Lock()
        self._is_running = True  # 控制线程运行标志
        self._executor = None    # 保存executor引用
        if os.path.exists(mapping_latestdate_path):
            self.mapping_latest_df = pd.read_csv(mapping_latestdate_path)
        else:
            self.mapping_latest_df = pd.DataFrame(columns=['path', 'latest_date'])
    
    def run(self):
        try:
            start_time = time.time()
            total_processed = 0
            total_files = 0
            for path in self.paths:
                if not self._is_running:
                    break
                total_files += len([f for f in os.listdir(path) if f.endswith('.csv')])
            for path in self.paths:
                if not self._is_running:
                    break
                fund_type = os.path.basename(path)  # Qdii, Equity等
                files = [f for f in os.listdir(path) if f.endswith('.csv')]
                
                if not files:
                    continue
                self.progress.emit(total_processed, total_files, f"正在处理: {fund_type}")
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
                future_to_file = {}
                
                try:
                    for f in files:
                        if not self._is_running:
                            break
                        future = self._executor.submit(self._fetch_single, path, f.split('.')[0])
                        future_to_file[future] = f
                    completed = 0
                    while future_to_file and self._is_running:
                        # 使用带超时的wait，以便检查终止标志
                        done, not_done = wait(
                            future_to_file.keys(), 
                            timeout=0.5,  # 0.5秒检查一次是否应该停止
                            return_when=FIRST_COMPLETED
                        )
                        
                        for future in done:
                            if not self._is_running:
                                break
                            try:
                                future.result(timeout=0.1)
                            except Exception:
                                pass  # 忽略已完成任务的异常
                            
                            completed += 1
                            current = total_processed + completed
                            self.progress.emit(current, total_files, f"处理中: {fund_type}")
                            del future_to_file[future]
                        if not self._is_running:
                            break
                finally:
                    if self._executor:
                        self._executor.shutdown(wait=False, cancel_futures=True)
                        self._executor = None
                total_processed += len(files)
            
            if self._is_running:  # 只有正常完成才保存
                with self.df_lock:
                    self.mapping_latest_df.to_csv(mapping_latestdate_path, index=False)
                
                elapsed = time.time() - start_time
                print(f'✅ 任务完成！耗时: {elapsed:.2f}秒，处理 {total_processed} 个基金')
                self.finished.emit()
            else:
                print('⚠️ 任务被中断')
        except Exception as e:
            print(f'❌ 线程运行出错: {e}')
            self.finished.emit()
    
    def _fetch_single(self, path, fund_code):
        """处理单个基金"""
        if not self._is_running:
            return False
            
        try:
            df = ak.fund_open_fund_info_em(fund_code, indicator="累计净值走势")
            latest_date = df['净值日期'].max().strftime('%Y-%m-%d')
            file_path = os.path.join(path, f"{fund_code}.csv")
            
            with self.df_lock:
                mask = self.mapping_latest_df['path'].apply(
                    lambda x: os.path.normpath(str(x)) == os.path.normpath(file_path)
                )
                
                if mask.any():
                    self.mapping_latest_df.loc[mask, 'latest_date'] = latest_date
                else:
                    new_row = pd.DataFrame({
                        'path': [os.path.normpath(file_path)], 
                        'latest_date': [latest_date]
                    })
                    self.mapping_latest_df = pd.concat(
                        [self.mapping_latest_df, new_row], 
                        ignore_index=True
                    )
            
            if self._is_running:  # 再次检查，防止在写入文件时被中断
                df.to_csv(file_path, index=False)
            return True
            
        except Exception as e:
            if self._is_running:  # 只在运行状态才打印错误
                print(f"处理 {fund_code} 失败: {e}")
            return False
    
    def stop(self):
        """安全停止线程"""
        self._is_running = False
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
        self.terminate()
        self.wait(2000)  # 等待2秒

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_paths = []  # 存储用户选择的路径
        self.globalfont=QFont("微软雅黑", 10)
        self.initUI()
        
    def initUI(self):
        self.setFont(self.globalfont)
        self.setWindowTitle('进阶基金数据处理工具')
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        title = QLabel('选择要处理的基金类型')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        group = QGroupBox("基金类型")
        group_layout = QVBoxLayout()
        self.checkboxes = {}
        path_configs = [
            ('QDII基金', qdii_path, 'qdii'),
            ('股票基金', equity_path, 'equity'),
            ('指数基金', index_path, 'index'),
            ('平衡基金', balanced_path, 'balanced')
        ]
        group.setMinimumWidth(300)  # 设置最小宽度
        group_layout.setAlignment(Qt.AlignCenter)
        for name, path, key in path_configs:
            # 检查路径是否存在
            path_exists = os.path.exists(path)
            file_count = len([f for f in os.listdir(path) if f.endswith('.csv')]) if path_exists else 0
            checkbox = QCheckBox(f"{name} ({file_count}个文件)")
            checkbox.path = path  # 将路径绑定到checkbox
            checkbox.setEnabled(path_exists)
            if not path_exists:
                checkbox.setToolTip(f"路径不存在: {path}")
            group_layout.addWidget(checkbox)
            self.checkboxes[key] = checkbox
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # 并发控制
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("并发数:"))
        
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 20)
        self.workers_spin.setValue(10)
        self.workers_spin.setToolTip("同时处理的线程数，建议8-12")
        control_layout.addWidget(self.workers_spin)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 全选/取消按钮
        btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton('全选')
        self.btn_select_all.clicked.connect(self.select_all)
        btn_layout.addWidget(self.btn_select_all)
        
        self.btn_deselect_all = QPushButton('取消全选')
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.btn_deselect_all)
        
        layout.addLayout(btn_layout)
        
        # 开始按钮
        self.btn_start = QPushButton('开始处理')
        self.btn_start.clicked.connect(self.start_task)
        layout.addWidget(self.btn_start)
        
        # 停止按钮
        self.btn_stop = QPushButton('停止任务')
        self.btn_stop.clicked.connect(self.stop_task)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)
        
        # 状态标签
        self.status_label = QLabel('就绪 - 请选择基金类型')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        self.center_window()
        
    def center_window(self):
        """将窗口置于屏幕中央"""
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def select_all(self):
        """全选"""
        for checkbox in self.checkboxes.values():
            if checkbox.isEnabled():
                checkbox.setChecked(True)
    
    def deselect_all(self):
        """取消全选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_paths(self):
        """获取用户选中的路径"""
        selected = []
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked() and checkbox.isEnabled():
                selected.append(checkbox.path)
        return selected
    
    def start_task(self):
        """开始处理任务"""
        # 获取选中的路径
        self.selected_paths = self.get_selected_paths()
        
        if not self.selected_paths:
            self.status_label.setText("⚠️ 请至少选择一个基金类型")
            return
        total_files = 0
        for path in self.selected_paths:
            total_files += len([f for f in os.listdir(path) if f.endswith('.csv')])
        
        if total_files == 0:
            self.status_label.setText("⚠️ 所选类型中没有CSV文件")
            return
        
        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            f"准备处理 {total_files} 个基金...", 
            "取消", 
            0, 
            100, 
            self
        )
        self.progress_dialog.setWindowTitle("处理进度")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.worker = FastWorkerThread(
            self.selected_paths, 
            max_workers=self.workers_spin.value()
        )
        
        # 连接信号
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.task_finished)
        self.progress_dialog.canceled.connect(self.stop_task)
        
        # 更新界面状态
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(False)
        
        self.status_label.setText(f"处理中: 0/{total_files}")
        
        # 开始任务
        self.worker.start()
        self.progress_dialog.show()
    
    def update_progress(self, current, total, fund_type):
        """更新进度"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_dialog.setValue(percent)
            self.progress_dialog.setLabelText(
                f"{fund_type}\n进度: {current}/{total} ({percent}%)"
            )
            self.status_label.setText(f"处理中: {current}/{total} - {fund_type}")
    
    def task_finished(self):
        """任务完成"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        # 重新启用复选框
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(True)
        
        # 更新状态
        self.status_label.setText("✅ 任务完成")
    
    def stop_task(self):
        """停止任务"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
        
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(True)
        
        self.status_label.setText("⏹️ 任务已停止")
    
    def closeEvent(self, event):
        """重写关闭事件，确保线程安全退出"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '任务正在运行，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    ret = app.exec_()

    if hasattr(window, 'worker') and window.worker.isRunning():
        window.worker.stop()
    
    sys.exit(ret)