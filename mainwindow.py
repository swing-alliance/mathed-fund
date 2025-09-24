import os
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QWidget, QDialog
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import QSize 
from qwidget import CsvGraphWidget
from qdialogue import ArimaConfigDialog, pulldata_dialog, FourierConfigDialog
from utils.pull import fetch_and_save_fund_csv
from utils.refresh import update_found_folder
from pannel_plan import ControlPanel
# from calculate import ArimaPredictor



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("金融计算系统")
        self.setMinimumSize(QSize(1200, 800)) # 设置一个更大的初始窗口大小
        self._create_menu_bar()
        self.setCentralWidget(QWidget())
        self.attention_now=None#当前关注的csvgraphwidget，df
        self.attention_path=None#当前关注的csv路径

    def _create_menu_bar(self):
        # 创建菜单栏
        menu_bar = self.menuBar()
        menu_bar.setFont(QFont("微软雅黑", 11))
        file_menu = menu_bar.addMenu("文件")
        calculate_menu = menu_bar.addMenu("计算")
        plan_menu = menu_bar.addMenu("定投计划")
        setting_menu = menu_bar.addMenu("设置")
        # 添加菜单项
        load_action = QAction("加载文件", self)
        load_action.triggered.connect(self.show_graph_for_file)
        pull_action = QAction("拉取数据入库", self)
        pull_action.triggered.connect(self.pull_data_by_rules)

        pull_black_horse_action = QAction("从库中拉取黑马数据(高级)", self)

       
        file_menu.addAction(load_action)
        calculate_menu.addAction("arima", self.use_arima)
        calculate_menu.addAction("fourier", self.use_fourier)
        plan_menu.addAction("计划主页", self.load_plan_pannel)
        plan_menu.addAction(pull_action)
        plan_menu.addAction("更新库中数据",self.update_found_folder)
        plan_menu.addAction(pull_black_horse_action)


    def update_found_folder(self):
        update_found_folder()

    def pull_data_by_rules(self):
        """按照规则拉取数据"""
        dialog = pulldata_dialog(self)  # QDialog 输入基金代码
        if dialog.exec_() == QDialog.Accepted:  # 用户点击确定
            codes = dialog.codes  # 获取输入数组
            if codes:
                # 调用 pull.py 的函数拉取 CSV
                fetch_and_save_fund_csv(codes)
                QMessageBox.information(self, "成功", f"已拉取代码: {', '.join(codes)}")
            else:
                QMessageBox.warning(self, "取消", "未输入任何代码")


    def show_graph_for_file(self, file_path=None):
        """
        根据给定的文件路径绘制图表并设置为中心部件。
        如果没有提供文件路径，则弹出文件选择对话框。
        """
        # 如果没有传入文件路径，则弹出文件选择对话框
        if not file_path:
            data_dir = os.path.join(os.getcwd(), 'found')
            if not os.path.exists(data_dir):
                QMessageBox.warning(self, "错误", "未找到'found'文件夹。")
                return
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择基金数据文件",
                data_dir,
                "CSV 文件 (*.csv)"
            )
        
        # 只有当成功获取到文件路径时才继续执行
        if file_path:
            try:
                # 把csv读成dataframe，pandas格式
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='gbk')
                # 检查必要的列
                if '净值日期' not in df.columns or '单位净值' not in df.columns:
                    QMessageBox.warning(self, "错误", "CSV文件缺少必要的列,'净值日期' 或 '单位净值'")
                    return
                # 创建新的图表部件
                new_graph_widget = CsvGraphWidget(df)
                # 删除旧的中心部件
                old_widget = self.centralWidget()
                if old_widget:
                    old_widget.deleteLater()
                # 设置新的中心部件
                self.setCentralWidget(new_graph_widget)
                self.attention_now = new_graph_widget
                self.attention_path = file_path
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载或绘制数据失败: {e}")

    def use_arima(self):
        """
        处理 ARIMA 预测请求。
        """
        if self.attention_now is None:
            QMessageBox.warning(self, "错误", "请先加载数据。")
            return
        # 获取当前显示的图表 Qwidget
        render_now = self.centralWidget()
        if not isinstance(render_now, CsvGraphWidget):
            QMessageBox.warning(self, "错误", "当前窗口不是基金净值图表。")
            return
        dialog = ArimaConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            p, d, q = dialog.get_params()
            render_now.use_arima(p, d, q, periods=30)

        else:
            QMessageBox.information(self, "信息", "ARIMA功能已取消。")

    def use_fourier(self):
        if self.attention_now is None:
            QMessageBox.warning(self, "错误", "请先加载数据。")
            return
        render_now = self.centralWidget()
        if not isinstance(render_now, CsvGraphWidget):
            QMessageBox.warning(self, "错误", "当前窗口不是基金净值图表。")
            return
        dialogue = FourierConfigDialog(self)
        if dialogue.exec_() == QDialog.Accepted:
            order, period, custom_period, is_trend, sampling, window, smoothing, expect_days, extrapolation_strategy, is_fit_exact = dialogue.get_params()
            render_now.use_fourier(order=order, period=period, custom_period=custom_period, is_trend=is_trend, sampling=sampling, window=window, smoothing=smoothing, expect_days=expect_days, extrapolation_strategy=extrapolation_strategy, overfit=is_fit_exact)
        else:
            QMessageBox.information(self, "信息", "傅里叶变换功能已取消。")


    def load_plan_pannel(self):
        self.control_panel = ControlPanel()
        self.control_panel.visualize_requested.connect(self.show_graph_for_file)
        self.setCentralWidget(self.control_panel)