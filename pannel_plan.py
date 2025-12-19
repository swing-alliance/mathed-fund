import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication,QMenu,QAction,QProgressDialog
)
import pyperclip
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont ,QIcon
import pandas as pd
from projectcard import ProjectCard
from PyQt5.QtCore import QTimer
from fundholding import stocker_prompt
from collections import Counter
import glob
TO_WORKER = "to_worker"
FOUND_PATH = "found"
target_dir = os.path.join(os.getcwd(), 'static')
pics = glob.glob(os.path.join(target_dir, '*.png'))
pic = next((p for p in pics if 'infinite.png' in p), None)
if pic is None and pics:
    pic = pics[0]
balanced_path = os.path.join(os.getcwd(), 'my_types','Balanced')
Equity_path = os.path.join(os.getcwd(), 'my_types','Equity')
index_path = os.path.join(os.getcwd(), 'my_types','Index')
Qdii_path = os.path.join(os.getcwd(), 'my_types','Qdii')
groups_path = os.path.join(os.getcwd(), 'groups')


class ControlPanel(QWidget):
    """控制面板（QWidget），带滚动区域"""
    visualize_requested = pyqtSignal(str)
    def __init__(self, parent=None,base_path=None):
        super().__init__(parent)
        self.hidden_storage = QWidget()
        self.card_to_show=[]
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
                csv_path = os.path.join(groups_path, 'group_cache.csv')
                df=pd.read_csv(csv_path,dtype=str)
                this_group_name=os.path.basename(this_group_path)
                selected_paths_series = df.loc[df['group_name'] == str(this_group_name), 'path']
                selected_paths = selected_paths_series.tolist()
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
            if path == balanced_path:
                load_files_from_path(balanced_path)
            elif path == Equity_path:
                load_files_from_path(Equity_path)
            elif path == index_path:
                load_files_from_path(index_path)
            elif path == Qdii_path:
                load_files_from_path(Qdii_path)
            else:
                load_projects_from_groups(this_group_path=self.base_path)




    def start_filter_timer(self):
        """当文本改变时调用，它会重置并启动定时器。"""
        if self.filter_timer.isActive():
            self.filter_timer.stop()
        self.filter_timer.start()


    def _perform_filtering(self):
        """实际的过滤逻辑。"""
        search_text = self.search_input.text().lower().strip()
        visible_cards = [
            card for card in self.loaded_cards.values()
            if not search_text or search_text in card.fund_tittle or search_text in card.filename
        ]
        self.setUpdatesEnabled(False)
        try:
            for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
                card.hide()
            for card in visible_cards:#写两个for比一个for快十倍
                if "过滤低点" in self.index_label.text():
                    if card.filename in self.card_to_show:
                        card.show()
                    else:
                        continue
                else:
                    card.show()
            for card in visible_cards:
                self.scroll_layout.addWidget(card)
        finally:
            card_count = 0
            for i in range(self.scroll_layout.count()):
                widget = self.scroll_layout.itemAt(i).widget()
                if isinstance(widget, ProjectCard):
                    card_count += 1
            print(f"当前布局中有 {card_count} 个卡片")
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
            df=pd.read_csv(os.path.join(groups_path, 'group_cache.csv'),dtype=str)
            group_name=os.path.basename(self.base_path)
            matching_row = df[df['group_name'] == group_name]
            self.group_file_nums = len(matching_row)
            qlabel.setText(f"当前组策略:{os.path.basename(self.base_path)}   {self.group_file_nums}个记录")
            self.add_btn.hide()
        return qlabel



    def resort_self(self):
        """重新排序项目卡片按照365天夏普比率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().sharp_constant, reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组365天夏普比排序")
        else:
            self.index_label.setText(f"当前365天夏普比排序")

    def resort_self_by_largest_sharpe_60days(self):
        """重新排序项目卡片按照60天夏普比率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().max_sharp_ratio_for_days(period_days=60), reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组60天夏普比排序")
        else:
            self.index_label.setText(f"当前计划60天夏普比排序")    
        

    def resort_self_by_80days_yearly_return(self):
        """重新排序项目卡片按照80天年化收益率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=80), reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组80天年化收益率排序")
        else:
            self.index_label.setText(f"当前计划80天年化收益率排序")

    def resort_self_by_30days_yearly_return(self):
        """重新排序项目卡片按照30天年化收益率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), 
                                   key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=30), 
                                   reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组30天年化收益率排序")
        else:
            self.index_label.setText(f"当前计划30天年化收益率排序")

    def resort_self_by_14days_yearly_return(self):
        """重新排序项目卡片按照14天年化收益率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=14), reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组14天年化收益率排序")
        else:
            self.index_label.setText(f"当前计划14天年化收益率排序")

    def resort_self_by_3days_yearly_return(self):
        """重新排序项目卡片按照3天年化收益率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=3), reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组3天年化收益率排序")
        else:
            self.index_label.setText(f"当前计划3天年化收益率排序")

    def resort_self_by_largest_votolity(self):
        """重新排序项目卡片按照波动率从大到小"""
        sorted_cards_list = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().max_annualized_volatility, reverse=True)
        new_ordered_cards = {card.filename: card for card in sorted_cards_list} # 假设卡片有 card_id 属性作为键
        self.loaded_cards = new_ordered_cards
        for card in list(self.loaded_cards.values()): # 使用 list() 复制值，确保移除时不会干扰迭代
            self.scroll_layout.removeWidget(card)
        for card in self.loaded_cards.values():
            self.scroll_layout.addWidget(card)
        if "组" in self.index_label.text():
            self.index_label.setText(f"当前组做波动率排序")
        else:    
            self.index_label.setText(f"当前计划做波动率排序")

    def filter_self_by_consider_lowpoint(self):
        """过滤项目卡片只显示考虑低点的 (通过控制可见性实现，无重叠Bug)"""
        filtered_cards = [card for card in self.loaded_cards.values() if card.return_decision().is_consider_lowpoint() is True]
        for card in self.loaded_cards.values():
                self.scroll_layout.removeWidget(card)
                card.hide()
        for card in filtered_cards:
            self.card_to_show.append(card.filename)
            card.show()
        for card in filtered_cards:
            self.scroll_layout.addWidget(card)
        self.scroll_layout.invalidate() 
        status_type = "组" if "组" in self.index_label.text() else "计划"
        self.index_label.setText(f"当前{status_type}过滤低点 ({len(filtered_cards)})")
        
    
    def export_ai_prompt(self):
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
        并将这些文件名列表打印出来。
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
        month_happened_withdrawal_ratio = month_happened_withdrawal / (today_up+today_down) if today_up+today_down > 0 else 0#月内存在10%回撤的比例
        month_happened_upover10_ratio = month_happened_upover10 / (today_up+today_down) if today_up+today_down > 0 else 0#月内存在10%上涨的比例
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

def generate_market_conclusion(index_up: int, index_down: int, index_normal: int, month_happened_withdrawal_ratio: float, month_happened_upover10_ratio: float) -> str:
    """
    index_up: 近30天年化收益率超过10%的基金数量,index_down: 近30天年化收益率小于0的基金数量,index_normal: 近30天年化收益率在0%到10%之间的基金数量,
    month_happened_withdrawal_ratio:过去30天存在10%回撤比例的基金占比,month_happened_upover10_ratio:过去30天存在10%上涨比例的基金占比
    """
    if any(arg < 0 for arg in [index_up, index_down, index_normal, month_happened_withdrawal_ratio, month_happened_upover10_ratio]):
        return "参数错误：所有输入值必须为非负数。"
    
    if month_happened_withdrawal_ratio > 1 or month_happened_upover10_ratio > 1:
        return "参数错误：回撤和上涨比例必须在0-1之间。"
    
    # 计算总量和比例
    total_funds = index_up + index_down + index_normal
    if total_funds == 0:
        return "暂无有效数据，当前无法判断市场行情。"
    
    p_up = index_up / total_funds
    p_down = index_down / total_funds
    p_normal = index_normal / total_funds
    
    # 阈值定义
    STRENGTH_ADVANTAGE_THRESHOLD = 0.10
    HIGH_DIVERGENCE_THRESHOLD = 0.85
    ABSOLUTE_BULLISH_THRESHOLD = 0.60
    EXTREME_MOVEMENT_THRESHOLD = 0.50  # 新增：极端波动阈值
    
    # 判断市场分化程度
    extreme_movement_ratio = month_happened_withdrawal_ratio + month_happened_upover10_ratio
    is_highly_divergent = (p_up + p_down) > HIGH_DIVERGENCE_THRESHOLD
    has_extreme_volatility = extreme_movement_ratio > EXTREME_MOVEMENT_THRESHOLD
    
    # 构建分化程度描述
    if is_highly_divergent:
        divergence_note = "市场处于高度分化状态，中间地带资产稀少。"
    else:
        divergence_note = "市场结构较为温和，多数资产处于中间状态。"
    
    # 添加波动性描述
    volatility_note = ""
    if has_extreme_volatility:
        if month_happened_withdrawal_ratio > 0.3 and month_happened_upover10_ratio > 0.3:
            volatility_note = "市场同时存在大量暴涨暴跌基金，波动极为剧烈。"
        elif month_happened_upover10_ratio > 0.4:
            volatility_note = "市场存在显著赚钱效应，但需注意波动风险。"
        elif month_happened_withdrawal_ratio > 0.4:
            volatility_note = "市场回撤压力较大，投资者情绪偏向谨慎。"
    
    # 主要判断逻辑
    if p_up > ABSOLUTE_BULLISH_THRESHOLD:
        return f"""【绝对牛市阶段】
                市场表现：超过60%的股票型基金近一个月年化收益率超10%，市场处于全面进攻期，情绪极度乐观。
                {divergence_note}{volatility_note}

                推荐关注板块：
                • 进攻型：科技（半导体、AI、互联网）、新能源车、军工
                • 周期向上：有色、煤炭、化工等景气周期板块

                规避板块：
                • 防御型：医药、消费、红利高股息（此阶段大概率落后大盘）

                操作建议：
                1. 继续满仓持有强势赛道基金，顺势而为
                2. 允许适度追高，但避免使用杠杆
                3. 警惕顶部剧烈震荡，设定止盈止损位
                4. 关注成交量和政策面变化，防范系统性风险"""

    elif p_down > ABSOLUTE_BULLISH_THRESHOLD:
        return f"""【绝对熊市阶段】

            市场表现：超过60%的股票型基金近一个月出现下跌，市场进入较深调整，恐慌情绪占主导。
            {divergence_note}{volatility_note}

            推荐关注板块：
            • 防御型：医药、必选消费（食品饮料、白酒）
            • 稳健型：红利高股息、公用事业、黄金
            • 价值型：银行、保险等低估值板块

            规避板块：
            • 高波动：科技、成长股、小盘股
            • 强周期：有色、化工、新能源等顺周期品种

            操作建议：
            1. 这是长期投资者最佳的低位布局窗口
            2. 建议开启或加大定投宽基指数（沪深300、中证500）
            3. 分批买入优质行业基金，跌得越深越值得关注
            4. 保持足够现金仓位，等待明确企稳信号"""

    elif p_up > p_down and (p_up - p_down) > STRENGTH_ADVANTAGE_THRESHOLD:
        return f"""【结构性牛市，偏强势】

                市场表现：上涨基金占比 {p_up:.0%}，领先下跌基金约 {p_up-p_down:.0%}，市场仍有上行动力。
                {divergence_note}{volatility_note}

                推荐关注板块：
                • 主线板块：科技、半导体、新能源、军工
                • 弹性品种：出口链、资源品（石油化工、有色）
                • 次优选择：消费（家电、旅游）、高端制造

                暂时规避：
                • 纯防御类：医药、红利高股息（抗跌但涨幅可能有限）

                操作建议：
                1. 继续持有并可适度加仓强势赛道基金
                2. 趋势未结束前不要轻易下车，但需控制仓位
                3. 关注板块轮动机会，避免过度追高
                4. 保留部分现金应对可能的调整"""

    elif p_down > p_up and (p_down - p_up) > STRENGTH_ADVANTAGE_THRESHOLD:
        return f"""【结构性熊市，偏弱势】

            市场表现：下跌基金占比 {p_down:.0%}，领先上涨基金约 {p_down-p_up:.0%}，市场短期承压。
            {divergence_note}{volatility_note}

            推荐关注板块：
            • 防御核心：医药（创新药、医疗器械）、必选消费
            • 稳健配置：红利高股息、银行、保险、公用事业
            • 避险资产：黄金及相关基金

            规避板块：
            • 高估值：科技（半导体、AI、计算机）
            • 强周期：新能源车、周期品、小盘成长

            操作建议：
            1. 降低总体股票仓位，控制风险暴露
            2. 优先配置防御类行业基金
            3. 耐心等待企稳信号，不急于抄底
            4. 少数抗跌的科技龙头可持有但不加仓"""

    else:
        return f"""【震荡市，多空平衡】

                市场表现：上涨与下跌基金数量接近，市场缺乏明确趋势，处于来回拉锯状态。
                {divergence_note}{volatility_note}

                短线投资者：
                • 关注热点轮动（AI→医药→消费→红利）
                • 小仓位波段操作，快进快出
                • 严格止损，控制单笔亏损

                长线投资者：
                • 保持定投节奏，不追涨杀跌
                • 优化持仓结构，汰弱留强
                • 等待下一轮趋势明确信号

                防御型投资者：
                • 超配红利高股息+黄金+债券混合基金
                • 注重资产配置的平衡性
                • 以稳健收益为主要目标

                总体建议：当前不宜重仓单一方向，分散配置与耐心持有是最优策略。关注政策面变化和资金流向，灵活调整战术。"""



class containerwidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

if __name__ == "__main__":
    pass
QLabel
