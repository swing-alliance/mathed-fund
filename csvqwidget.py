import pandas as pd
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QFont 
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import numpy as np

# 设置matplotlib的全局样式
plt.style.use('default')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class MplCanvas(FigureCanvas):
    """一个自适应的 Matplotlib 画布，用于绘制图形。"""
    def __init__(self, parent=None, dpi=100):
        self.fig = Figure(figsize=(10, 7.5), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes: Axes = self.fig.add_subplot(111)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()
        # 绑定鼠标滚轮事件，实现放大缩小
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        # 绑定鼠标点击和释放事件，用于双击还原和拖动
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        # 用于记录拖动状态和初始位置
        self.press = None
        
    def on_scroll(self, event):
        """处理鼠标滚轮事件以实现放大和缩小。"""
        if event.xdata is None or event.ydata is None:
            return
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        scale_factor = 1.2

        if event.button == 'up':
            # 向上滚动，放大
            x_min_new = event.xdata - (event.xdata - x_min) / scale_factor
            x_max_new = event.xdata + (x_max - event.xdata) / scale_factor
            y_min_new = event.ydata - (event.ydata - y_min) / scale_factor
            y_max_new = event.ydata + (y_max - event.ydata) / scale_factor
        elif event.button == 'down':
            # 向下滚动，缩小
            x_min_new = event.xdata - (event.xdata - x_min) * scale_factor
            x_max_new = event.xdata + (x_max - event.xdata) * scale_factor
            y_min_new = event.ydata - (event.ydata - y_min) * scale_factor
            y_max_new = event.ydata + (y_max - event.ydata) * scale_factor
        else:
            return

        self.axes.set_xlim(x_min_new, x_max_new)
        self.axes.set_ylim(y_min_new, y_max_new)
        self.fig.canvas.draw_idle()

    def on_press(self, event):
        """处理鼠标按下事件，用于双击还原和记录拖动起始点。"""
        # 如果是左键双击，则还原视图
        if event.button == 1 and event.dblclick:
            self.axes.autoscale(enable=True, axis='both', tight=True)
            self.axes.figure.autofmt_xdate()
            self.draw_idle()
            return
        # 记录左键按下的初始位置
        if event.button == 1 and event.inaxes:
            self.press = event.xdata, event.ydata

    def on_motion(self, event):
        """处理鼠标移动事件，用于拖动。"""
        if self.press is None or event.inaxes is None or event.button != 1:
            return
        # 计算拖动偏移量
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        dx = event.xdata - self.press[0]
        dy = event.ydata - self.press[1]
        # 更新坐标轴范围
        self.axes.set_xlim(x_min - dx, x_max - dx)
        self.axes.set_ylim(y_min - dy, y_max - dy)
        self.draw_idle()

    def on_release(self, event):
        """处理鼠标释放事件，结束拖动。"""
        self.press = None

class CsvGraphWidget(QWidget):
    """一个QWidget，用于展示基金净值折线图，新增时间范围选择功能。"""
    def __init__(self, df, parent=None):
        super(CsvGraphWidget, self).__init__(parent)
        # 游标和事件ID的初始化
        self._active_cursor: mplcursors.cursor = None
        self._click_cid = None
        try:
            self.original_df: pd.DataFrame = df.copy()
            self.original_df['净值日期'] = pd.to_datetime(self.original_df['净值日期'], format='%Y-%m-%d')
            self.original_df.sort_values(by='净值日期', inplace=True)  # 按日期排序
            self.current_df: pd.DataFrame = None
        except KeyError:
            raise ValueError("CSV文件缺少'净值日期'或'单位净值'列。")
        except ValueError:
            raise ValueError("CSV文件'净值日期'列的格式不正确，应为'YYYY-MM-DD'。")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.load_elements()
        
    def load_elements(self):
        self.time_range_combo = QComboBox(self)
        self.time_range_combo.addItems(['过去15天', '过去30天', '过去60天', '过去90天', '过去180天', '过去一年',"过去两年","过去三年", '过去十年', '全部'])
        self.time_range_combo.setCurrentText('过去30天')
        self.time_range_combo.setFont(QFont("微软雅黑", 11))
        self.time_range_combo.setMinimumWidth(100)
        self.time_range_combo.setMinimumHeight(25)
        self.layout.addWidget(self.time_range_combo)
        self.canvas = MplCanvas()
        self.layout.addWidget(self.canvas)
        self.layout.setContentsMargins(5, 0, 0, 2)
        self.time_range_combo.currentTextChanged.connect(self.update_plot_by_range)
        # 初始化图表
        self.update_plot_by_range(self.time_range_combo.currentText())

    def update_plot_by_range(self, text):
        """根据下拉菜单的选择更新图表。"""
        if text == '全部':
            self.current_df: pd.DataFrame = self.original_df.copy()
        else:
            days: int = 0
            if text == '过去15天': days = 15
            elif text == '过去30天': days = 30
            elif text == '过去60天': days = 60
            elif text == '过去90天': days = 90
            elif text == '过去180天': days = 180
            elif text == '过去一年': days = 365
            elif text == '过去两年': days = 730
            elif text == '过去三年': days = 1095
            elif text == '过去十年': days = 3650 
            
            last_date: pd.Timestamp = self.original_df['净值日期'].max()
            start_date = last_date - pd.Timedelta(days=days)
            self.current_df = self.original_df[self.original_df['净值日期'] >= start_date].copy()
            
        self._plot_data()

    def _setup_cursor_and_events(self):
        """设置游标和事件绑定，有bug，不建议使用。"""
        def on_click(event):
            line = self.canvas.axes.lines[0] if self.canvas.axes.lines else None
            if line is None:
                return
            # 如果点击在画布外，则销毁游标并退出
            if not event.inaxes:
                if self._active_cursor is not None:
                    self._active_cursor.remove()
                    self._active_cursor = None
                    self.canvas.draw_idle()
                return
            contains, info = line.contains(event)
            if contains:
                if self._active_cursor is None:
                    self._active_cursor = mplcursors.cursor(line, hover=False, highlight=True)
                    # 连接 'add' 事件，它会在选中时自动触发
                    @self._active_cursor.connect("add")
                    def on_add(sel):
                        x, y = sel.target
                        dt = mdates.num2date(x)
                        sel.annotation.set_text(f"{dt:%Y-%m-%d}\n净值: {y:.4f}")
                        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
                # --- 关键改动在这里 ---
                # 使用库的内部方法来获取正确的 Selection 对象
                sel = self._active_cursor._get_selection_at_point(event)
                if sel:
                    # 找到 Selection 对象后，手动添加它
                    self._active_cursor.add_selection(sel)
            else:
                # 如果点击在空白处，则销毁游标
                if self._active_cursor is not None:
                    self._active_cursor.remove()
                    self._active_cursor = None
            self.canvas.draw_idle()
        # 断开旧的连接，防止重复绑定
        if self._click_cid is not None:
            self.canvas.mpl_disconnect(self._click_cid)
        self._click_cid = self.canvas.mpl_connect("button_press_event", on_click)

        
    def _plot_data(self):
        """内部方法，仅用于绘制数据。"""
        try:
            self.canvas.axes.clear()
            if '单位净值' in self.current_df.columns:
                self.canvas.axes.plot(
                    self.current_df['净值日期'], 
                    self.current_df['单位净值'], 
                    linestyle='-', linewidth=1, 
                    marker='o', markersize=2, 
                    markerfacecolor='red', markeredgecolor='red',
                    label='单位净值'
                )
            if '累计净值' in self.current_df.columns:
                self.canvas.axes.plot(
                    self.current_df['净值日期'], 
                    self.current_df['累计净值'], 
                    linestyle='-', linewidth=1, 
                    marker='o', markersize=2, 
                    markerfacecolor='blue', markeredgecolor='blue',
                    label='累计净值'
                )
            self.canvas.axes.set_title('基金净值走势图')
            self.canvas.axes.set_xlabel('净值日期')
            self.canvas.axes.set_ylabel('净值')
            self.canvas.axes.grid(True, linestyle='-', alpha=0.7, zorder=10)
            self.canvas.axes.legend()

            self.canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.canvas.axes.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.canvas.figure.autofmt_xdate()
            self.canvas.figure.tight_layout()
            self.canvas.draw()
        except KeyError as e:
            print(f"DataFrame缺少必要的列: {e}")
        except Exception as e:
            print(f"绘制图形时发生错误: {e}")

    def use_arima(self, p=2, d=1, q=2, periods=30):
        """
        使用 ARIMA 模型对当前 QWidget 显示的数据进行预测，并在图上绘制预测曲线。
        参数：
            p, d, q : int   ARIMA 模型参数
            periods : int   预测天数
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            # 取当前显示区间的数据
            df = self.current_df.copy()
            if df.empty:
                print("当前区间没有数据，无法预测")
                return
            # 设置时间序列索引并指定频率（工作日）
            series = df.set_index('净值日期')['单位净值']
            series = series.asfreq('B')  # B 表示工作日频率
            series = series.fillna(method='ffill')  # 填充缺失值
            # 建立 ARIMA 模型
            model = ARIMA(series, order=(p, d, q))
            model_fit = model.fit()
            # 预测未来 periods 天
            forecast = model_fit.forecast(steps=periods)
            # forecast.index 已有频率，不再报警告
            # 绘制预测曲线
            self.canvas.axes.plot(
                forecast.index,
                forecast.values,
                linestyle='--',
                color='red',
                marker='x',
                markersize=3,
                label=f'ARIMA预测({p},{d},{q})'
            )
            # 更新图例和画布
            self.canvas.axes.legend()
            self.canvas.draw()
        except Exception as e:
            print(f"ARIMA预测失败: {e}")


    def use_fourier(self, order=None, period=None, custom_period=None, is_trend=None,
                    sampling=None, window=None, smoothing=None, expect_days=None,
                    extrapolation_strategy="直接外推", overfit=False, rolling_step_size=1):
        try:
            # 数据检查和预处理 (这部分代码保持不变)
            df = self.current_df.copy()
            if df.empty:
                print("当前区间没有数据，无法预测")
                return
            series = df.set_index('净值日期')['单位净值'].copy()
            series = pd.to_numeric(series, errors='coerce').dropna()

            if overfit:
                window = len(series)
                series = series.iloc[-window:]
                sampling = 1
                smoothing = 1.0
                T = len(series)
                order = max(1, (len(series) - 1) // 2)
            else:
                window = min(int(window), len(series))
                series = series.iloc[-window:]
                sampling = max(int(sampling), 1)
                series = series.iloc[::sampling]
                smoothing = max(float(smoothing), 1)
                if smoothing > 1:
                    series = series.rolling(window=int(smoothing), min_periods=1).mean()
                period_map = {"日": 1, "周": 5, "月": 21, "年": 252}
                if isinstance(period, str):
                    T = period_map.get(period, int(custom_period))
                else:
                    T = int(period)
                max_order = max(1, (len(series) - 1) // 2)
                order = min(int(order), max_order)

            # --- 核心预测逻辑 ---
            expect_days = max(int(expect_days), 1)
            forecast_results = []
            current_series = series.copy()

            if extrapolation_strategy == "滚动窗口预测(高级)":
                rolling_step_size = max(int(rolling_step_size), 1)
                
                # 循环预测，每次预测一个步长
                for _ in range(0, expect_days, rolling_step_size):
                    
                    # 确保窗口大小不小于阶数
                    current_window = current_series.iloc[-window:]
                    if len(current_window) < 2 * order + 1:
                         print("数据窗口太小，无法进行傅里叶拟合")
                         return

                    t = np.arange(len(current_window))
                    y = current_window.values
                    
                    # 趋势处理 (与直接外推的趋势处理逻辑一致)
                    if is_trend:
                        coeffs = np.polyfit(t, y, 1)
                        trend_predict_func = lambda t_vals: np.polyval(coeffs, t_vals)
                        y_detrended = y - trend_predict_func(t)
                    else:
                        y_detrended = y
                        trend_predict_func = lambda t_vals: np.zeros_like(t_vals)

                    # 傅里叶拟合
                    X = np.ones((len(t), 1))
                    for k in range(1, order + 1):
                        X = np.column_stack([X,
                                            np.sin(2 * np.pi * k * t / T),
                                            np.cos(2 * np.pi * k * t / T)])
                    try:
                        coef, _, _, _ = np.linalg.lstsq(X, y_detrended, rcond=None)
                    except np.linalg.LinAlgError as e:
                        print(f"滚动窗口预测 - 傅里叶拟合失败: {e}")
                        return
                    
                    # 预测下一个步长
                    t_future = np.arange(len(t), len(t) + rolling_step_size)
                    X_future = np.ones((len(t_future), 1))
                    for k in range(1, order + 1):
                        X_future = np.column_stack([X_future,
                                                    np.sin(2 * np.pi * k * t_future / T),
                                                    np.cos(2 * np.pi * k * t_future / T)])
                    
                    y_future = X_future @ coef
                    y_future = y_future + trend_predict_func(t_future)
                    
                    # 更新数据序列
                    current_series = pd.concat([current_series, pd.Series(y_future)])
                    forecast_results.extend(y_future)
                
                # 截取预测结果到 expect_days 的长度
                forecast_results = forecast_results[:expect_days]

            elif extrapolation_strategy in ["直接外推", "与趋势模型融合"]:
                # --- 原有的直接外推逻辑 ---
                t = np.arange(len(current_series))
                y = current_series.values
                
                if is_trend:
                    coeffs = np.polyfit(t, y, 1)
                    y_detrended = y - np.polyval(coeffs, t)
                else:
                    y_detrended = y

                X = np.ones((len(t), 1))
                for k in range(1, order + 1):
                    X = np.column_stack([X, np.sin(2 * np.pi * k * t / T), np.cos(2 * np.pi * k * t / T)])
                try:
                    coef, _, _, _ = np.linalg.lstsq(X, y_detrended, rcond=None)
                except np.linalg.LinAlgError as e:
                    print(f"直接外推 - 傅里叶拟合失败: {e}")
                    return

                # 未来预测
                t_future = np.arange(len(t), len(t) + expect_days)
                X_future = np.ones((len(t_future), 1))
                for k in range(1, order + 1):
                    X_future = np.column_stack([X_future, np.sin(2 * np.pi * k * t_future / T), np.cos(2 * np.pi * k * t_future / T)])
                
                y_future = X_future @ coef
                
                if is_trend:
                    trend_future = np.polyval(coeffs, t_future)
                    y_future = y_future + trend_future
                
                forecast_results = y_future.tolist()
            else:
                print("无效的外推策略。")
                return

            # --- 结果绘图 (这部分代码保持不变) ---
            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date, periods=len(forecast_results) + 1, freq="B")[1:]
            forecast = pd.Series(forecast_results, index=future_dates)
            
            self.canvas.axes.plot(
                forecast.index,
                forecast.values,
                linestyle="--",
                color="green",
                marker="s",
                markersize=3,
                label=f"Fourier预测(order={order}, 策略={extrapolation_strategy})"
            )
            self.canvas.axes.legend()
            self.canvas.draw()

        except Exception as e:
            print(f"Fourier预测失败: {e}")



    def save_snapshot(self, filename="", dpi=300):
        """接受文件名和dpi作为参数。"""
        self.canvas.figure.savefig(filename, dpi=dpi)


