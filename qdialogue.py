from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QLineEdit, QLabel, QMessageBox, QPushButton, 
                             QHBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,QHeaderView,QTableWidget,QTableWidgetItem
                             ,QScrollArea)
from PyQt5.QtCore import Qt
import re
import akshare as ak
from PyQt5.QtGui import QFont 



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
        # 信号绑定
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.reject)

    def on_ok(self):
        text = self.input_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "错误", "请输入至少一个基金代码")
            return
        # 使用正则提取六位数字
        codes = re.findall(r'\b\d{6}\b', text)
        if not codes:
            QMessageBox.warning(self, "错误", "请输入有效的六位数字")
            return
        self.codes = codes
        self.accept()



class ArimaConfigDialog(QDialog):
    """
    一个用于设置ARIMA模型p, d, q参数的对话框。
    """
    def __init__(self, parent=None):
        super(ArimaConfigDialog, self).__init__(parent)
        self.setWindowTitle("设置ARIMA参数,仔细考量，否则失真")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(400, 250)

        self.p_param = ""
        self.d_param = ""
        self.q_param = ""

        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # p参数输入框
        self.p_input = QLineEdit(self)
        self.p_input.setPlaceholderText("通常设为2")
        self.p_input.setText(str(self.p_param))
        form_layout.addRow(QLabel("p (AR阶数):"), self.p_input)

        # d参数输入框
        self.d_input = QLineEdit(self)
        self.d_input.setPlaceholderText("通常设为1")
        self.d_input.setText(str(self.d_param))
        form_layout.addRow(QLabel("d (差分阶数):"), self.d_input)

        # q参数输入框
        self.q_input = QLineEdit(self)
        self.q_input.setPlaceholderText("通常设为2")
        self.q_input.setText(str(self.q_param))
        form_layout.addRow(QLabel("q (MA阶数):"), self.q_input)

        self.layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

    def accept(self):
        """
        验证用户输入并在输入有效时接受对话框。
        """
        try:
            # 如果输入为空，使用默认值
            p_text = self.p_input.text().strip()
            d_text = self.d_input.text().strip()
            q_text = self.q_input.text().strip()

            this_p = int(p_text) if p_text else 2
            this_d = int(d_text) if d_text else 1
            this_q = int(q_text) if q_text else 2

            if this_p < 0 or this_d < 0 or this_q < 0:
                raise ValueError("参数值不能为负数")
            self.p_param = this_p
            self.d_param = this_d
            self.q_param = this_q
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "无效输入", f"请输入有效的非负整数。\n错误: {e}")
    def get_params(self):
        """
        返回用户设置的p, d, q参数。
        """
        return self.p_param, self.d_param, self.q_param



class FourierConfigDialog(QDialog):
    """配置 Fourier 预测参数的对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fourier 预测参数配置")
        self.resize(400, 300)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        # 阶数（harmonics）短期一到三个月时5-10，中期三个月到一年10-50，一年以上长期50-100，短期高阶放大噪音，长期高阶抗低频影响
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 100)
        self.order_spin.setValue(5)
        form_layout.addRow("阶数 (harmonics):", self.order_spin)
        # 周期性强弱（可以用 ComboBox 选择常见周期：日/周/月/年）
        self.period_combo = QComboBox()
        self.period_combo.addItems(["日", "周", "月", "年", "自定义"])
        form_layout.addRow("周期性:", self.period_combo)
        # 自定义周期长度（当选择“自定义”时使用）
        self.custom_period_spin = QSpinBox()
        self.custom_period_spin.setRange(1, 10000)
        self.custom_period_spin.setValue(30)
        form_layout.addRow("自定义周期长度:", self.custom_period_spin)
        # 趋势处理（是否去趋势）
        self.detrend_check = QCheckBox("保留趋势 (detrend)")
        self.detrend_check.setChecked(True)
        form_layout.addRow("趋势处理:", self.detrend_check)
        # 采样频率（窗口内的数据点数），短期1-3，中期3-5，长期5-10以上
        self.sampling_spin = QSpinBox()
        self.sampling_spin.setRange(1, 100)
        self.sampling_spin.setValue(1)
        form_layout.addRow("采样频率:", self.sampling_spin)
        # 窗口长度
        self.window_spin = QSpinBox()
        self.window_spin.setRange(10, 10000)
        self.window_spin.setValue(30)
        form_layout.addRow("窗口长度:", self.window_spin)
        # 噪声控制（平滑强度）
        self.smoothing_spin = QDoubleSpinBox()
        self.smoothing_spin.setRange(0.0, 1.0)
        self.smoothing_spin.setSingleStep(0.05)
        self.smoothing_spin.setValue(0.2)
        form_layout.addRow("噪声控制 (平滑强度):", self.smoothing_spin)
        # 外推策略
        self.extrapolation_combo = QComboBox()
        self.extrapolation_combo.addItems(["直接外推", "滚动窗口预测(高级)", "与趋势模型融合"])
        form_layout.addRow("外推策略:", self.extrapolation_combo)
        #预测天数
        self.expect_days_spin = QSpinBox()
        self.expect_days_spin.setRange(1, 3650)
        self.expect_days_spin.setValue(30)
        form_layout.addRow("预测天数:", self.expect_days_spin)
        layout.addLayout(form_layout)
        #启用过拟合
        self.enable_fit_check = QCheckBox("启用过拟合")
        self.enable_fit_check.setChecked(False)
        layout.addWidget(self.enable_fit_check)
        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    def get_params(self):
        """返回所有参数"""
        return (
            self.order_spin.value(),#阶数
            self.period_combo.currentText(),#周期性
            self.custom_period_spin.value(),#自定义周期
            self.detrend_check.isChecked(),#是否去趋势
            self.sampling_spin.value(),#采样频率
            self.window_spin.value(),#窗口长度
            self.smoothing_spin.value(),#平滑强度
            self.expect_days_spin.value(),#预测天数
            self.extrapolation_combo.currentText(),#外推策略
            self.enable_fit_check.isChecked()
        )


class FundInfoDialog(QDialog):
    """显示基金详细信息对话框"""
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详细信息")
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
        self.resize(800, window_height)  # 设置初始窗口大小，800宽，动态高度