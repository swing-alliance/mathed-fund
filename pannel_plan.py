import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication,QMenu,QAction,QProgressDialog
)
from PyQt5.QtCore import QTimer
import pyperclip
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont ,QIcon
import pandas as pd
from projectcard import ProjectCard
from PyQt5.QtCore import QTimer
from fundholding import stocker_prompt
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import glob
import json
from threadworker import AssumingManager
from conclusion import generate_market_conclusion
from qdialogue import MultiRankChartWidget
from log.logsharp import save_to_log
import socket
from config.get_config import get_config,get_proxy_config
from log.analysislog100 import analysis_log_batch
import time
TO_WORKER = "to_worker"
FOUND_PATH = "found"
target_dir = os.path.join(os.getcwd(), 'static')
timenow = time.strftime('%Y-%m-%d', time.localtime(time.time()))
current_month = int(time.strftime('%m', time.localtime(time.time())))  # 获取当前月份
if 3 <= current_month <= 5:
    season = 'spring'
elif 6 <= current_month <= 8:
    season = 'summer'
elif 9 <= current_month <= 11:
    season = 'autumn'
else:
    season = 'winter'
pics = glob.glob(os.path.join(target_dir, f'{season}*.png'))
if not pics:
    picdefault = glob.glob(os.path.join(target_dir, 'infinite.png'))
pic=pics[0] if pics else picdefault[0]
balanced_path = os.path.join(os.getcwd(), 'my_types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'my_types','Equity')
index_path = os.path.join(os.getcwd(), 'my_types','Index')
Qdii_path = os.path.join(os.getcwd(), 'my_types','Qdii')
groups_path = os.path.join(os.getcwd(), 'groups')
flagged_tracking_path = os.path.join(os.getcwd(), 'track',"flagged.json")


class ControlPanel(QWidget):
    """控制面板（QWidget），带滚动区域"""
    visualize_requested = pyqtSignal(str)
    def __init__(self, parent=None,base_path=None,load_required_from=None):
        super().__init__(parent)
        self.load_required_from=load_required_from
        self.hidden_storage = QWidget()
        self.filtered_card_to_show=[]
        self.loaded_cards = {}#用于缓存已加载的卡片
        self.base_path = base_path # 当前所关注的文件夹路径
        self.file_nums = len(os.listdir(base_path))
        main_layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setFont(QFont('微软雅黑', 20))
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_project_from_found)
        self.index_label=self.what_label_now()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索项目...")
        self.search_input.setClearButtonEnabled(True) # 添加清除按钮
        self.search_input.setMaximumWidth(300)
        self.search_input.setFont(QFont('微软雅黑', 12))
        #QTimer 用于延时过滤
        self.filter_timer = QTimer(self)
        self.filter_timer.setSingleShot(True)  
        self.filter_timer.setInterval(10)      
        self.filter_timer.timeout.connect(self._perform_filtering) 
        self.search_input.textChanged.connect(self.start_filter_timer)
        

        top_bar.addWidget(self.add_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.search_input)
        top_bar.addStretch(1)  
        
        top_bar.addWidget(self.index_label, alignment=Qt.AlignRight)
        top_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addLayout(top_bar)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 自动扩展
        main_layout.addWidget(self.scroll_area)
        
        

        # 滚动内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)  # 卡片从上往下排
        self.scroll_layout.setContentsMargins(0, 0, 30, 0)
        self.scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            lambda min_val, max_val: self.scroll_content.setMinimumWidth(
                self.scroll_area.viewport().width() + 30
            )
        )
        self.load_projects_from_path(path=self.base_path)

    def add_project_from_found(self):
        """只允许在 found 文件夹下选择 CSV，并检查 TO_WORKER 文件夹是否已有该文件"""
        os.makedirs(FOUND_PATH, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", FOUND_PATH, "CSV Files (*.csv)"
        )
        if not file_path:
            return
        os.makedirs(TO_WORKER, exist_ok=True)
        target_path = os.path.join(TO_WORKER, os.path.basename(file_path))
        if os.path.exists(target_path):
            QMessageBox.warning(self, "警告", "该文件已经存在面板中！")
            return 
        try:
            shutil.copy(file_path, target_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"复制文件失败: {e}")
            return
        card = ProjectCard(target_path)
        card.visualize_requested.connect(self.visualize_requested.emit)
        self.scroll_layout.addWidget(card)




    def load_projects_from_path(self, path):
            """从 types 文件夹加载项目卡片，并将实例缓存起来。"""
            UPDATE_FREQUENCY = 2000
            def load_files_from_path(directory_path):
                """加载指定路径下的文件并更新进度框"""
                if not os.path.isdir(directory_path):
                    print(f"路径 {directory_path} 不存在或不是目录！")
                    return
                project_files = os.listdir(directory_path)
                self.file_nums = len(project_files)
                if not project_files:
                    print(f"路径 {directory_path} 中没有文件！")
                    return
                progress_dialog = QProgressDialog("正在加载文件...", "取消", 0, len(project_files), self)
                progress_dialog.setWindowIcon(QIcon(pic))
                progress_dialog.setWindowModality(Qt.WindowModal)  # 设置为模态对话框，防止其他操作
                progress_dialog.setCancelButton(None)  # 禁用取消按钮
                progress_dialog.setFont(QFont('微软雅黑', 10))
                progress_dialog.resize(600, 50)
                progress_dialog.show()  
                QApplication.processEvents() 
                for index, file_name in enumerate(project_files):
                    if file_name not in self.loaded_cards:
                        file_path = os.path.join(directory_path, file_name)
                        try:
                            card = ProjectCard(file_path,parent=self)
                            card.visualize_requested.connect(self.visualize_requested.emit)
                            self.scroll_layout.addWidget(card)
                            self.loaded_cards[file_name] = card
                        except Exception as e:
                            print(f"创建 ProjectCard 失败 ({file_name}): {e}")
                    if (index + 1) % UPDATE_FREQUENCY == 0 or (index + 1) == self.file_nums:
                        progress_dialog.setValue(index + 1)
                        QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        break
                progress_dialog.setValue(self.file_nums)
                QApplication.processEvents()
                progress_dialog.close()

            def load_projects_from_groups( this_group_path=None):
                """从组中加载项目卡片，并将实例缓存起来。"""
                csv_path = os.path.join(groups_path, 'group_cache.csv')
                df=pd.read_csv(csv_path,dtype=str)
                this_group_name=os.path.basename(this_group_path)
                selected_paths_series = df.loc[df['group_name'] == str(this_group_name), 'path']
                selected_paths = selected_paths_series.tolist()#缓存中读取后加载
                if not selected_paths:
                    print(f"分组 {this_group_name} 中没有项目！")
                    return
                self.file_nums = len(selected_paths)
                progress_dialog = QProgressDialog("正在加载文件...", "取消", 0, len(selected_paths), self)
                progress_dialog.setWindowIcon(QIcon(pic))
                progress_dialog.setWindowModality(Qt.WindowModal)  # 设置为模态对话框，防止其他操作
                progress_dialog.setCancelButton(None)  # 禁用取消按钮
                progress_dialog.setFont(QFont('微软雅黑', 10))
                progress_dialog.resize(600, 50)
                progress_dialog.show()  
                QApplication.processEvents() 
                for index, file_path in enumerate(selected_paths):
                    if file_path not in self.loaded_cards:
                        try:
                            card = ProjectCard(file_path,parent=self)
                            card.visualize_requested.connect(self.visualize_requested.emit)
                            self.scroll_layout.addWidget(card)
                            self.loaded_cards[file_path] = card
                        except Exception as e:
                            print(f"创建 ProjectCard 失败 ({file_path}): {e}")
                    if (index + 1) % 200 == 0 or (index + 1) == self.file_nums:
                        progress_dialog.setValue(index + 1)
                        QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        break
                progress_dialog.setValue(self.file_nums)
                QApplication.processEvents()
                progress_dialog.close()
            def load_project_from_goup_sys_manage(flag):
                """后面带(系统)的组"""
                if "标记的股票型(系统)" in self.base_path and flag == "系统":
                    paths=[]
                    try:
                        with open(flagged_tracking_path, 'r', encoding='utf-8') as f:
                            datas = json.load(f)
                        files=[file.split(".")[0] for file in os.listdir(Equity_path) if file.endswith(".csv")]
                        for data in datas:
                            if data in files:
                                path=Equity_path+"/"+data+".csv"
                                paths.append(path)
                        for everypath in paths:
                            if everypath not in self.loaded_cards:
                                try:
                                    card = ProjectCard(everypath,parent=self)
                                    card.visualize_requested.connect(self.visualize_requested.emit)
                                    self.scroll_layout.addWidget(card)
                                    self.loaded_cards[everypath] = card
                                except Exception as e:
                                    print(f"创建 ProjectCard 失败 ({everypath}): {e}")
                    except Exception as e:
                        print(f"读取标记股票型文件失败：{e}")
                        return


            if path == balanced_path:
                load_files_from_path(balanced_path)
            elif path == Equity_path:
                load_files_from_path(Equity_path)
            elif path == index_path:
                load_files_from_path(index_path)
            elif path == Qdii_path:
                load_files_from_path(Qdii_path)
            elif self.load_required_from == "groups":
                if "标记的股票型(系统)" in self.base_path:
                    load_project_from_goup_sys_manage("系统")
                else:
                    load_projects_from_groups(this_group_path=self.base_path)
            else:
                print("错误")




    def start_filter_timer(self):
        """当文本改变时调用，它会重置并启动定时器。"""
        if self.filter_timer.isActive():
            self.filter_timer.stop()
        self.filter_timer.start()


    def _perform_filtering(self):
        """实际的过滤逻辑。"""
        search_text = self.search_input.text().lower().strip()
        search_text = search_text.replace('（', '(').replace('）', ')')
        visible_cards = []
        for card in self.loaded_cards.values():
            target_title = card.fund_tittle.lower().replace('（', '(').replace('）', ')')
            target_fname = card.filename.lower().replace('（', '(').replace('）', ')')
            if not search_text or search_text in target_title or search_text in target_fname:
                visible_cards.append(card)
            self.setUpdatesEnabled(False)
        try:
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
                card.hide()
            for card in visible_cards:#写两个for比一个for快十倍
                if "过滤低点" in self.index_label.text():
                    if card.filename in self.filtered_card_to_show:
                        card.show()
                    else:
                        continue
                else:
                    card.show()
            for card in visible_cards:
                self.scroll_layout.addWidget(card)
        finally:
            self.setUpdatesEnabled(True)
            self.update()

            


    def what_label_now(self):
        """用于显示当前所关注的项目类"""
        qlabel = QLabel()
        qlabel.setFont(QFont('微软雅黑', 12))
        if self.base_path == balanced_path:
            qlabel.setText(f"混合型{self.file_nums}个")
        elif self.base_path == Equity_path:
            qlabel.setText(f"股票型{self.file_nums}个")
        elif self.base_path == index_path:
            qlabel.setText(f"指数型{self.file_nums}个")
        elif self.base_path == Qdii_path:
            qlabel.setText(f"QDII或另类{self.file_nums}个")
        elif "groups" in self.base_path:
            if "标记的股票型(系统)" in self.base_path:
                try:
                    with open(flagged_tracking_path, 'r', encoding='utf-8') as f:
                        data=json.load(f)
                        qlabel.setText(f"当前组策略:标记的股票型(系统)   {len(data)}个记录")
                        return qlabel
                except Exception as e:
                    print("系统失败")
                    return
            df=pd.read_csv(os.path.join(groups_path, 'group_cache.csv'),dtype=str)
            group_name=os.path.basename(self.base_path)
            matching_row = df[df['group_name'] == group_name]
            self.group_file_nums = len(matching_row)
            qlabel.setText(f"当前组策略:{os.path.basename(self.base_path)}   {self.group_file_nums}个记录")
            self.add_btn.hide()
        return qlabel



    def resort_self(self):
        """重新排序项目卡片按照365天夏普比率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="365天夏普比率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="365天夏普比率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组365天夏普比率排序")
            else:
                self.index_label.setText("当前计划365天夏普比率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def resort_self_by_largest_sharpe_60days(self):
        """重新排序项目卡片按照60天夏普比率从大到小,重点关注,有log功能记录"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="60天夏普比率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="60天夏普比率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            namelist = []
            showed_name = {}
            count = 1
            for card in sorted_cards_list:
                if not showed_name.get(card.fund_tittle):
                    showed_name[card.fund_tittle] = 1
                    namelist.append(card.fund_tittle)
                    count += 1
                if count > 100: break
            if "股票" in self.index_label.text() and is_daytime():
                save_to_log(namelist)
                
            if "组" in self.index_label.text():
                self.index_label.setText("当前组60天夏普比排序")
            else:
                self.index_label.setText("当前计划60天夏普比排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()
        

    def resort_self_by_80days_yearly_return(self):
        """重新排序项目卡片按照80天年化收益率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="80天年化收益率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="80天年化收益率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组80天年化收益率排序")
            else:
                self.index_label.setText("当前计划80天年化收益率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def resort_self_by_30days_yearly_return(self):
        """重新排序项目卡片按照30天年化收益率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="30天年化收益率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="30天年化收益率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组30天年化收益率排序")
            else:
                self.index_label.setText("当前计划30天年化收益率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def resort_self_by_14days_yearly_return(self):
        """重新排序项目卡片按照14天年化收益率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="14天年化收益率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="14天年化收益率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组14天年化收益率排序")
            else:
                self.index_label.setText("当前计划14天年化收益率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def resort_self_by_3days_yearly_return(self):
        """重新排序项目卡片按照3天年化收益率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="3天年化收益率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="3天年化收益率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组3天年化收益率排序")
            else:
                self.index_label.setText("当前计划3天年化收益率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def resort_self_by_largest_yearly_return(self):
        """重新排序项目卡片按照365天年化收益率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="365天年化收益率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="365天年化收益率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组365天年化收益率排序")
            else:
                self.index_label.setText("当前计划365天年化收益率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()


    def resort_self_by_largest_votolity(self):
        """重新排序项目卡片按照波动率从大到小"""
        from threadworker import LoadingDialog, SortWorker
        dialog = LoadingDialog(self,job="波动率")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="波动率")
        def on_finished(sorted_cards_list):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
            self.loaded_cards = {f"{card.filename}.csv": card for card in sorted_cards_list}
            for card in self.loaded_cards.values():
                self.scroll_layout.addWidget(card)
            if "组" in self.index_label.text():
                self.index_label.setText("当前组波动率排序")
            else:
                self.index_label.setText("当前波动率排序")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()

    def filter_self_by_consider_lowpoint(self):
        """过滤项目卡片只显示考虑低点的 (通过控制可见性实现，无重叠Bug)"""
        # filtered_cards = [card for card in self.loaded_cards.values() if card.return_decision().is_consider_lowpoint() is True]
        from threadworker import LoadingDialog, SortWorker
        config=get_config()
        dialog = LoadingDialog(self,job="过滤低点")
        cards_to_sort = list(self.loaded_cards.values())
        self.worker = SortWorker(cards_to_sort,job="过滤低点",config=config)
        def on_finished(filtered_cards):
            dialog.accept() # 关闭弹窗
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
                card.hide()
            for card in filtered_cards:
                self.filtered_card_to_show.append(card.filename)
                card.show()
            for card in filtered_cards:
                self.scroll_layout.addWidget(card)
            self.scroll_layout.invalidate() 
            status_type = "组" if "组" in self.index_label.text() else "计划"
            if "夏普" in self.index_label.text():
                self.index_label.setText(f"当前{status_type}60天夏普过滤低点 ({len(filtered_cards)})")
            else:
                self.index_label.setText(f"当前{status_type}过滤低点 ({len(filtered_cards)})")
        self.worker.finished_signal.connect(on_finished)
        dialog.finished.connect(self.worker.stop) # 对话框关闭则终止计算
        self.worker.start()
        dialog.exec()
        
    def export_batch_log_analysis(self):
        """展示批量log100的夏普分析结果"""
        if "夏普" in self.index_label.text():
            batchlog=[]
            count=1
            showed_name={}
            for card in self.loaded_cards.values():
                if count>100:
                    break
                if not showed_name.get(card.fund_tittle):
                    showed_name[card.fund_tittle]=1
                    batchlog.append(card.fund_tittle)
                    count+=1
                pass
            ranking_result=analysis_log_batch(batchlog)
            dialog=MultiRankChartWidget(ranking_result,self)
            dialog.show()
        
    
    def export_ai_prompt(self):
        """导出当前组策略下的所有股票基金 Prompt 到剪切板"""
        if "组" in self.index_label.text():
            codes = []
            num_children = self.scroll_layout.count()
            for i in range(num_children):
                item = self.scroll_layout.itemAt(i)
                card = item.widget()
                codes.append(card.filename)
            if not codes:
                return
            if len(codes) > 12:
                QMessageBox.warning(
                    self, 
                    "导出数量超限", 
                    f"当前选择了 {len(codes)} 只股票，最多只能导出 12 只。\n请减少选择后重试。",
                    QMessageBox.Ok
                )
                return
            prompt_instance = stocker_prompt(code=None, codes=codes)
            prompt = prompt_instance.prompt_text_multiple
            pyperclip.copy(prompt)
            QMessageBox.information(self,"导出成功",f"已成功生成 {len(codes)} 只股票的 Prompt，并已复制到剪切板！\n",QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "导出失败", f"只能在组策略下导出 Prompt。",QMessageBox.Ok)

    def export_top_50(self):
        """
        遍历 self.scroll_layout 中的前 50 个组件，提取它们的 'filename' 属性，
        并将这些文件名列表打印出来。ai_prompt 
        """
        file_names = []
        latest_datememory=[]
        prompt=""
        listeddict={}
        count=0
        max_cards = 50
        num_children = self.scroll_layout.count()
        for i in range(num_children):
            item = self.scroll_layout.itemAt(i)
            card = item.widget()
            latest_datememory.append(card.latest_date)
        try:
            for i in range(num_children):
                item = self.scroll_layout.itemAt(i)
                card = item.widget()
                if card and hasattr(card, 'fund_tittle'):
                    if count >= max_cards:
                        break
                    if card.fund_tittle not in listeddict:
                        listeddict[card.fund_tittle] = 1
                        count += 1
                        file_names.append(card.fund_tittle)
                    else:
                        continue  
            if file_names:
                if "过滤低点" in self.index_label.text():
                    print("导出考虑低点的Prompt")
                    prompt = f"你是一个专业的AI助手,这是最近表现下跌的{count}只基金,均为考虑低点后跌破20天均线,且回撤超过7.2%的基金,查看表达了什么信号,结合最近一个月的时事新闻，做市场调研，并给出最终的建议能否买入还是卖出或是等待:{', '.join(file_names)}\n"
                else:
                    prompt = f"你是一个专业的AI助手,这是最近表现优秀的{count}只基金按强弱排名,查看表达了什么信号,结合最近一个月的时事新闻，做市场调研，并给出最终的建议:{', '.join(file_names)}\n"
                pyperclip.copy(prompt)
                QMessageBox.information(self,"导出成功",f"已成功生成 {count}只股票的Prompt,并已复制到剪切板!\n",QMessageBox.Ok)
            else:
                QMessageBox.warning(self, "导出失败", f"未找到文件名。",QMessageBox.Ok)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"错误：{e}",QMessageBox.Ok)
    

    def show_assuming_return(self):
        """卡片显示预期收益"""
        # cards_to_process = list(self.loaded_cards.values())[:200]
        cards_to_process = [
        self.scroll_layout.itemAt(i).widget() 
        for i in range(min(self.scroll_layout.count(), 200))
        if self.scroll_layout.itemAt(i).widget() is not None
        ]
        if not cards_to_process:
            return
        while not check_proxy_alive():  # 注意：调用方法要加 self. 和 ()
            ret = QMessageBox.warning(
                self,
                "网络问题",
                "无法连接到数据源，本功能需要代理环境才能正常运行。\n\n"
                "请开启代理软件后点击“重试”，或点击“取消”放弃本次操作。",
                QMessageBox.Retry | QMessageBox.Cancel,
                QMessageBox.Retry
            )
            if ret == QMessageBox.Cancel:
                return  # 用户取消，直接退出
        def process_batch():
            self.assuming_manager = AssumingManager()
            self.assuming_manager.start_batch(cards_to_process, max_count=200)
            self.assuming_manager.card_finished.connect(self.update_assuming_ui)
        QTimer.singleShot(200, process_batch)

        
    def update_assuming_ui(self,card, result):
        """显示预测收益时通知card更新UI显示预期收益和基金行业"""
        card.update_assuming_return_ui(result)







    def return_market_general_index(self):
        """返回总体市场指数"""
        index_up = index_down = index_normal = 0
        extreme_hot = extreme_cold = 0      # 三天极热/极冷计数
        obvious_hot = obvious_cold = 0      # 三天明显热/明显冷
        total_cards = len(self.loaded_cards)
        decide_todayconclusiondates = []
        today_date=None
        today_up=0
        today_down=0
        month_happened_withdrawal=0
        month_happened_upover10=0
        for card in self.loaded_cards.values():
            rd = card.return_decision()
            
            # 【核心不变】30天年化主逻辑
            year_rate_30d = rd.year_rate_since_start_this(expected_interval_days=30)
            if year_rate_30d > 0.10:
                index_up += 1
            elif year_rate_30d < 0:
                index_down += 1
            else:
                index_normal += 1

            # 【新增】最近三天几何日均收益率
            ret_3d_daily = rd.short_term_return(days=3)
            if ret_3d_daily is not None:
                if ret_3d_daily >= 0.028:       # 顶级亢奋
                    extreme_hot += 1
                elif ret_3d_daily <= -0.025:     # 顶级恐慌
                    extreme_cold += 1
                elif ret_3d_daily >= 0.015:      # 明显升温
                    obvious_hot += 1
                elif ret_3d_daily <= -0.015:     # 明显杀跌
                    obvious_cold += 1
            #计算当日市场盈亏情况
            today_profit_conclusion, date_str = rd.onedayprofitconclusion() 
            one_month_withdrawal_over_10percent = rd.one_month_withdrawal_over_10percent()
            one_month_up_over_10percent = rd.one_month_up_over_10percent()
            decide_todayconclusiondates.append((today_profit_conclusion,date_str,one_month_withdrawal_over_10percent,one_month_up_over_10percent))#添加当日盈亏情况,当天日期。当天是否大于10%回撤
        all_dates = [date_tuple[1] for date_tuple in decide_todayconclusiondates]
        date_counts = Counter(all_dates)
        if not date_counts:
            today_date=None
        else:
            today_date = max(date_counts)
        for date_tuple in decide_todayconclusiondates:
            if date_tuple[1]==today_date:
                if date_tuple[0]=="up":
                    today_up+=1
                elif date_tuple[0]=="down":
                    today_down+=1
            if date_tuple[2]:
                month_happened_withdrawal+=1
            if date_tuple[3]:
                month_happened_upover10+=1
        print(f"{today_date}上涨基金数为：{today_up},今日下跌基金数为：{today_down},今日过去30天大于10%回撤基金数为：{month_happened_withdrawal},今日过去30天大于10%上涨基金数为：{month_happened_upover10}")
        today_up_ratio = today_up / (today_up+today_down) if today_up+today_down > 0 else 0
        today_down_ratio = today_down / (today_up+today_down) if today_up+today_down > 0 else 0
        month_happened_withdrawal_ratio = month_happened_withdrawal / total_cards#月内存在10%回撤的比例
        month_happened_upover10_ratio = month_happened_upover10 / total_cards#月内存在10%上涨的比例
        left_cards_ratio = (total_cards - today_up - today_down)/total_cards if total_cards > 0 else 0
        counted_cards_ratio = 1-left_cards_ratio
        self._show_market_index_dialog(
        index_up, index_down, index_normal,
        extreme_hot, extreme_cold, obvious_hot, obvious_cold,
        total_cards,today_up_ratio,today_down_ratio,left_cards_ratio,counted_cards_ratio,month_happened_withdrawal_ratio,month_happened_upover10_ratio,today_date
    )

    def _show_market_index_dialog(self, index_up, index_down, index_normal,
        extreme_hot, extreme_cold, obvious_hot, obvious_cold, total_cards,today_up_ratio,today_down_ratio,left_cards_ratio,counted_cards_ratio,month_happened_withdrawal_ratio,month_happened_upover10_ratio,today_date):
        dialog = QDialog(self)
        dialog.setWindowTitle("市场行情指数")
        dialog.setFixedSize(790, 690)
        dialog.setFont(QFont('微软雅黑', 11))
        # 1. 原有30天结论（保持原样）
        market_conclusion = generate_market_conclusion(index_up, index_down, index_normal,month_happened_withdrawal_ratio,month_happened_upover10_ratio)
        # 2. 计算30天核心趋势方向（简化判断）
        p_up   = index_up / total_cards
        p_down = index_down / total_cards
        is_bull   = p_up > 0.55 or (p_up > p_down + 0.10)   # 明确偏牛
        is_bear   = p_down > 0.55 or (p_down > p_up + 0.10) # 明确偏熊
        is_shock  = not (is_bull or is_bear)                # 震荡市
        # 3. 3天极端情绪判断
        has_extreme_hot  = extreme_hot >= max(5, total_cards * 0.1)
        has_extreme_cold = extreme_cold >= max(5, total_cards * 0.1)
        has_obvious_hot  = obvious_hot >= total_cards * 0.2
        has_obvious_cold = obvious_cold >= total_cards * 0.2
        # 4. 【核心】多时间框架综合决策逻辑（这就是你缺的灵魂！）
        if has_extreme_hot and (is_bull or not is_bear):
            final_advice = "【牛市顶部预警】30天趋势向上但3天极度亢奋，短期冲顶概率极高！\n→ 立即减仓50~80%，留底仓等调整结束再回补！"
        elif has_extreme_cold and (is_bear or not is_bull):
            final_advice = "【熊市底部确认】30天趋势向下但3天极度恐慌，超级黄金坑已现！\n→ 大胆加仓或开启定投！这是长期最佳买入点！"
        elif has_extreme_hot and is_shock:
            final_advice = "【震荡市冲高回落风险】3天出现极端普涨，属于诱多概率大\n→ 建议高抛低吸，勿追高，重仓者减仓观望"
        elif has_extreme_cold and is_shock:
            final_advice = "【震荡市低吸机会】3天出现极端普跌，恐慌盘集中释放\n→ 可轻仓抄底，等待企稳信号"
        elif is_bull and (has_obvious_hot or extreme_hot > 0):
            final_advice = "【牛市加速段】30天趋势强+3天资金加速流入，最佳持仓阶段！\n→ 满仓甚至可适度加仓强势板块，无需减仓！"
        elif is_bear and (has_obvious_cold or extreme_cold > 0):
            final_advice = "【熊市下跌加速】趋势+情绪共振向下，杀伤力最大\n→ 空仓者继续观望，重仓者必须止损或大幅减仓！"
        elif is_bull:
            final_advice = "【牛市健康运行中】30天趋势向上，3天无极端，趋势未结束\n→ 继续持有强势基金，趋势未完不要下车"
        elif is_bear:
            final_advice = "【熊市调整中】30天趋势向下，但3天无极端杀跌\n→ 降低仓位，优先配置防御板块，耐心等底部信号"
        else:
            final_advice = "【震荡市】30天多空平衡，3天无明显极端\n→ 保持定投 + 轻仓波段，不追涨杀跌"

        # 5. 3天情绪简要提示（辅助信息）
        parts = []
        if extreme_hot > 0 and total_cards > 0:
            parts.append(f"极端亢奋比率{extreme_hot/total_cards:.2%}")
        if extreme_cold > 0 and total_cards > 0:
            parts.append(f"极端恐慌比率{extreme_cold/total_cards:.2%}")
        if obvious_hot > 0 and total_cards > 0:
            parts.append(f"明显加速比率{obvious_hot/total_cards:.2%}")
        if obvious_cold > 0 and total_cards > 0:
            parts.append(f"明显杀跌比率{obvious_cold/total_cards:.2%}")
        short_signal = "; ".join(parts) if parts else "暂无情绪数据"

        overallwords=""
        if today_up_ratio>0:
            overallwords+=f"&nbsp;&nbsp;上涨占{today_up_ratio:.1%}  "
        if today_down_ratio>0:
            overallwords+=f"&nbsp;&nbsp;下跌占{today_down_ratio:.1%}<br>"
        if month_happened_withdrawal_ratio>0:
            overallwords+=f"&nbsp;&nbsp;今日过去30天回撤大于百分之十占{month_happened_withdrawal_ratio:.1%}  "
        if month_happened_upover10_ratio>0:
            overallwords+=f"&nbsp;&nbsp;今日过去30天增长大于百分之十占{month_happened_upover10_ratio:.1%}" 


        # 6. 最终UI展示（层次清晰，一眼看懂）
        html = f"""
        <b>30天年化趋势：</b> 走强<b>{index_up}</b> 　 走弱<b>{index_down}</b> 　 表现平平<b>{index_normal}</b> （共{total_cards}只）<br><br>
        {market_conclusion.replace('【', '<br><b>【').replace('】', '】</b>')}<br><br>
        
        <b>3日极端情绪：</b> {short_signal}<br><br>
        <b>{today_date}当日市场整体:</b><br>{overallwords}<br>剩下{left_cards_ratio:.1%}未即时更新。<br><br>
        <h3 align="center"><font >【最终综合结论】</font></h3>
        <font  size="5"><b>{final_advice.split('】')[1] if '】' in final_advice else final_advice}</b></font>
        """

        

        label = QLabel(html)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setContentsMargins(25, 25, 25, 25)
        label.setFont(QFont('微软雅黑', 11))

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addStretch()
        dialog.setLayout(layout)
        dialog.exec_()





class containerwidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)



def is_daytime():
    from datetime import datetime
    now = datetime.now().time()
    start = now.replace(hour=6, minute=0, second=0, microsecond=0)
    end = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if start <= now < end:
        return True
    return False


def check_proxy_alive(host="127.0.0.1"):
    """极速探测代理端口是否开放"""
    proxy_port = get_proxy_config()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)  # 只给 0.5 秒探测时间，不阻塞主线程
    try:
        s.connect((host, proxy_port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, Exception):
        return False


if __name__ == "__main__":
    pass
QLabel
