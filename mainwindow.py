import os
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QWidget, QDialog,QStackedWidget, QProgressDialog
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import QSize,QThread, pyqtSignal
from csvqwidget import CsvGraphWidget
from qdialogue import  pulldata_dialog,GroupConfigDialog,List_group_dialog
from utils.pull import fetch_and_save_fund_csv
from my_types.nice_utils import update_files
from pannel_plan import ControlPanel
from sys_center import SysCentral
import shutil


balanced_path = os.path.join(os.getcwd(), 'my_types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'my_types','Equity')
index_path = os.path.join(os.getcwd(), 'my_types','Index')
Qdii_path = os.path.join(os.getcwd(), 'my_types','Qdii')
cache_path = os.path.join(os.getcwd(), 'mapping','mapping_latestdate.csv')
groups_path = os.path.join(os.getcwd(), 'groups')
to_worker_path = os.path.join(os.getcwd(), 'to_worker')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("金融计算系统")
        self.setMinimumSize(QSize(1200, 800)) # 设置一个更大的初始窗口大小
        self._create_menu_bar()
        self.attention_now=None#当前关注的csvgraphwidget，df,窗口
        self.attention_path=None#当前关注的csv路径
        self.last_loaded_group=None
        self.load_sys_central()
        
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.setFont(QFont("微软雅黑", 12))
        file_menu = menu_bar.addMenu("文件")
        plan_menu = menu_bar.addMenu("计划")
        data_menu = menu_bar.addMenu("数据")
        calculate_menu = menu_bar.addMenu("计算")
        
        load_action = QAction("加载文件", self)
        load_action.triggered.connect(self.show_graph_for_file)
        add_group_action = QAction("创建分组", self)
        add_group_action.triggered.connect(lambda:self.add_group())
        load_group_action = QAction("加载分组", self)
        load_group_action.triggered.connect(lambda:self.load_group(groups_path))
        load_last_group_action = QAction("回到分组", self)
        load_last_group_action.triggered.connect(lambda:self.load_group(last_group_path=self.last_loaded_group))
        del_group_action = QAction("删除分组", self)
        del_group_action.triggered.connect(lambda:self.del_group(groups_path))

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
        updateBalanced_action.triggered.connect(lambda: self.start_file_update(balanced_path, cache_path))
        updateEquity_action = QAction("更新Equity数据", self)
        updateEquity_action.triggered.connect(lambda: self.start_file_update(Equity_path, cache_path))
        updateindex_action = QAction("更新Index数据", self)
        updateindex_action.triggered.connect(lambda: self.start_file_update(index_path, cache_path))
        updateQdii_action = QAction("更新Qdii或另类数据", self)
        updateQdii_action.triggered.connect(lambda: self.start_file_update(Qdii_path, cache_path))

        batch_redirect_action = QAction("批量转到组(bug)", self)
        batch_redirect_action.triggered.connect(self.batch_redirect)
        group_resort_action = QAction("当前组重新排序夏普比最大", self)
        group_resort_action.triggered.connect(self.group_resort)
        group_resort_yearly_return_action = QAction("当前组年化收益排序最大", self)
        group_resort_yearly_return_action.triggered.connect(self.group_sort_by_max_yearly_return)
        group_resort_80days_yearly_return_action = QAction("当前组80天年化收益排序最大", self)
        group_resort_80days_yearly_return_action.triggered.connect(self.group_sort_by_80days_yearly_return)
        group_resort_30days_yearly_return_action = QAction("当前组30天年化收益排序最大", self)
        group_resort_30days_yearly_return_action.triggered.connect(self.group_sort_by_30days_yearly_return)
        group_resort_14days_yearly_return_action = QAction("当前组14天年化收益排序最大", self)
        group_resort_14days_yearly_return_action.triggered.connect(self.group_sort_by_14days_yearly_return) 
        group_resort_3days_yearly_return_action= QAction("当前组3天年化收益排序最大", self)
        group_resort_3days_yearly_return_action.triggered.connect(self.group_sort_by_3days_yearly_return)
        group_resort_votality_action = QAction("当前组年化波动率排序最大", self)
        group_resort_votality_action.triggered.connect(self.group_sort_by_votality)
        group_fileter_lowpoint_action = QAction("当前组过滤低点", self)
        group_fileter_lowpoint_action.triggered.connect(self.fileter_group_by_lowpoint)
        group_return_market_index_action = QAction("返回总体市场指数", self)
        group_return_market_index_action.triggered.connect(self.return_market_index)



        load_group_action.setFont(QFont('微软雅黑', 11))
        add_group_action.setFont(QFont('微软雅黑', 11))
        del_group_action.setFont(QFont('微软雅黑', 11))
        advanced_pull_action.setFont(QFont('微软雅黑', 11))
        pull_action.setFont(QFont('微软雅黑', 11))
        load_action.setFont(QFont('微软雅黑', 11))
        load_last_group_action.setFont(QFont('微软雅黑', 11))
        updateQdii_action.setFont(QFont('微软雅黑', 11))
        index_action.setFont(QFont('微软雅黑', 11))
        qdii_action.setFont(QFont('微软雅黑', 11))
        balenced_action.setFont(QFont('微软雅黑', 11))
        equity_action.setFont(QFont('微软雅黑', 11))
        updateBalanced_action.setFont(QFont('微软雅黑', 11))
        updateEquity_action.setFont(QFont('微软雅黑', 11))
        updateindex_action.setFont(QFont('微软雅黑', 11))
        planpage_action.setFont(QFont('微软雅黑', 11))
        batch_redirect_action.setFont(QFont('微软雅黑', 11))
        group_resort_action.setFont(QFont('微软雅黑', 11))
        group_resort_yearly_return_action.setFont(QFont('微软雅黑', 11))
        group_resort_votality_action.setFont(QFont('微软雅黑', 11))
        group_resort_80days_yearly_return_action.setFont(QFont('微软雅黑', 11))
        group_resort_30days_yearly_return_action.setFont(QFont('微软雅黑', 11))
        group_resort_3days_yearly_return_action.setFont(QFont('微软雅黑', 11))
        group_resort_14days_yearly_return_action.setFont(QFont('微软雅黑', 11))
        group_fileter_lowpoint_action.setFont(QFont('微软雅黑', 11))
        group_return_market_index_action.setFont(QFont('微软雅黑', 11))


        
        plan_menu.addAction(planpage_action)
        plan_menu.addAction(balenced_action)
        plan_menu.addAction(equity_action)
        plan_menu.addAction(index_action)
        plan_menu.addAction(qdii_action)
        file_menu.addAction(load_action)
        file_menu.addAction(load_group_action)
        file_menu.addAction(load_last_group_action)
        file_menu.addAction(add_group_action)
        file_menu.addAction(del_group_action)
        data_menu.addAction(pull_action)
        data_menu.addAction(advanced_pull_action)
        data_menu.addAction(updateBalanced_action)
        data_menu.addAction(updateEquity_action)
        data_menu.addAction(updateindex_action)
        data_menu.addAction(updateQdii_action)
        calculate_menu.addAction(batch_redirect_action)
        calculate_menu.addAction(group_resort_action)
        calculate_menu.addAction(group_resort_yearly_return_action)
        calculate_menu.addAction(group_resort_votality_action)
        
        calculate_menu.addAction(group_resort_80days_yearly_return_action)
        calculate_menu.addAction(group_resort_30days_yearly_return_action)
        calculate_menu.addAction(group_resort_14days_yearly_return_action)
        calculate_menu.addAction(group_resort_3days_yearly_return_action)
        calculate_menu.addAction(group_fileter_lowpoint_action)
        calculate_menu.addAction(group_return_market_index_action)


        
        


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
        dialog = GroupConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            group_name = dialog.get_group_name()
            description_text = dialog.get_description_text()
            if "(系统)" in group_name or "系统" in group_name:
                QMessageBox.warning(self, "错误", "分组名称不能包含 '(系统)' 字符。")
                return
            if group_name:
                try:
                    this_group_path = os.path.join(groups_path, group_name)
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
                        if "(系统)" in self.to_selected_group_path:
                            QMessageBox.information(self, "信息", "系统分组不能删除。")
                            return
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
        


    def load_group(self, path=None,last_group_path=None):
        """加载分组"""
        try:
            if last_group_path:
                self.load_plan_pannel(base_path=last_group_path)
                return
            List_group_dialog_instance = List_group_dialog(groups__path=path,title="选择要加载的分组",parent=self)
            if List_group_dialog_instance.exec_() == QDialog.Accepted:
                selected_group_path = List_group_dialog_instance.get_selected_group_path()
                if selected_group_path:
                    self.load_plan_pannel(base_path=selected_group_path)
                    self.last_loaded_group=selected_group_path
                else:
                    QMessageBox.information(self, "信息", "未选择任何分组。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载分组失败: {e}")

    

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



    def batch_redirect(self):
        """计算后批量导入文件到组"""
        print("正在执行我")
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            for card in central_widget.loaded_cards.values():
                isthis_consider_risky_reward,isthis_consider_long_term_return,isthis_consider_low_point=card.auto_calculate_type()
                if isthis_consider_risky_reward:
                    risky_reward_group_path = os.path.join(os.getcwd(), "groups", "危险回报观察组(系统)")
                    card.add_to_group(risky_reward_group_path)
                    print("放在危险回报分组")
                    
                elif isthis_consider_long_term_return:
                    long_term_return_group_path = os.path.join(os.getcwd(), "groups", "长期收益观察组(系统)")
                    card.add_to_group(long_term_return_group_path)
                    print("放在长期收益分组")
                elif isthis_consider_low_point:
                    low_point_group_path = os.path.join(os.getcwd(), "groups", "黑马或白马")
                    card.add_to_group(low_point_group_path)
                    print("放在其他分组")
                else:
                    print("不放在任何分组")

    def group_resort(self):
        """分组重排"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self()#pannel_plan中定义
    
    def group_sort_by_max_yearly_return(self):
        """分组重排, 按最大年化收益排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_largest_yearly_return()

    def group_sort_by_votality(self):
        """分组重排, 按波动率排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_largest_votolity()

    def group_sort_by_80days_yearly_return(self):
        """分组重排, 按80天年化收益排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_80days_yearly_return()

    def group_sort_by_30days_yearly_return(self):
        """分组重排, 按30天年化收益排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_30days_yearly_return()
    
    def group_sort_by_14days_yearly_return(self):
        """分组重排, 按14天年化收益排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_14days_yearly_return()

    def group_sort_by_3days_yearly_return(self):
        """分组重排, 按3天年化收益排序"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.resort_self_by_3days_yearly_return()

    def fileter_group_by_lowpoint(self):
        """分组重排, 按低点过滤"""
        print("正在过滤低点")
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.filter_self_by_consider_lowpoint()

    def return_market_index(self):
        """返回总体市场指数"""
        central_widget = self.centralWidget()
        if isinstance(central_widget, ControlPanel):
            central_widget.return_market_general_index()


    def start_file_update(self,file_path,cache_path):
            """启动文件更新线程"""
            Font=QFont("微软雅黑", 10)
            self.setFont(Font)
            self.worker = FileUpdateWorker(update_files, file_path, cache_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)

            self.progress_dialog = QProgressDialog(f"执行中，{os.path.basename(file_path)}更新中...共{len(os.listdir(file_path))}个文件", "取消", 0, 100, self)
            self.progress_dialog.setWindowTitle("文件更新")
            self.progress_dialog.setModal(True)  # 确保弹窗阻塞界面
            self.progress_dialog.setValue(0)
            self.progress_dialog.setFont(QFont('微软雅黑', 10))
            self.progress_dialog.setFixedSize(600, 100)
            self.progress_dialog.canceled.connect(self.on_cancel_button_clicked)
            self.worker.start()

    def update_progress(self, current, total):
        """更新进度条"""
        progress = int((current / total) * 100)  # 计算百分比
        self.progress_dialog.setValue(progress)  # 更新进度对话框的进度

    def on_finished(self):
        """完成后的处理"""
        self.progress_dialog.setValue(100)  # 设置进度条为 100%
        QMessageBox.information(self, "完成", "文件更新完成,请刷新界面查看最新数据。")

    def on_error(self, error_message):
        """错误处理"""
        self.progress_dialog.setValue(100)  # 假设更新失败也设置为 100%，用户看到更新结束
        QMessageBox.critical(self, "错误", f"发生错误: {error_message}")
    def on_cancel_button_clicked(self):
        self.worker.terminate()

class FileUpdateWorker(QThread):
    progress = pyqtSignal(int, int)  # 用于传递进度的信号 (当前文件, 总文件数)
    finished = pyqtSignal()  # 用于表示任务完成的信号
    error = pyqtSignal(str)  # 用于传递错误信息的信号
    def __init__(self, update_func, file_path, cache_path):
        super().__init__()
        self.update_func = update_func
        self.file_path = file_path
        self.cache_path = cache_path
    def run(self):
        try:
            self.update_func(self.file_path, self.cache_path, self.report_progress)
            self.finished.emit()  # 任务完成信号
        except Exception as e:
            self.error.emit(str(e))  # 发生错误时发出错误信号
    def report_progress(self, current, total):
        """更新进度条"""
        self.progress.emit(current, total)

















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

