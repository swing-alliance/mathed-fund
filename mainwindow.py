import os
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QWidget, QDialog,QStackedWidget
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import QSize 
from csvqwidget import CsvGraphWidget
from qdialogue import  pulldata_dialog,GroupConfigDialog,List_group_dialog
from utils.pull import fetch_and_save_fund_csv
from my_types.nice_utils import update_files
from pannel_plan import ControlPanel
from sys_center import SysCentral
import shutil

# from calculate import ArimaPredictor
balanced_path = os.path.join(os.getcwd(), 'my_types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'my_types','Equity')
index_path = os.path.join(os.getcwd(), 'my_types','Index')
Qdii_path = os.path.join(os.getcwd(), 'my_types','Qdii')
cache_path = os.path.join(os.getcwd(), 'mapping','mapping_latestdate.csv')
groups__path = os.path.join(os.getcwd(), 'groups')
to_worker_path = os.path.join(os.getcwd(), 'to_worker')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("金融计算系统")
        self.setMinimumSize(QSize(1200, 800)) # 设置一个更大的初始窗口大小
        self._create_menu_bar()
        self.attention_now=None#当前关注的csvgraphwidget，df,窗口
        self.attention_path=None#当前关注的csv路径
        self.load_sys_central()
        
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.setFont(QFont("微软雅黑", 12))
        file_menu = menu_bar.addMenu("文件")
        plan_menu = menu_bar.addMenu("定投计划")
        data_menu = menu_bar.addMenu("数据")
        calculate_menu = menu_bar.addMenu("计算")
        
        load_action = QAction("加载文件", self)
        load_action.triggered.connect(self.show_graph_for_file)
        add_group_action = QAction("添加分组", self)
        add_group_action.triggered.connect(self.add_group)
        load_group_action = QAction("加载分组", self)
        del_group_action = QAction("删除分组", self)
        del_group_action.triggered.connect(lambda:self.del_group(groups__path))

        pull_action = QAction("拉取数据入库", self)
        pull_action.triggered.connect(self.pull_data)
        

        advanced_pull_action = QAction("拉取数据入库(高级)", self)
        advanced_pull_action.triggered.connect(self.advanced_pull_data)
        

        planpage_action = QAction("计划主页", self)
        planpage_action.triggered.connect(lambda:self.load_sys_central())
        

        balenced_action = QAction("从混合型开始", self)
        balenced_action.triggered.connect(lambda:self.load_plan_pannel(balanced_path))
        equity_action = QAction("从股票型开始", self)
        equity_action.triggered.connect(lambda:self.load_plan_pannel(Equity_path))
        index_action = QAction("从指数型开始", self)
        index_action.triggered.connect(lambda:self.load_plan_pannel(index_path))
        qdii_action = QAction("从QDII或特殊商品开始", self)
        qdii_action.triggered.connect(lambda:self.load_plan_pannel(Qdii_path))
        
        updateBalanced_action = QAction("更新Balanced数据", self)
        updateBalanced_action.triggered.connect(lambda: update_files(balanced_path, cache_path))
        updateEquity_action = QAction("更新Equity数据", self)
        updateEquity_action.triggered.connect(lambda: update_files(Equity_path, cache_path))
        updateindex_action = QAction("更新Index数据", self)
        updateindex_action.triggered.connect(lambda: update_files(index_path, cache_path))
        updateQdii_action = QAction("更新Qdii或另类数据", self)
        updateQdii_action.triggered.connect(lambda: update_files(Qdii_path, cache_path))



        load_group_action.setFont(QFont('微软雅黑', 11))
        add_group_action.setFont(QFont('微软雅黑', 11))
        del_group_action.setFont(QFont('微软雅黑', 11))
        advanced_pull_action.setFont(QFont('微软雅黑', 11))
        pull_action.setFont(QFont('微软雅黑', 11))
        load_action.setFont(QFont('微软雅黑', 11))
        updateQdii_action.setFont(QFont('微软雅黑', 11))
        index_action.setFont(QFont('微软雅黑', 11))
        qdii_action.setFont(QFont('微软雅黑', 11))
        balenced_action.setFont(QFont('微软雅黑', 11))
        equity_action.setFont(QFont('微软雅黑', 11))
        updateBalanced_action.setFont(QFont('微软雅黑', 11))
        updateEquity_action.setFont(QFont('微软雅黑', 11))
        updateindex_action.setFont(QFont('微软雅黑', 11))
        planpage_action.setFont(QFont('微软雅黑', 11))

        plan_menu.addAction(planpage_action)
        plan_menu.addAction(balenced_action)
        plan_menu.addAction(equity_action)
        plan_menu.addAction(index_action)
        plan_menu.addAction(qdii_action)
        file_menu.addAction(load_action)
        file_menu.addAction(load_group_action)
        file_menu.addAction(add_group_action)
        file_menu.addAction(del_group_action)
        data_menu.addAction(pull_action)
        data_menu.addAction(advanced_pull_action)
        data_menu.addAction(updateBalanced_action)
        data_menu.addAction(updateEquity_action)
        data_menu.addAction(updateindex_action)
        data_menu.addAction(updateQdii_action)
        
        


    def pull_data(self):
        """拉取数据到found"""
        dialog = pulldata_dialog(self)  # QDialog 输入基金代码
        if dialog.exec_() == QDialog.Accepted:  # 用户点击确定
            codes = dialog.codes  # 获取输入数组
            if codes:
                fetch_and_save_fund_csv(codes)
                QMessageBox.information(self, "成功", f"已拉取代码: {', '.join(codes)}")
            else:
                QMessageBox.warning(self, "取消", "未输入任何代码")

    def advanced_pull_data(self):
        """高级拉取数据到found"""
        pass

    def show_graph_for_file(self, file_path=None):
        """
        根据给定的文件路径绘制图表并设置为中心部件。
        如果没有提供文件路径，则弹出文件选择对话框。
        """
        this_file_path = file_path
        if not this_file_path:
            data_dir = os.path.join(os.getcwd(), 'found')
            if not os.path.exists(data_dir):
                QMessageBox.warning(self, "错误", "未找到'found'文件夹。")
                return
            this_file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择基金数据文件",
                data_dir,
                "CSV 文件 (*.csv)"
            )
        if this_file_path:
            try:
                try:
                    df = pd.read_csv(this_file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(this_file_path, encoding='gbk')
                if '净值日期' not in df.columns :
                    QMessageBox.warning(self, "错误", "CSV文件缺少必要的列,'净值日期' ")
                    return
                new_graph_widget = CsvGraphWidget(df)
                old_widget = self.centralWidget()
                if old_widget:
                    old_widget.deleteLater()
                self.setCentralWidget(new_graph_widget)
                self.attention_now = new_graph_widget
                self.attention_path = this_file_path
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载或绘制数据失败: {e}")
        else:
            QMessageBox.warning(self, "错误", "未选择文件或文件路径为空。")


    def load_plan_pannel(self, base_path=None):
        """加载计划面板, 信号连接到控制面板"""
        current_control_panel = self.centralWidget()
        if isinstance(current_control_panel, ControlPanel):
            # 断开信号连接，先检查信号是否已连接
            try:
                current_control_panel.visualize_requested.disconnect(self.show_graph_for_file)
            except TypeError:
                pass  
            current_control_panel.deleteLater()
        self.control_panel = ControlPanel(base_path=base_path)
        self.control_panel.visualize_requested.connect(self.show_graph_for_file)
        self.setCentralWidget(self.control_panel)

    def load_sys_central(self):
        self.attention_now = SysCentral(parent_window=self)
        self.setCentralWidget(self.attention_now)


    def add_group(self):
        """添加分组"""
        dialog = GroupConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            group_name = dialog.get_group_name()
            description_text = dialog.get_description_text()
            if group_name:
                try:
                    this_group_path = os.path.join(groups__path, group_name)
                    os.makedirs(this_group_path, exist_ok=True)
                    description_file_path = os.path.join(this_group_path, f"{group_name}.txt")
                    with open(description_file_path, 'w', encoding='utf-8') as f:
                        f.write(description_text or '无描述')
                    QMessageBox.information(self, "成功", f"已添加分组: {group_name}\n描述: {description_text or '无'}")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"保存分组失败: {e}")
                    return
            else:
                QMessageBox.warning(self, "取消", "未输入分组名称")

    def del_group(self, path=None):
            """删除分组"""
            # 检查当前目录下是否有 groups 文件夹
            Font=QFont("微软雅黑", 10)
            self.setFont(Font)
            if "groups" not in os.listdir(os.getcwd()):
                QMessageBox.warning(self, "错误", "当前目录下没有 groups 文件夹。")
                return
            else:
                try:
                    self.isdoc = self.is_doc_exists(path)
                    if self.isdoc is False:
                        return
                    List_group_dialog_instance = List_group_dialog(groups__path=path,title="选择要删除的分组",parent=self)
                    if List_group_dialog_instance.exec_() == QDialog.Accepted:
                        self.to_selected_group_path = List_group_dialog_instance.get_selected_group_path()
                        print(f"用户选择的分组路径: {self.to_selected_group_path}")
                        if self.to_selected_group_path:
                            if os.path.isdir(self.to_selected_group_path):
                                try:
                                    shutil.rmtree(self.to_selected_group_path)
                                    QMessageBox.information(self, "信息", "已删除分组。")
                                except Exception as e:
                                    QMessageBox.warning(self, "错误", f"删除分组失败: {e}")
                            else:
                                QMessageBox.warning(self, "错误", "选择的路径不是一个有效的文件夹。")
                        else:
                            QMessageBox.information(self, "信息", "未选择任何分组或分组不存在。")
                    elif List_group_dialog_instance.result() == QDialog.Rejected:
                        return
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"删除分组失败: {e}")
                    return 


    def list_groups(self, path=None):
        """列出所有分组"""
        List_group_dialog_instance = List_group_dialog(groups__path=path)
        if List_group_dialog_instance.exec_() == QDialog.Accepted:
            selected_group_path = List_group_dialog_instance.on_item_double_clicked()
            if selected_group_path:
                self.del_group(selected_group_path)
            else:
                QMessageBox.information(self, "信息", "未选择任何分组。")
        

    def is_doc_exists(self,path=None):
        """检查路径下是否存在文件夹"""
        Font=QFont("微软雅黑", 10)
        self.setFont(Font)
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    return True
            QMessageBox.information(self, "系统", f"当前分组为空，请先添加分组。")
            return False
        except Exception as e:
            QMessageBox.warning(self, "错误", f"检查文件夹失败: {e}")    
            return False

        # calculate_menu.addAction(arima_action)
        # calculate_menu.addAction(fourier_action)
        # arima_action = QAction("arima", self)
        # arima_action.triggered.connect(self.use_arima)
        # arima_action.setFont(QFont('微软雅黑', 11))
        # fourier_action = QAction("fourier", self)
        # fourier_action.triggered.connect(self.use_fourier)
        # fourier_action.setFont(QFont('微软雅黑', 11))























    # def use_arima(self):
    #     """
    #     处理 ARIMA 预测请求。
    #     """
    #     if self.attention_now is None:
    #         QMessageBox.warning(self, "错误", "请先加载数据。")
    #         return
    #     # 获取当前显示的图表 Qwidget
    #     render_now = self.centralWidget()
    #     if not isinstance(render_now, CsvGraphWidget):
    #         QMessageBox.warning(self, "错误", "当前窗口不是基金净值图表。")
    #         return
    #     dialog = ArimaConfigDialog(self)
    #     if dialog.exec_() == QDialog.Accepted:
    #         p, d, q = dialog.get_params()
    #         render_now.use_arima(p, d, q, periods=30)

    #     else:
    #         QMessageBox.information(self, "信息", "ARIMA功能已取消。")

    # def use_fourier(self):
    #     if self.attention_now is None:
    #         QMessageBox.warning(self, "错误", "请先加载数据。")
    #         return
    #     render_now = self.centralWidget()
    #     if not isinstance(render_now, CsvGraphWidget):
    #         QMessageBox.warning(self, "错误", "当前窗口不是基金净值图表。")
    #         return
    #     dialogue = FourierConfigDialog(self)
    #     if dialogue.exec_() == QDialog.Accepted:
    #         order, period, custom_period, is_trend, sampling, window, smoothing, expect_days, extrapolation_strategy, is_fit_exact = dialogue.get_params()
    #         render_now.use_fourier(order=order, period=period, custom_period=custom_period, is_trend=is_trend, sampling=sampling, window=window, smoothing=smoothing, expect_days=expect_days, extrapolation_strategy=extrapolation_strategy, overfit=is_fit_exact)
    #     else:
    #         QMessageBox.information(self, "信息", "傅里叶变换功能已取消。")

