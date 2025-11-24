import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea,QLineEdit, QComboBox,QDialog,QApplication,QMenu,QAction,QProgressDialog
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
import pandas as pd
import shutil
from projectcard import ProjectCard
TO_WORKER = "to_worker"
FOUND_PATH = "found"

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
        self.loaded_cards = {}#用于缓存已加载的卡片
        self.base_path = base_path 
        self.file_nums = len(os.listdir(base_path))
        main_layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setFont(QFont('微软雅黑', 20))
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_project_from_found)
        self.index_label=self.what_label_now()
        top_bar.addWidget(self.add_btn, alignment=Qt.AlignLeft)
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
        self.scroll_area.setWidget(self.scroll_content)

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
                df=pd.read_csv(csv_path)
                this_group_name=os.path.basename(this_group_path)
                selected_paths_series = df.loc[df['group_name'] == this_group_name, 'path']
                selected_paths = selected_paths_series.tolist()
                if not selected_paths:
                    print(f"分组 {this_group_name} 中没有项目！")
                    return
                self.file_nums = len(selected_paths)
                progress_dialog = QProgressDialog("正在加载文件...", "取消", 0, len(selected_paths), self)
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
            df=pd.read_csv(os.path.join(groups_path, 'group_cache.csv'))
            group_name=os.path.basename(self.base_path)
            matching_row = df[df['group_name'] == group_name]
            self.group_file_nums = len(matching_row)
            qlabel.setText(f"当前组策略:{os.path.basename(self.base_path)}   {self.group_file_nums}个记录")
            self.add_btn.hide()
        return qlabel



    def resort_self(self):
        """重新排序项目卡片按照夏普比率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().sharp_constant, reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)
    def resort_self_by_largest_yearly_return(self):
        """重新排序项目卡片按照开始年化收益率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(), reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)

    def resort_self_by_80days_yearly_return(self):
        """重新排序项目卡片按照80天年化收益率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=80), reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)

    def resort_self_by_30days_yearly_return(self):
        """重新排序项目卡片按照30天年化收益率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=30), reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)
    
    def resort_self_by_14days_yearly_return(self):
        """重新排序项目卡片按照14天年化收益率从大到小"""
        print("重新排序项目卡片按照14天年化收益率从大到小被调用")
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=14), reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)

    def resort_self_by_3days_yearly_return(self):
        """重新排序项目卡片按照3天年化收益率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().year_rate_since_start_this(expected_interval_days=3), reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)


    def resort_self_by_largest_votolity(self):
        """重新排序项目卡片按照波动率从大到小"""
        sorted_cards = sorted(self.loaded_cards.values(), key=lambda card: card.return_decision().max_annualized_volatility, reverse=True)
        for card in self.loaded_cards.values():
            self.scroll_layout.removeWidget(card)
        for card in sorted_cards:
            self.scroll_layout.addWidget(card)

    def filter_self_by_consider_lowpoint(self):
        """
        过滤项目卡片只显示考虑低点的 (通过控制可见性实现，无重叠Bug)
        """
        
        # 遍历所有卡片，根据条件显示或隐藏
        for card in self.loaded_cards.values():
            
            # 1. 判断是否符合过滤条件 (注意：这里必须调用方法，加上括号 ())
            is_lowpoint = card.return_decision().is_consider_lowpoint()
            
            if is_lowpoint is True:
                # 2. 符合条件：显示卡片
                card.show()
            else:
                # 3. 不符合条件：隐藏卡片 (解决重叠Bug的关键)
                card.hide()
                
        # 4. 通知布局系统重新计算大小，以回收被隐藏控件占用的空间
        # 这一步是让QScrollArea/QLayout适应新高度的关键
        if self.scroll_layout:
            self.scroll_layout.update()
            # 尝试更新父级视图以确保刷新，特别是滚动区域
            scroll_area = self.scroll_layout.parentWidget().parentWidget()
            if hasattr(scroll_area, 'viewport'):
                scroll_area.viewport().update()
        



            


    def return_market_general_index(self):
        """返回目前市场大体行情指数，用于决策参考"""
        index_up = 0
        index_down = 0
        index_normal = 0
        for card in self.loaded_cards.values():
            return_rate = card.return_decision().year_rate_since_start_this(expected_interval_days=30)
            if return_rate > 0.10:
                index_up += 1
            elif return_rate < 0:
                index_down += 1
            else:
                index_normal += 1
        self._show_market_index_dialog(index_up, index_down, index_normal)


    def _show_market_index_dialog(self, index_up, index_down, index_normal):
        """
        内部方法：根据传入的指数数据创建并显示 QDialog 弹窗。
        - 改进：加入微软雅黑字体，加粗关键数字，显示市场结论。
        """
        total = index_up + index_down + index_normal
        
        # --- 1. 创建对话框并设置基本属性 ---
        dialog = QDialog(self) 
        
        # 尝试设置字体（注意：为确保所有控件生效，也可以单独设置）
        font = QFont('微软雅黑', 10)
        # 不直接对 dialog.setFont，因为 QLabel 的 RichText 格式化效果更好
        dialog.setWindowTitle("市场行情指数")
        dialog.setFixedSize(600, 400) # 扩大尺寸以容纳结论
        market_conclusion = generate_market_conclusion(index_up, index_down, index_normal)
        data_text = (f"过去一个月 <b>{total}</b> 条数据中：<br>"
                    f"<b>{index_up}</b> 个走强，<b>{index_down}</b> 个走弱，<b>{index_normal}</b> 个表现平平。")
        conclusion_text = f"市场总结： {market_conclusion}"
        data_label = QLabel(data_text)
        data_label.setTextFormat(Qt.RichText)
        data_label.setAlignment(Qt.AlignCenter)
        data_label.setFont(QFont('微软雅黑', 12)) # 独立设置字体和大小
        
        # B. 结论 Label (左对齐，用于显示更长的分析文本)
        conclusion_label = QLabel(conclusion_text)
        conclusion_label.setWordWrap(True) # 允许自动换行
        conclusion_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        conclusion_label.setFont(font)
        layout = QVBoxLayout()
        layout.addWidget(data_label)
        layout.addSpacing(15) 
        layout.addWidget(conclusion_label)
        layout.addStretch(1) 
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

def generate_market_conclusion(index_up: int, index_down: int, index_normal: int) -> str:
    total_data = index_up + index_down + index_normal
    if total_data == 0:
        return "暂无数据，当前无法判断市场行情。"
    
    p_up = index_up / total_data
    p_down = index_down / total_data
    STRENGTH_ADVANTAGE_THRESHOLD = 0.10
    HIGH_DIVERGENCE_THRESHOLD = 0.85
    ABSOLUTE_BULLISH_THRESHOLD = 0.60
    
    is_highly_divergent = (p_up + p_down) > HIGH_DIVERGENCE_THRESHOLD
    if is_highly_divergent:
        conclusion_divergence = "市场处于高度分化状态，中间地带资产稀少。"
    else:
        conclusion_divergence = "市场结构较为温和。"

    if p_up > ABSOLUTE_BULLISH_THRESHOLD:
        return ("【绝对牛市阶段】\n"
                "超过60%的股票型基金近一个月年化收益率超10%，市场处于全面进攻期，情绪极度乐观。\n"
                "推荐板块：科技（半导体、AI、互联网）、新能源车、军工、周期向上（有色、煤炭、化工）。\n"
                "规避板块：医药、消费、红利高股息（此阶段大概率落后）。\n"
                "操作建议：继续满仓持有强势赛道基金，允许适度追高，但不要杠杆，警惕顶部剧烈震荡。")

    elif p_down > ABSOLUTE_BULLISH_THRESHOLD:
        return ("【绝对熊市阶段】\n"
                "超过60%的股票型基金近一个月出现下跌，市场进入较深调整，恐慌情绪占主导。\n"
                "推荐板块：医药、消费（食品饮料、白酒）、红利高股息、公用事业、黄金。\n"
                "规避板块：科技、成长、周期（有色、化工、新能源）、小盘股。\n"
                "操作建议：这是长期投资者最佳的低位布局窗口，建议开启或加大定投宽基指数（如沪深300、中证500）和优质行业基金，跌得越狠越值得买入。")

    elif p_up > p_down and (p_up - p_down) > STRENGTH_ADVANTAGE_THRESHOLD:
        return (f"【结构性牛市，偏强势】\n"
                f"上涨基金占比 {p_up:.0%}，领先下跌基金约 {p_up-p_down:.0%}，市场仍有上行动力。\n"
                f"{conclusion_divergence}\n"
                "推荐板块：科技、半导体、新能源、军工、出口链、资源品（石油化工、有色）。\n"
                "次优选择：消费（家电、旅游）、高端制造。\n"
                "暂时规避：纯防御类医药、红利高股息（抗跌但涨幅有限）。\n"
                "操作建议：继续持有并可适度加仓强势赛道基金，趋势未结束前不要轻易下车。")

    elif p_down > p_up and (p_down - p_up) > STRENGTH_ADVANTAGE_THRESHOLD:
        return (f"【结构性熊市，偏弱势】\n"
                f"下跌基金占比 {p_down:.0%}，领先上涨基金约 {p_down-p_up:.0%}，市场短期承压。\n"
                f"{conclusion_divergence}\n"
                "推荐板块：医药（创新药、医疗器械）、必选消费（食品饮料、白酒）、红利高股息、银行、保险、公用事业、黄金。\n"
                "规避板块：科技（半导体、AI、计算机）、新能源车、周期品、小盘成长。\n"
                "操作建议：降低总体股票仓位，优先配置防御类行业基金，耐心等待企稳信号。少数抗跌的科技龙头也可继续持有但不加仓。")

    else:
        return ("【震荡市，多空平衡】\n"
                "上涨与下跌基金数量接近，市场缺乏明确趋势，处于来回拉锯状态。\n"
                f"{conclusion_divergence}\n"
                "推荐策略：\n"
                "• 短线投资者：可关注热点轮动（如AI→医药→消费→红利），小仓位波段操作\n"
                "• 长线投资者：保持定投，不追涨杀跌，等待下一轮趋势明确\n"
                "• 防御型投资者：可超配红利高股息+黄金+债券混合基金\n"
                "当前不宜重仓单一方向，分散与耐心是最优策略。")

    # def load_projects_from_path(self, path):
    #         def load_files_from_path(directory_path):
    #             """加载指定路径下的文件（无进度框）"""
                
    #             # 路径检查（添加更稳健的检查）
    #             if not os.path.isdir(directory_path):
    #                 print(f"路径 {directory_path} 不存在或不是目录！")
    #                 return

    #             project_files = os.listdir(directory_path)
    #             self.file_nums = len(project_files)
                
    #             if not project_files:
    #                 print(f"路径 {directory_path} 中没有文件！")
    #                 return
    #             for index, file_name in enumerate(project_files):
    #                 if file_name not in self.loaded_cards:
    #                     file_path = os.path.join(directory_path, file_name)
    #                     try:
    #                         card = ProjectCard(file_path)
    #                         card.visualize_requested.connect(self.visualize_requested.emit)
    #                         self.scroll_layout.addWidget(card)
    #                         self.loaded_cards[file_name] = card
    #                     except Exception as e:
    #                         print(f"创建 ProjectCard 失败 ({file_name}): {e}")
    #                         continue
    #         if path == balanced_path:
    #             load_files_from_path(balanced_path)
    #         elif path == Equity_path:
    #             load_files_from_path(Equity_path)
    #         elif path == index_path:
    #             load_files_from_path(index_path)
    #         elif path == Qdii_path:
    #             load_files_from_path(Qdii_path)


    def refresh_self(self):
        print("试图刷新自己")
        self.load_projects_from_path(self.base_path)



if __name__ == "__main__":
    pass

