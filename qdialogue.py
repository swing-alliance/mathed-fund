from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QLineEdit, QLabel, QMessageBox, QPushButton, 
                             QHBoxLayout, QSpinBox,QApplication, QDoubleSpinBox, QCheckBox, QComboBox,QHeaderView,QTableWidget,QTableWidgetItem
                             ,QScrollArea,QGroupBox,QFormLayout,QListWidget,QListWidgetItem,QDesktopWidget)
from PyQt5.QtCore import Qt
import re
import sys
import pandas as pd
import akshare as ak
from PyQt5.QtGui import QFont 
import os
import shutil


class pulldata_dialog(QDialog):
    """拉取数据时弹出的参数控制的对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入基金代码")
        self.resize(300, 150)
        self.codes = []  # 保存最终返回的数组
        layout = QVBoxLayout()
        # 输入提示
        layout.addWidget(QLabel("请输入代码，用空格或逗号分隔："))
        # 输入框
        self.input_edit = QLineEdit()
        layout.addWidget(self.input_edit)
        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.reject)

    def on_ok(self):
        text = self.input_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "错误", "请输入至少一个基金代码")
            return
        codes = re.findall(r'\b\d{6}\b', text)
        if not codes:
            QMessageBox.warning(self, "错误", "请输入有效的六位数字")
            return
        self.codes = codes
        self.accept()

#找基金序号范围，期望找到基金的数量
# 基金本身的年年化收益率(过去一年的净值增长率),夏普比率，年化波动率，最大回撤率，最大回撤天数
class advance_pulldata_dialog(QDialog):
    """高级拉取数据时弹出的参数控制的对话框"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("基金筛选参数配置")
        self.setGeometry(100, 100, 450, 480) # 调整窗口高度以容纳新控件
        self.set_font()
        self.create_widgets()
    def set_font(self):
        """设置窗口的字体为微软雅黑"""
        font = QFont("微软雅黑", 10)
        self.setFont(font)
    def create_widgets(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        # 顶部标题
        self.title_label = QLabel("基金筛选参数配置")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        # --- 基金基础信息分组 ---
        basic_info_group = QGroupBox("基础设置")
        basic_info_layout = QFormLayout()
        
        self.start_label = QLabel("基金代码范围：")
        self.start_input = QLineEdit("000001")
        self.start_input.setPlaceholderText("起始代码")
        
        self.end_label = QLabel("至")
        self.end_input = QLineEdit("999999")
        self.end_input.setPlaceholderText("结束代码")
        
        code_range_layout = QHBoxLayout()
        code_range_layout.addWidget(self.start_input)
        code_range_layout.addWidget(self.end_label)
        code_range_layout.addWidget(self.end_input)
        basic_info_layout.addRow(self.start_label, code_range_layout)
        
        self.fund_count_label = QLabel("期望数量：")
        self.fund_count_input = QSpinBox()
        self.fund_count_input.setRange(1, 10000)
        self.fund_count_input.setValue(100)
        basic_info_layout.addRow(self.fund_count_label, self.fund_count_input)
        
        basic_info_group.setLayout(basic_info_layout)

        # --- 筛选指标分组 ---
        metric_group = QGroupBox("筛选指标")
        metric_layout = QFormLayout()
        
        self.return_label = QLabel("最低年化回报率 (%)：")
        self.return_input = QDoubleSpinBox()
        self.return_input.setRange(0.0, 100.0)
        self.return_input.setSuffix(" %")
        self.return_input.setValue(20.0)
        metric_layout.addRow(self.return_label, self.return_input)
        
        self.sharpe_label = QLabel("最低夏普比率：")
        self.sharpe_input = QDoubleSpinBox()
        self.sharpe_input.setRange(0.0, 10.0)
        self.sharpe_input.setValue(1.0)
        metric_layout.addRow(self.sharpe_label, self.sharpe_input)
        
        self.volatility_label = QLabel("最高年化波动率 (%)：")
        self.volatility_input = QDoubleSpinBox()
        self.volatility_input.setRange(0.0, 100.0)
        self.volatility_input.setSuffix(" %")
        self.volatility_input.setValue(20.0)
        metric_layout.addRow(self.volatility_label, self.volatility_input)

        self.drawdown_label = QLabel("最高最大回撤率 (%)：")
        self.drawdown_input = QDoubleSpinBox()
        self.drawdown_input.setRange(0.0, 100.0)
        self.drawdown_input.setSuffix(" %")
        self.drawdown_input.setValue(30.0)
        metric_layout.addRow(self.drawdown_label, self.drawdown_input)
        
        self.drawdown_days_label = QLabel("最大回撤天数：")
        self.drawdown_days_input = QSpinBox()
        self.drawdown_days_input.setRange(1, 3650)
        self.drawdown_days_input.setValue(100)
        metric_layout.addRow(self.drawdown_days_label, self.drawdown_days_input)
        
        metric_group.setLayout(metric_layout)
        
        # --- 其他筛选条件分组 ---
        other_group = QGroupBox("其他筛选条件")
        other_layout = QFormLayout()

        self.fund_size_label = QLabel("最低基金规模 (亿元)：")
        self.fund_size_input = QDoubleSpinBox()
        self.fund_size_input.setRange(0.0, 1000.0)
        self.fund_size_input.setValue(10.0) # 默认最低10亿
        self.fund_size_input.setSuffix(" 亿")
        other_layout.addRow(self.fund_size_label, self.fund_size_input)
        
        self.fund_type_label = QLabel("基金类型：")
        self.fund_type_combo = QComboBox()
        self.fund_type_combo.addItem("所有类型", "all")
        self.fund_type_combo.addItem("股票型", "stock")
        self.fund_type_combo.addItem("混合型", "mixed")
        self.fund_type_combo.addItem("债券型", "bond")
        self.fund_type_combo.addItem("指数型", "index")
        other_layout.addRow(self.fund_type_label, self.fund_type_combo)

        other_group.setLayout(other_layout)

        # 保存文件夹选择
        self.folder_label = QLabel("保存文件夹：")
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("保存到 found 文件夹", ['found'])
        self.folder_combo.addItem("同时保存到 found 和 worker", ['found', 'worker'])

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_combo)

        # 提交按钮
        self.submit_button = QPushButton("开始筛选")
        self.submit_button.clicked.connect(self.submit)

        # 布局组合
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(basic_info_group)
        main_layout.addWidget(metric_group)
        main_layout.addWidget(other_group) # 添加新的分组
        main_layout.addLayout(folder_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.submit_button)
        self.setLayout(main_layout)

    def submit(self):
        # 获取用户输入的筛选参数
        start_code = self.start_input.text()#开始序号
        end_code = self.end_input.text()#结束序号
        fund_count = self.fund_count_input.value()#希望抓多少个
        annual_return = self.return_input.value()#最低年化回报
        sharpe_ratio = self.sharpe_input.value()#最低夏普比
        volatility = self.volatility_input.value()#最高年化波动
        max_drawdown = self.drawdown_input.value()#最高最大回撤比
        max_drawdown_days = self.drawdown_days_input.value()#最大回撤天数
        
        # 获取新的参数
        fund_size = self.fund_size_input.value()
        fund_type = self.fund_type_combo.currentData()

        # 获取用户选择的保存路径列表
        save_paths = self.folder_combo.currentData()
        
        # 打印所有输入值
        print(f"筛选条件：")
        print(f"基金序号范围：{start_code} - {end_code}")
        print(f"期望找到的基金数量：{fund_count}")
        print(f"最低年化回报率：{annual_return}%")
        print(f"最低夏普比率：{sharpe_ratio}")
        print(f"最高年化波动率：{volatility}%")
        print(f"最高最大回撤率：{max_drawdown}%")
        print(f"最大回撤天数：{max_drawdown_days}天")
        print(f"最低基金规模：{fund_size}亿元")
        print(f"基金类型：{fund_type}")
        
        # 打印用户选择的保存路径列表
        print("保存文件夹：", save_paths)
        
        # 对话框关闭，程序流程继续
        self.accept()


class FundInfoDialog(QDialog):
    """显示基金详细信息对话框"""
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详细信息")
        font = QFont("微软雅黑", 10)
        self.setFont(font)

        # 创建 QTableWidget 组件
        self.table_widget = QTableWidget(self)
        # 设置表格行数和列数
        self.table_widget.setRowCount(df.shape[0])  # DataFrame 行数
        self.table_widget.setColumnCount(df.shape[1])  # DataFrame 列数
        # 设置表格列名
        self.table_widget.setHorizontalHeaderLabels(df.columns)
        
        # 填充数据到表格
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.table_widget.setItem(row, col, item)
        
        # 自适应列宽
        self.table_widget.resizeColumnsToContents()
        # 禁用编辑功能，只允许选中和复制
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        # 保留水平滚动条
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 设置垂直滚动条为自动显示
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 自动调整行高以适应内容，设置最大行高以避免过大
        self.table_widget.setRowHeight(0, 50)  # 默认行高，确保表格可见
        max_row_height = 150  # 设置最大行高
        for row in range(df.shape[0]):
            max_height = max([len(str(df.iloc[row, col])) for col in range(df.shape[1])])
            # 根据内容调整行高，且最大行高为 150
            self.table_widget.setRowHeight(row, min(int(max(50, max_height * 1.2)), max_row_height))
        
        # 创建滚动区域，使表格可以滚动
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)  # 允许调整大小
        
        # 设置最大和最小尺寸，避免数据框占用过多空间
        scroll_area.setMaximumHeight(600)  # 设置最大高度
        scroll_area.setMinimumHeight(200)  # 设置最小高度
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        
        # 动态调整窗口大小，根据内容和表格自动调整
        num_rows = df.shape[0]
        window_height = min(600, num_rows * 40 + 100)  # 设置窗口高度，最大为600，最小为根据内容计算的大小
        self.resize(800, window_height)



class GroupConfigDialog(QDialog):
    """对话框输入组名，描述，用于创建分组"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加分组")
        Font=QFont("微软雅黑", 10)
        self.setFont(Font)
        self.resize(300, 150)
        self.group_name = ""  # 保存最终返回的组名
        self.description_text = ""  # 保存最终返回的描述
        layout = QVBoxLayout()
        layout.addWidget(QLabel("请输入分组名称："))
        self.title_input_edit = QLineEdit()
        layout.addWidget(self.title_input_edit)
        layout.addWidget(QLabel("分组描述(选填)："))
        self.description_input_edit = QLineEdit()
        layout.addWidget(self.description_input_edit)
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.reject)
    def on_ok(self):
        title_text = self.title_input_edit.text().strip()
        description_text = self.description_input_edit.text().strip()
        if not title_text:
            QMessageBox.warning(self, "错误", "请输入分组名称")
            return
        self.group_name = title_text
        if description_text:
            self.description_text = description_text
        self.accept()

    def get_group_name(self):
        return self.group_name
    def get_description_text(self):
        return self.description_text



class List_group_dialog(QDialog):
    """列出所有分组（文件夹）的对话框，双击选择某个分组"""
    def __init__(self, groups__path=None, title=None,parent=None,this_code=None):#title,this_code用于标记选中的基金代码
        super().__init__(parent)
        Font = QFont("微软雅黑", 10)
        self.setFont(Font)
        self.setWindowTitle(title if title else "选择分组")
        layout = QVBoxLayout(self)
        self.groups_path = groups__path
        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)
        self.this_code = this_code
        self.list_groups()
        if title=="选择要删除的分组":
            self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked_del)
        if title=="添加到分组":
            self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked_add)
        if title=="选择要加载的分组":
            self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked_load)
        self.center()  # 窗口居中



    def list_groups(self):
        """列出所有分组（文件夹）"""
        try:
            groups = os.listdir(self.groups_path)
            self.list_widget.clear()
            self.found_group = False
            for group in groups:
                group_path = os.path.join(self.groups_path, group)
                if os.path.isdir(group_path): 
                    item = QListWidgetItem(group)
                    self.list_widget.addItem(item)
                    self.found_group = True
            if  self.found_group is False:
                QMessageBox.information(self, "信息", "没有找到任何分组。")
                self.reject()  # 没有分组则关闭对话框
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法列出分组: {e}")

    def on_item_double_clicked_del(self, item):
        """双击列表项时关闭对话框并获取文件夹路径"""
        group_name = item.text()  # 获取双击项的文本
        group_path = os.path.join(self.groups_path, group_name)
        last_confirm = QMessageBox.warning(self, "删除确认", f"确定删除选择的分组 '{group_name}' 吗？删除后只能手动恢复", QMessageBox.Yes | QMessageBox.No)
        if last_confirm == QMessageBox.Yes:
            self.accept()  # 关闭对话框，允许进一步处理
        else:
            return
        

    def on_item_double_clicked_add(self, item):
        try:
            if self.this_code:
                exam_code=str(self.this_code).zfill(6)
                df=pd.read_csv(os.path.join(self.groups_path, "group_cache.csv"))
                matching_row = df[df['path'].str.contains(exam_code)]
            if not matching_row.empty:
                groupname = matching_row['group_name'].iloc[0]#获取对应的分组名称
                if item.text() == groupname:
                    QMessageBox.information(self, "信息", f"该基金代码已存在于分组 '{groupname}' 中。")
                    return None
            self.accept()  # 关闭对话框
        except Exception as e:
            print(f"双击事件出错: {e}")

    def on_item_double_clicked_load(self, item):
        self.accept()  # 关闭对话框

    def get_selected_group_path(self):
        """返回用户选择的分组路径"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            group_name = selected_items[0].text()
            return os.path.join(self.groups_path, group_name)
        return None

    
    def center(self):
        """将窗口居中"""
        screen = QDesktopWidget().screenGeometry()  # 获取屏幕尺寸
        size = self.geometry()  # 获取窗口尺寸
        # 计算窗口位置，使其居中
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)  # 移动窗口到计算出的中心位置
        self.resize(400, 300)  # 保持原有大小

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = advance_pulldata_dialog()
    dialog.show()
    sys.exit(app.exec_())


















































# class ArimaConfigDialog(QDialog):
#     """
#     一个用于设置ARIMA模型p, d, q参数的对话框。
#     """
#     def __init__(self, parent=None):
#         super(ArimaConfigDialog, self).__init__(parent)
#         self.setWindowTitle("设置ARIMA参数,仔细考量，否则失真")
#         self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
#         self.setFixedSize(400, 250)

#         self.p_param = ""
#         self.d_param = ""
#         self.q_param = ""

#         self.layout = QVBoxLayout(self)

#         form_layout = QFormLayout()

#         # p参数输入框
#         self.p_input = QLineEdit(self)
#         self.p_input.setPlaceholderText("通常设为2")
#         self.p_input.setText(str(self.p_param))
#         form_layout.addRow(QLabel("p (AR阶数):"), self.p_input)

#         # d参数输入框
#         self.d_input = QLineEdit(self)
#         self.d_input.setPlaceholderText("通常设为1")
#         self.d_input.setText(str(self.d_param))
#         form_layout.addRow(QLabel("d (差分阶数):"), self.d_input)

#         # q参数输入框
#         self.q_input = QLineEdit(self)
#         self.q_input.setPlaceholderText("通常设为2")
#         self.q_input.setText(str(self.q_param))
#         form_layout.addRow(QLabel("q (MA阶数):"), self.q_input)

#         self.layout.addLayout(form_layout)

#         # 按钮
#         button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
#         button_box.accepted.connect(self.accept)
#         button_box.rejected.connect(self.reject)
#         self.layout.addWidget(button_box)

#     def accept(self):
#         """
#         验证用户输入并在输入有效时接受对话框。
#         """
#         try:
#             # 如果输入为空，使用默认值
#             p_text = self.p_input.text().strip()
#             d_text = self.d_input.text().strip()
#             q_text = self.q_input.text().strip()

#             this_p = int(p_text) if p_text else 2
#             this_d = int(d_text) if d_text else 1
#             this_q = int(q_text) if q_text else 2

#             if this_p < 0 or this_d < 0 or this_q < 0:
#                 raise ValueError("参数值不能为负数")
#             self.p_param = this_p
#             self.d_param = this_d
#             self.q_param = this_q
#             super().accept()
#         except ValueError as e:
#             QMessageBox.warning(self, "无效输入", f"请输入有效的非负整数。\n错误: {e}")
#     def get_params(self):
#         """
#         返回用户设置的p, d, q参数。
#         """
#         return self.p_param, self.d_param, self.q_param



# class FourierConfigDialog(QDialog):
#     """配置 Fourier 预测参数的对话框"""
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Fourier 预测参数配置")
#         self.resize(400, 300)
#         layout = QVBoxLayout(self)
#         form_layout = QFormLayout()
#         # 阶数（harmonics）短期一到三个月时5-10，中期三个月到一年10-50，一年以上长期50-100，短期高阶放大噪音，长期高阶抗低频影响
#         self.order_spin = QSpinBox()
#         self.order_spin.setRange(1, 100)
#         self.order_spin.setValue(5)
#         form_layout.addRow("阶数 (harmonics):", self.order_spin)
#         # 周期性强弱（可以用 ComboBox 选择常见周期：日/周/月/年）
#         self.period_combo = QComboBox()
#         self.period_combo.addItems(["日", "周", "月", "年", "自定义"])
#         form_layout.addRow("周期性:", self.period_combo)
#         # 自定义周期长度（当选择“自定义”时使用）
#         self.custom_period_spin = QSpinBox()
#         self.custom_period_spin.setRange(1, 10000)
#         self.custom_period_spin.setValue(30)
#         form_layout.addRow("自定义周期长度:", self.custom_period_spin)
#         # 趋势处理（是否去趋势）
#         self.detrend_check = QCheckBox("保留趋势 (detrend)")
#         self.detrend_check.setChecked(True)
#         form_layout.addRow("趋势处理:", self.detrend_check)
#         # 采样频率（窗口内的数据点数），短期1-3，中期3-5，长期5-10以上
#         self.sampling_spin = QSpinBox()
#         self.sampling_spin.setRange(1, 100)
#         self.sampling_spin.setValue(1)
#         form_layout.addRow("采样频率:", self.sampling_spin)
#         # 窗口长度
#         self.window_spin = QSpinBox()
#         self.window_spin.setRange(10, 10000)
#         self.window_spin.setValue(30)
#         form_layout.addRow("窗口长度:", self.window_spin)
#         # 噪声控制（平滑强度）
#         self.smoothing_spin = QDoubleSpinBox()
#         self.smoothing_spin.setRange(0.0, 1.0)
#         self.smoothing_spin.setSingleStep(0.05)
#         self.smoothing_spin.setValue(0.2)
#         form_layout.addRow("噪声控制 (平滑强度):", self.smoothing_spin)
#         # 外推策略
#         self.extrapolation_combo = QComboBox()
#         self.extrapolation_combo.addItems(["直接外推", "滚动窗口预测(高级)", "与趋势模型融合"])
#         form_layout.addRow("外推策略:", self.extrapolation_combo)
#         #预测天数
#         self.expect_days_spin = QSpinBox()
#         self.expect_days_spin.setRange(1, 3650)
#         self.expect_days_spin.setValue(30)
#         form_layout.addRow("预测天数:", self.expect_days_spin)
#         layout.addLayout(form_layout)
#         #启用过拟合
#         self.enable_fit_check = QCheckBox("启用过拟合")
#         self.enable_fit_check.setChecked(False)
#         layout.addWidget(self.enable_fit_check)
#         # 按钮
#         self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
#         self.button_box.accepted.connect(self.accept)
#         self.button_box.rejected.connect(self.reject)
#         layout.addWidget(self.button_box)
#     def get_params(self):
#         """返回所有参数"""
#         return (
#             self.order_spin.value(),#阶数
#             self.period_combo.currentText(),#周期性
#             self.custom_period_spin.value(),#自定义周期
#             self.detrend_check.isChecked(),#是否去趋势
#             self.sampling_spin.value(),#采样频率
#             self.window_spin.value(),#窗口长度
#             self.smoothing_spin.value(),#平滑强度
#             self.expect_days_spin.value(),#预测天数
#             self.extrapolation_combo.currentText(),#外推策略
#             self.enable_fit_check.isChecked()
#         )


