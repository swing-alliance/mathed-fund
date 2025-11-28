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
from PyQt5.QtCore import QTimer
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
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索项目...")
        self.search_input.setClearButtonEnabled(True) # 添加清除按钮
        self.search_input.setMaximumWidth(300)
        self.search_input.setFont(QFont('微软雅黑', 12))
        #QTimer 用于延时过滤
        self.filter_timer = QTimer(self)
        self.filter_timer.setSingleShot(True)  
        self.filter_timer.setInterval(20)      
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




    def start_filter_timer(self):
        """当文本改变时调用，它会重置并启动定时器。"""
        if self.filter_timer.isActive():
            self.filter_timer.stop()
        self.filter_timer.start()


    def _perform_filtering(self):
        """
        增量式过滤：只对需要改变状态（从布局中移除或添加）的卡片进行操作。
        """
        search_text = self.search_input.text().lower().strip()
        
        # 禁用更新
        self.setUpdatesEnabled(False) 
        
        # 跟踪当前布局中的组件，用于快速判断
        # 假设 self.scroll_layout 是您的布局
        current_widgets_in_layout = {self.scroll_layout.itemAt(i).widget() 
                                    for i in range(self.scroll_layout.count()) 
                                    if self.scroll_layout.itemAt(i).widget() is not None}
        
        # 准备一个列表，存放本次应该显示的卡片，以便按正确的顺序重新添加
        cards_to_show_in_order = []

        # 1. 遍历所有卡片，决定其状态
        for card in self.loaded_cards.values():
            
            # 使用预处理数据 (推荐)
            filename = card.search_data['filename'] 
            fund_title = card.search_data['fund_title']
            
            is_match = (search_text == "") or (search_text in filename or search_text in fund_title)

            if is_match:
                cards_to_show_in_order.append(card)
            else:
                # A. 如果不匹配，且卡片当前在布局中，则移除
                if card in current_widgets_in_layout:
                    self.scroll_layout.removeWidget(card)
                    card.setParent(None) # 断开父子关系
                    card.hide()
                # B. 如果不匹配且不在布局中，无需操作
                else:
                    card.hide()
                    
        # 2. 清空并重新添加（这是为了保证顺序正确）
        # 在这个结构下，为了确保卡片始终按照 self.loaded_cards 的顺序显示，
        # 我们仍然需要清空整个布局，只添加匹配项。
        # 否则，如果使用增量添加，卡片会在列表的末尾出现。

        # 我们回到使用 clear_layout，但目标是确保清空/添加操作的性能已经通过 Debouncing 优化到最低频率。
        
        # --- 重新使用 clear_layout，并优化清空逻辑 ---
        
        # 重新清空布局（现在我们知道清空是必须的，以保证顺序）
        # 但我们优化 clear_layout，只移除可见的/在布局中的组件
        
        self.clear_layout_widgets_only(self.scroll_layout) 

        # 3. 重新添加所有匹配的卡片（按加载顺序）
        for card in cards_to_show_in_order:
            self.scroll_layout.addWidget(card)
            card.show()

        # 启用更新
        self.setUpdatesEnabled(True)

            
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
        
    def clear_layout_widgets_only(self, layout):
        """
        辅助函数：从给定的布局中移除所有组件。
        只移除 QWidget，不处理子布局，以确保卡片对象仍存在。
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                
                if widget is not None:
                    # 从布局中移除并断开父子关系
                    widget.setParent(None)


            


    def return_market_general_index(self):
        """返回总体市场指数"""
        index_up = index_down = index_normal = 0
        extreme_hot = extreme_cold = 0      # 三天极热/极冷计数
        obvious_hot = obvious_cold = 0      # 三天明显热/明显冷
        total_cards = len(self.loaded_cards)
        decide_todayconclusiondates = []
        today_up=0
        today_down=0
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
                if ret_3d_daily >= 0.028:       # 顶级亢奋（历史不到20次）
                    extreme_hot += 1
                elif ret_3d_daily <= -0.025:     # 顶级恐慌
                    extreme_cold += 1
                elif ret_3d_daily >= 0.015:      # 明显加速
                    obvious_hot += 1
                elif ret_3d_daily <= -0.015:     # 明显杀跌
                    obvious_cold += 1

            #计算当日市场盈亏情况
            today_profit_conclusion, date_str = rd.onedayprofitconclusion() 
            decide_todayconclusiondates.append(date_str)
            if today_profit_conclusion == "up":
                today_up += 1
            else:
                today_down += 1
        altimate_today_date_conunt={}        
        for everydate in decide_todayconclusiondates:
            if everydate not in altimate_today_date_conunt:
                altimate_today_date_conunt[everydate]=1
            altimate_today_date_conunt[everydate] +=1
        most_today_date=max(altimate_today_date_conunt,key=altimate_today_date_conunt.get)

        today_up_ratio = today_up / total_cards if total_cards > 0 else 0
        today_down_ratio = today_down / total_cards if total_cards > 0 else 0
        self._show_market_index_dialog(
        index_up, index_down, index_normal,
        extreme_hot, extreme_cold, obvious_hot, obvious_cold,
        total_cards,today_up_ratio,today_down_ratio,most_today_date
    )


    def _show_market_index_dialog(self, index_up, index_down, index_normal,
        extreme_hot, extreme_cold, obvious_hot, obvious_cold, total_cards,today_up_ratio,today_down_ratio,most_today_date):
        dialog = QDialog(self)
        dialog.setWindowTitle("市场行情指数")
        dialog.setFixedSize(780, 680)
        dialog.setFont(QFont('微软雅黑', 11))

        # 1. 原有30天结论（保持原样）
        market_conclusion = generate_market_conclusion(index_up, index_down, index_normal)

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
        if has_extreme_hot:
            short_signal = f"极度亢奋！{extreme_hot}只基金3日日均≥4.5%"
        elif has_extreme_cold:
            short_signal = f"极度恐慌！{extreme_cold}只基金3日日均≤-4.5%"
        elif has_obvious_hot:
            short_signal = f"明显加速（{obvious_hot}只≥3%）"
        elif has_obvious_cold:
            short_signal = f"明显降温（{obvious_cold}只≤-3%）"
        else:
            short_signal = "情绪平稳"


        # 6. 最终UI展示（层次清晰，一眼看懂）
        html = f"""
        <b>30天年化趋势：</b> 走强<b>{index_up}</b> 　 走弱<b>{index_down}</b> 　 表现平平<b>{index_normal}</b> （共{total_cards}只）<br><br>
        {market_conclusion.replace('【', '<br><b>【').replace('】', '】</b>')}<br><br>
        
        <b>3日极端情绪：</b> {short_signal}<br><br>
        <b>{most_today_date}当日市场整体：</b>上涨占比{today_up_ratio:.0%}，下跌占比{today_down_ratio:.0%}<br><br>
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

