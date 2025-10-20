"""计算层"""
import os
import pandas as pd
import numpy as np
import akshare as ak
import statsmodels.api as sm
from numpy.polynomial.polynomial import Polynomial
from typing import Optional, Tuple
from datetime import datetime, timedelta,date
from typing import Optional, Tuple, List, Union
from typing import Union, Dict, Callable
from sklearn.linear_model import LinearRegression
import math
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas




def readcsv(path):
    df = pd.read_csv(path)
    return df


# fund_info_df = ak.fund_individual_basic_info_xq(symbol="000309")，返回基金信息
# df_new = ak.fund_open_fund_info_em(symbol="000216", indicator="累计净值走势")，返回累计净值走势

#年化比率

#滑动窗口年化比率
def year_rate_sliding(code,df, base_date=None,window_size_days=30, step_size_days=7):
    """滑动窗口年化，反应大方向的趋势，具有延后性，不够敏感,base_date以前的数据不计算年化收益率"""
    if df.empty:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        except Exception as e:
            print(f"获取基金 {code} 数据失败: {e}")
            return None, None
    else:
        df=df.copy()
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values("净值日期").reset_index(drop=True)
        if len(df) < window_size_days:
            print(f"基金 {code} 的数据不足，无法计算年化收益率。")
            return None, None
        window_size_days = window_size_days  
        step_size_days = step_size_days      
        annualized_returns = []
        window_dates = []
        end_date = df['净值日期'].iloc[-1]
        while True:
            window_end_date = end_date
            window_start_date = window_end_date - pd.Timedelta(days=window_size_days)
            if window_start_date < df['净值日期'].iloc[0]:
                print(f"基金{code}的{window_start_date}到{window_end_date}数据不足，或是计算完了。")
                break
            if base_date and window_end_date < pd.to_datetime(base_date):
                print(f'设置了base_date为{base_date},到base_date结束计算')
                break
            df_window = df[(df['净值日期'] >= window_start_date) & (df['净值日期'] <= window_end_date)]#重置窗口
            if len(df_window) < 2:
                return None, None
            start_value = df_window['累计净值'].iloc[0]
            end_value = df_window['累计净值'].iloc[-1]
            if start_value <= 0 or end_value <= 0:
                return None, None
            years = (df_window['净值日期'].iloc[-1] - df_window['净值日期'].iloc[0]).days / 365.25#代表window_size_days是多少年
            if years <= 0:#不可能发生？
                end_date = end_date - pd.Timedelta(days=step_size_days)
                continue
            annualized_return = (end_value / start_value) ** (1 / years) - 1
            annualized_returns.append(annualized_return)
            window_dates.append(window_end_date)
            print(f"基金{code}的{window_start_date}到{window_end_date}年化收益率约为{annualized_return}")
            end_date = end_date - pd.Timedelta(days=step_size_days)
        return annualized_returns[0], window_dates[0]

def yearly_return_since_start(code: str, df: pd.DataFrame) -> float:
    """计算基金成立以来的年化收益率"""
    if df.empty:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        except Exception as e:
            print(f"获取基金 {code} 数据失败: {e}")
            return None
    else:
        df = df.copy()
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values("净值日期").reset_index(drop=True)
        if len(df) < 2:
            print(f"基金 {code} 的数据不足，无法计算年化收益率。")
            return None
        start_value = df['累计净值'].iloc[0]
        end_value = df['累计净值'].iloc[-1]
        if start_value <= 0 or end_value <= 0:
            print(f"基金 {code} 的累计净值异常，无法计算年化收益率。")
            return None
        total_days = (df['净值日期'].iloc[-1] - df['净值日期'].iloc[0]).days
        years = total_days / 365.25
        if years <= 0:
            print(f"基金 {code} 的数据时间段不足，无法计算年化收益率。")
            return None
        annualized_return = (end_value / start_value) ** (1 / years) - 1
        return annualized_return

def how_long_since_start(code: str, df: pd.DataFrame) -> int:
    """计算基金成立以来的天数"""
    if df.empty:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        except Exception as e:
            print(f"获取基金 {code} 数据失败: {e}")
            return None
    else:
        df = df.copy()
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values("净值日期").reset_index(drop=True)
        if len(df) < 2:
            print(f"基金 {code} 的数据不足，无法计算成立天数。")
            return None
        total_days = (df['净值日期'].iloc[-1] - df['净值日期'].iloc[0]).days
        return total_days

def linear_regression_sliding_window(code: str, df: pd.DataFrame, window_size: int = 30):
    """线性回归窗口，反应大方向的趋势"""
    if code and not df.empty:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        except Exception as e:
            print(f"获取基金 {code} 数据失败: {e}")
            return []
    elif df is not None and not df.empty:
        df = df.copy()
    try:
        df['净值日期'] = pd.to_datetime(df['净值日期'],errors='coerce')
        df = df.dropna(subset=['净值日期'])
        df = df.sort_values("净值日期").reset_index(drop=True)
        df=df.tail(window_size)
        if len(df) < window_size:
            print(f"基金 {code} 的数据不足，无法进行线性回归计算。")
            return []
        df['天数'] = (df['净值日期'] - df['净值日期'].min()).dt.days
        X = df['天数'].values.reshape(-1, 1)
        y = df['累计净值'].values
        model = LinearRegression()
        model.fit(X, y)
        slope = model.coef_[0]
        intercept = model.intercept_
        proximate_yearly_return_index = slope * 252  # 252个交易日年化收益率
        func_str = f"y = {slope:.4f} * X + {intercept:.4f}"
        return func_str, proximate_yearly_return_index,slope
    except Exception as e:
        print(f"数据预处理失败: {e}")
#夏普比率
# def sharp_ratio(code,df):
#     return np.mean(annualized_returns) / np.std(annualized_returns)

#最高年化波动
def get_annualized_volatility_for_period(code: str, df: pd.DataFrame, period_days: int) -> tuple[float, pd.Timestamp]:
    """
    计算并返回基金在过去指定天数内的年化波动率。

    参数:
    - code (str): 基金代码，例如 '001211'。
    - df (pd.DataFrame): 基金数据，必须包含'净值日期'和'累计净值'列。
    - period_days (int): 要计算的时间段（例如过去 365 天或 30 天）。
    
    返回:
    - tuple[float, pd.Timestamp]: 一个元组，包含年化波动率和计算时使用的日期范围。
                                  如果数据获取失败，则返回 (None, None)。
    """
    if df.empty:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
            if df.empty:
                print(f"基金 {code} 数据获取失败：返回数据为空。")
                return None, None
        except Exception as e:
            print(f"获取基金 {code} 数据失败：{e}")
            return None, None
    else:
        df = df.copy()
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
        df.dropna(subset=['累计净值'], inplace=True)

        # 计算时间段内的起始日期
        end_date = df['净值日期'].max()  # 数据的最后日期
        start_date = end_date - timedelta(days=period_days)  # 计算过去指定天数的起始日期

        # 筛选出数据范围内的数据
        df_period = df[df['净值日期'] >= start_date]
        
        if len(df_period) < 2:
            print(f"数据点不足以计算过去 {period_days} 天的年化波动率。")
            return None, None

        # 计算每日收益率
        daily_returns = df_period['累计净值'].pct_change().dropna()
        
        # 计算波动率并年化
        daily_volatility = daily_returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)

        return annualized_volatility, start_date

#最大回撤率

#最大回撤天数

def find_top_n_cycles(
    code: str, 
    start_date: Union[str, pd.Timestamp], 
    end_date: Union[str, pd.Timestamp], 
    n_cycles: int = 1,  # 希望返回的最佳周期数量
    min_cycle: float = 2.0  # 最小周期长度（天），用于过滤高频噪声
) -> List[float]:
    """
    自动找到时间序列的 N 个最佳周期长度，通过 FFT 检测频率的主峰。
    
    参数:
    - code: 基金代码（str）。
    - start_date: 起始日期（str 或 pd.Timestamp）。
    - end_date: 结束日期（str 或 pd.Timestamp）。
    - n_cycles: 希望返回的最佳周期数量。
    - min_cycle: 最小周期长度，用于过滤高频噪声。
    
    返回:
    - 最佳周期长度列表（List[float]）。
    """
    try:
        # 获取基金数据
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return []

    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df.set_index('净值日期', inplace=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    df = df.loc[start:end]
    
    if df.empty:
        print(f"指定日期范围内没有数据: {start} - {end}")
        return []
    series = df['累计净值'].values
    N_data = len(series)
    fft_result = np.fft.fft(series)
    fft_freq = np.fft.fftfreq(N_data, d=1)  # d=1 表示时间间隔为 1 天
    fft_magnitude = np.abs(fft_result)
    positive_freq_idx = fft_freq > 0.0001  # 过滤掉直流分量
    filtered_freq = fft_freq[positive_freq_idx]
    filtered_magnitude = fft_magnitude[positive_freq_idx]
    cycle_lengths = 1 / filtered_freq
    valid_idx = cycle_lengths >= min_cycle
    cycle_lengths = cycle_lengths[valid_idx]
    valid_magnitude = filtered_magnitude[valid_idx]

    if len(valid_magnitude) == 0:
        print("没有找到满足最小周期限制的有效周期。")
        return []
    top_n_indices = np.argsort(valid_magnitude)[::-1][:n_cycles]
    optimal_cycles = cycle_lengths[top_n_indices]
    print(f"基金代码 {code}，自动检测到 {n_cycles} 个最佳周期长度 (天): {optimal_cycles}")
    return np.round(optimal_cycles, 2).tolist()




def fourier_worm_rolling(
    code: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    sampling_frequency: str,
    order: int,
    df_row: pd.DataFrame = None,
    window_size: Optional[int] = None,
    prediction_steps: int = 10,
    trend_added: bool = True,
    max_daily_volatility: float = 0.02, # 用于平滑极限，限制预测值与前一值的偏差
    global_trend_weight: float = 0.2,
    cycle_length: Optional[float] = 181.5
) -> Tuple[pd.DatetimeIndex, pd.Series, str]:
    
    # 验证 sampling_frequency
    valid_frequencies = ['D', 'W', 'M', 'Q', 'Y']
    if sampling_frequency not in valid_frequencies:
        print(f"无效的重采样频率: {sampling_frequency}。支持的频率: {valid_frequencies}")
        return None, None, None
        
    # 转换为 pd.Timestamp
    try:
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
    except Exception as e:
        print(f"日期转换失败: {e}")
        return None, None, None

    # 获取数据
    df = df_row.copy() if df_row is not None else mock_ak_fund_open_fund_info_em(symbol=code, indicator="累计净值走势") # 使用 mock 函数代替 akshare
    # if df_row is None:
    #     try:
    #         df: pd.DataFrame = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    #     except Exception as e:
    #         print(f"获取基金 {code} 数据失败: {e}")
    #         return None, None, None

    # 数据预处理
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df.set_index('净值日期', inplace=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)
    
    # 重采样并保留最后真实值
    try:
        df = df.loc[start_date:end_date]
        df = df.resample(sampling_frequency).last().ffill()
        df.dropna(subset=['累计净值'], inplace=True)
    except Exception as e:
        print(f"数据重采样或切片失败: {e}")
        return None, None, None
        
    if df.empty:
        print("数据为空，请检查日期范围或数据源。")
        return None, None, None
        
    series = df['累计净值']
    
    # **关键修改点 1: 全局时间轴 t**
    t_global = np.arange(len(series)) 
    
    if window_size is None:
        window_size = max(30, len(series) // 5)
        
    if window_size <= 0 or window_size > len(series):
        print(f"无效的窗口大小: {window_size}。数据长度为 {len(series)}。")
        return None, None, None
        
    if cycle_length is None:
        cycle_length = window_size
    cycle_length = max(5, min(cycle_length, window_size)) # 限制周期长度
    
    
    # 全局趋势计算 (基于整个 series)
    if trend_added:
        coeffs_global = np.polyfit(t_global, series.values, 1)
        # 全局趋势函数 (基于 t_global 时间轴)
        global_trend_func = lambda t_vals: np.polyval(coeffs_global, t_vals)
        # 记录全局趋势的最后一个点值和斜率
        global_trend_last_val = global_trend_func(t_global[-1])
        global_trend_slope = coeffs_global[0]
        # 整个序列的残差（用于确定傅里叶拟合的目标）
        series_detrended_global = series.values - global_trend_func(t_global)
        print(f"全局趋势斜率: {global_trend_slope}")
    else:
        global_trend_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)
        global_trend_slope = 0.0
        
    # 预测日期范围
    # 注意：pd.Timedelta(seconds=1) 确保从 end_date 后的第一个频率开始
    future_dates = pd.date_range(start=end_date + pd.Timedelta(seconds=1), periods=prediction_steps, freq=sampling_frequency)
    
    forecast_results = []
    
    if len(series) < window_size:
        print(f"数据长度 {len(series)} 小于窗口大小 {window_size}，无法进行滚动预测。")
        return None, None, None
        
    current_series = series.copy()
    
    # **关键修改点 2: 滚动预测循环**
    for i in range(prediction_steps):
        
        # 始终取当前 series 的最后 window_size 个数据
        current_window = current_series[-window_size:]
        
        # t_window: 窗口内的时间轴 (从 0 开始)
        t_window = np.arange(window_size)
        
        # **关键修改点 3: 确定当前窗口在全局时间轴上的起点和终点**
        # 窗口的最后一个点的全局时间轴索引
        t_last_global = len(series) + i - 1 
        # 窗口的起始点的全局时间轴索引
        t_start_global = t_last_global - window_size + 1 
        
        t_global_window = np.arange(t_start_global, t_last_global + 1)

        
        # 局部趋势计算 (基于当前窗口)
        # 使用局部趋势来帮助 detrending
        if trend_added:
            coeffs_local = np.polyfit(t_global_window, current_window.values, 1)
            local_trend_func = lambda t_vals: np.polyval(coeffs_local, t_vals)
            
            # 使用局部趋势对窗口进行去趋势
            y_detrended = current_window.values - local_trend_func(t_global_window)
        else:
            y_detrended = current_window.values
            
        n = len(y_detrended)
        k = np.arange(1, order + 1)
        
        # **关键修改点 4: 傅里叶拟合 (基于去趋势后的残差)**
        t_grid_local = t_window[:, np.newaxis] # 窗口时间轴，从 0 到 window_size-1
        X_fourier = np.hstack([
            np.ones((n, 1)), # 常数项
            np.sin(2 * np.pi * k * t_grid_local / cycle_length),
            np.cos(2 * np.pi * k * t_grid_local / cycle_length)
        ])
        
        try:
            # coef[0] 是常数项 (残差的均值)，其余是傅里叶系数
            coef, _, _, _ = np.linalg.lstsq(X_fourier, y_detrended, rcond=None)
        except np.linalg.LinAlgError as e:
            print(f"傅里叶拟合失败: {e}")
            return None, None, None
            
        # **关键修改点 5: 预测下一个时间点的傅里叶项**
        t_future_local = np.array([len(t_window)]) # 窗口时间轴上的下一个点 (即 window_size)
        X_future_fourier = np.hstack([
            np.ones((1, 1)),
            np.sin(2 * np.pi * k * t_future_local[:, np.newaxis] / cycle_length),
            np.cos(2 * np.pi * k * t_future_local[:, np.newaxis] / cycle_length)
        ])
        
        # 傅里叶预测值 (残差)
        fourier_residual_future = X_future_fourier @ coef
        
        # **关键修改点 6: 趋势项的回归**
        # 预测点的全局时间轴索引
        t_predict_global = t_last_global + 1 
        
        if trend_added:
            # 趋势项应该平滑地从当前点延续，使用局部趋势来修正全局趋势的预测值
            # 趋势预测 = 局部趋势在 t_predict_global 上的值
            # 这样预测点就能平滑地衔接当前窗口的最后一个点
            trend_predict_value = local_trend_func(t_predict_global)
            
            # 也可以尝试使用混合趋势，但为了平滑衔接，通常直接用拟合窗口的趋势延续：
            # trend_predict_value = (global_trend_weight * global_trend_func(t_predict_global) +
            #                       (1 - global_trend_weight) * local_trend_func(t_predict_global))
        else:
            trend_predict_value = 0.0
            
        # 最终预测值 = 趋势预测值 + 傅里叶残差预测值
        y_future = trend_predict_value + fourier_residual_future[0]
        
        # 限制每日波动，防止陡变，确保平滑衔接
        if i == 0:
            prev_value = series.iloc[-1]
        else:
            prev_value = forecast_results[-1]
            
        y_future_clipped = np.clip(
            y_future,
            prev_value * (1 - max_daily_volatility),
            prev_value * (1 + max_daily_volatility)
        )
        
        forecast_results.append(y_future_clipped)
        
        # **关键修改点 7: 更新 series 用于下一次滚动**
        # 将预测值加入 current_series，并用 future_dates 的日期作为索引
        current_series = pd.concat([
            current_series,
            pd.Series([y_future_clipped], index=[future_dates[i]])
        ])
        
    forecast = pd.Series(forecast_results, index=future_dates)
    
    # 趋势方向分析
    # 使用第一个预测点和最后一个预测点来判断方向
    trend_direction = "positive" if forecast.iloc[-1] > forecast.iloc[0] else "negative"
    
    return future_dates, forecast, trend_direction 

def get_df(code):
    df=ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    return df


def fit_cycles_and_get_weights(
    code: str, 
    start_date: Union[str, pd.Timestamp], 
    end_date: Union[str, pd.Timestamp], 
    n_cycles: int = 2,  
    min_cycle: float = 5.0, # 最小周期稍微放大，减少高频噪声干扰
    fit_intercept: bool = True # 是否包含截距项（基线）
) -> dict:
    """
    基于 FFT 检测到的最佳周期，通过线性回归拟合每个周期的 sin/cos 权重。

    参数:
    - code: 基金代码（str）。
    - start_date: 起始日期（str 或 pd.Timestamp）。
    - end_date: 结束日期（str 或 pd.Timestamp）。
    - n_cycles: 希望拟合的主要周期数量。
    - min_cycle: 最小周期长度，用于过滤高频噪声。
    - fit_intercept: 线性回归是否包含截距项（常数项）。

    返回:
    - 包含周期、sin 权重、cos 权重的字典。
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return {}
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df.set_index('净值日期', inplace=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    df = df.loc[start:end]
    if df.empty:
        print(f"指定日期范围内没有数据: {start} - {end}")
        return {}
    top_cycles = find_top_n_cycles(code, start_date, end_date, n_cycles=n_cycles, min_cycle=min_cycle)
    if not top_cycles:
        print("未检测到有效周期，无法拟合。")
        return {}
    y = df['累计净值'].values
    t = np.arange(len(y)) 
    X_features = []
    results = {'cycle': [], 'sin_weight': [], 'cos_weight': []}
    for cycle in top_cycles:
        omega = 2 * np.pi / cycle
        sin_term = np.sin(omega * t)
        X_features.append(sin_term)
        cos_term = np.cos(omega * t)
        X_features.append(cos_term)
        results['cycle'].extend([cycle, cycle]) # 记录两次，分别对应 sin/cos
    X = np.column_stack(X_features)
    model = LinearRegression(fit_intercept=fit_intercept)
    model.fit(X, y)
    weights = model.coef_
    final_weights = {}
    if fit_intercept:
        final_weights['intercept'] = model.intercept_
    for i, cycle in enumerate(top_cycles):
        sin_weight = weights[2 * i]
        cos_weight = weights[2 * i + 1]
        final_weights[f'{cycle:.2f}_days'] = {
            'sin_weight': np.round(sin_weight, 5),
            'cos_weight': np.round(cos_weight, 5)
        }
    print(f"基金 {code}，基于 {n_cycles} 个周期项的拟合权重结果:")
    return final_weights




def fourier_worm_rolling_classic(
    df_series: pd.DataFrame,
    start_date: Optional[Union[str, pd.Timestamp]] = None,
    end_date: Optional[Union[str, pd.Timestamp]] = None,
    sampling_frequency: str = 'D',
    cycles: Union[float, List[float]] = 287,  # 傅里叶分析的周期长度，可以是一个列表或单个值
    window_size: int = 120,  # 拟合周期项的窗口大小
    prediction_steps: int = 10,
    add_trend: bool = True  # 是否添加线性趋势项
) -> Tuple[pd.DatetimeIndex, pd.Series, str]:
    """
    基于傅里叶级数的经典滚动预测函数。
    参数:
        df_series (pd.DataFrame): 包含 '净值日期' 和 '累计净值' 的时间序列数据框。
        start_date, end_date: 数据筛选的开始和结束日期。
        sampling_frequency (str): 数据重采样的频率 ('D', 'W', 'M' 等)。
        cycles (Union[float, List[float]]): 用于傅里叶拟合的周期长度（时间步长），如 [60, 180]。
        window_size (int): 每次拟合时使用的历史数据窗口大小。
        prediction_steps (int): 预测未来的步数。
        add_trend (bool): 是否在拟合中添加线性趋势。
    返回:
        Tuple[pd.DatetimeIndex, pd.Series, str]: 预测日期、预测值序列、预测方向 ("positive" 或 "negative")。
    """
    if df_series is None or df_series.empty:
        print("输入数据为空。")
        return None, None, None
    df = df_series.copy()
    df.rename(columns={'净值日期': 'Date', '累计净值': 'Value'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df.dropna(subset=['Value'], inplace=True)
    if start_date is not None or end_date is not None:
        start = pd.to_datetime(start_date) if start_date else df.index.min()
        end = pd.to_datetime(end_date) if end_date else df.index.max()
        df = df.loc[start:end]
    df = df.resample(sampling_frequency).last().ffill()
    df.dropna(subset=['Value'], inplace=True)

    # 动态调整窗口大小，确保数据点足够
    if len(df) < window_size:
        print(f"有效数据点过少 ({len(df)})，自动调整窗口大小。")
        window_size = len(df)  # 动态调整窗口大小为数据点数量

    if df.empty or len(df) < window_size:
        print(f"有效数据点过少 ({len(df)})，请确保数据长度大于窗口大小 ({window_size})。")
        return None, None, None
    
    series = df['Value']
    if not isinstance(cycles, list):
        cycles_list = [cycles]
    else:
        cycles_list = cycles
    current_series = series.copy()
    start_pred_date = series.index[-1] + pd.Timedelta(seconds=1)
    future_dates = pd.date_range(start=start_pred_date, periods=prediction_steps, freq=sampling_frequency)
    forecast_results = []
    
    for i in range(prediction_steps):
        window_data = current_series[-window_size:]
        n = len(window_data)
        t_window = np.arange(n)
        if add_trend:
            coeffs_trend = np.polyfit(t_window, window_data.values, 1)
            trend_func = lambda t_vals: np.polyval(coeffs_trend, t_vals)
            y_detrended = window_data.values - trend_func(t_window)
        elif add_trend == False:
            y_detrended = window_data.values
            trend_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)

        X_fourier = np.ones((n, 1))  # 常数项
        for cycle_len in cycles_list:
            cycle_len = max(1.0, float(cycle_len))
            X_fourier = np.hstack([
                X_fourier,
                np.sin(2 * np.pi * t_window[:, np.newaxis] / cycle_len),
                np.cos(2 * np.pi * t_window[:, np.newaxis] / cycle_len)
            ])

        try:
            coef, _, _, _ = np.linalg.lstsq(X_fourier, y_detrended, rcond=None)
        except np.linalg.LinAlgError as e:
            print(f"傅里叶拟合失败: {e}")
            return None, None, None
        
        t_predict_local = np.array([n])
        trend_predict_value = trend_func(t_predict_local)[0]
        X_predict_fourier = np.ones((1, 1))
        for cycle_len in cycles_list:
            cycle_len = max(1.0, float(cycle_len))
            X_predict_fourier = np.hstack([
                X_predict_fourier,
                np.sin(2 * np.pi * t_predict_local[:, np.newaxis] / cycle_len),
                np.cos(2 * np.pi * t_predict_local[:, np.newaxis] / cycle_len)
            ])

        fourier_residual_future = X_predict_fourier @ coef
        y_future = trend_predict_value + fourier_residual_future[0]
        forecast_results.append(y_future)
        current_series = pd.concat([
            current_series,
            pd.Series([y_future], index=[future_dates[i]])
        ])
    
    forecast = pd.Series(forecast_results, index=future_dates)
    trend_direction = "positive" if forecast.iloc[-1] > forecast.iloc[0] else "negative"
    return forecast






def fourier_worm_normal(
    code: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    sampling_frequency: str,
    order: int,
    prediction_steps: int = 1,
    trend_added: bool = True,
    max_daily_volatility: float = 0.02,
    cycle_length: int = 30
) -> Tuple[pd.DatetimeIndex, pd.Series]:
    """
    使用傅里叶分析进行直接外推预测，基于整个数据集生成基金净值预测。

    Parameters:
    -----------
    code : str
        基金代码。
    start_date : pd.Timestamp
        数据开始日期。
    end_date : pd.Timestamp
        数据结束日期。
    sampling_frequency : str
        重采样频率（如 'D' 表示每日，'W' 表示每周）。
    order : int
        傅里叶级数的阶数（正弦和余弦项的数量）。
    prediction_steps : int
        预测的步数，默认为 1。
    trend_added : bool
        是否保留趋势，默认为 True。
    max_daily_volatility : float
        单日最大波动率（绝对值），默认为 0.02（2%）。
    cycle_length : Optional[float]
        傅里叶周期长度（天），默认为 None（使用数据长度）。

    Returns:
    --------
    Tuple[pd.DatetimeIndex, pd.Series]
        预测日期和对应的预测净值序列。如果失败，返回 (None, None).
    """
    # 验证 sampling_frequency
    valid_frequencies = ['D', 'W', 'M', 'Q', 'Y']
    if sampling_frequency not in valid_frequencies:
        print(f"无效的重采样频率: {sampling_frequency}。支持的频率: {valid_frequencies}")
        return None, None

    # 获取数据
    try:
        df: pd.DataFrame = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return None, None

    # 数据预处理
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df.set_index('净值日期', inplace=True)
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=['累计净值'], inplace=True)

    # 重采样并保留最后真实值
    try:
        df = df.loc[start_date:end_date]
        df = df.resample(sampling_frequency).last().ffill()
        df.dropna(subset=['累计净值'], inplace=True)
    except Exception as e:
        print(f"数据重采样或切片失败: {e}")
        return None, None

    if df.empty:
        print("数据为空，请检查日期范围或数据源。")
        return None, None

    # 获取时间序列
    series = df['累计净值']
    t = np.arange(len(series))

    # 设置 cycle_length
    if cycle_length is None:
        cycle_length = len(series)  # 默认使用整个数据长度
    cycle_length = max(5, cycle_length)

    # 计算趋势
    if trend_added:
        coeffs = np.polyfit(t, series.values, 1)
        trend_last = np.polyval(coeffs, t[-1])
        offset = series.iloc[-1] - trend_last
        trend_predict_func = lambda t_vals: np.polyval(coeffs, t_vals) + offset
        y_detrended = series.values - trend_predict_func(t)
        print(f"趋势斜率: {coeffs[0]}, 偏移校正: {offset}")
    else:
        y_detrended = series.values
        trend_predict_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)

    n = len(y_detrended)
    t_grid = t[:, np.newaxis]
    k = np.arange(1, order + 1)
    X = np.hstack([
        np.ones((n, 1)),
        np.sin(2 * np.pi * k * t_grid / cycle_length),
        np.cos(2 * np.pi * k * t_grid / cycle_length)
    ])

    try:
        coef, _, _, _ = np.linalg.lstsq(X, y_detrended, rcond=None)
    except np.linalg.LinAlgError as e:
        print(f"傅里叶拟合失败: {e}")
        return None, None

    # 设置预测日期
    future_dates = pd.date_range(start=end_date, periods=prediction_steps, freq=sampling_frequency)
    t_future = np.arange(len(t), len(t) + prediction_steps)
    X_future = np.hstack([
        np.ones((len(t_future), 1)),
        np.sin(2 * np.pi * k * t_future[:, np.newaxis] / cycle_length),
        np.cos(2 * np.pi * k * t_future[:, np.newaxis] / cycle_length)
    ])
    y_future = X_future @ coef + trend_predict_func(t_future)

    # 控制单日波动率
    last_value = series.iloc[-1]  # 2025-08-30 净值（约1.98）
    y_future[0] = np.clip(y_future[0], last_value * (1 - max_daily_volatility), last_value * (1 + max_daily_volatility))
    for i in range(1, len(y_future)):
        y_future[i] = np.clip(
            y_future[i],
            y_future[i-1] * (1 - max_daily_volatility),
            y_future[i-1] * (1 + max_daily_volatility)
        )

    forecast = pd.Series(y_future, index=future_dates)
    return future_dates, forecast


def get_interpolated_fund_data(code: str) -> Optional[pd.DataFrame]:
    """获取基金的累计净值数据，进行清洗、去重、排序，并按日插值。"""
    try:
        df: pd.DataFrame = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return None
    required_cols = ['净值日期', '累计净值']
    if not all(col in df.columns for col in required_cols):
        print(f"基金 {code} 数据缺少必要字段: {required_cols}")
        return None
    df['净值日期'] = pd.to_datetime(df['净值日期'], errors='coerce')
    df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
    df.dropna(subset=required_cols, inplace=True)
    df.drop_duplicates(subset=['净值日期'], keep='last', inplace=True)
    df.set_index('净值日期', inplace=True)
    df.sort_index(inplace=True)
    if df.empty:
        return None
    start_date = df.index.min()
    end_date = df.index.max()
    all_dates_index = pd.date_range(start=start_date, end=end_date, freq='D')
    df_interp = df.reindex(all_dates_index)
    df_interp['累计净值'] = df_interp['累计净值'].interpolate(method='linear')
    if df_interp['累计净值'].isnull().any():
        df_interp['累计净值'].ffill(inplace=True)
        if df_interp['累计净值'].isnull().any():
             df_interp.dropna(subset=['累计净值'], inplace=True)
             if df_interp.empty:
                 return None
    return df_interp.reset_index().rename(columns={'index': '净值日期'})


def real_data_direction(code: str, date: str, expected_steps: int = 10, df: pd.DataFrame = None) -> Optional[str]:
    """根据基金代码和指定日期，判断指定天数后（基于每日插值数据）的净值趋势。"""
    try:
        start_date = pd.Timestamp(date).normalize()
    except Exception as e:
        print(f"日期格式错误: {date} - {e}")
        return None
    if df is None:
        df = get_interpolated_fund_data(code)
        if df is None:
            return None
    if df.index.name != '净值日期':
        if '净值日期' in df.columns:
            df_working = df.set_index('净值日期').sort_index()
        else:
            return None
    else:
        df_working = df.sort_index()
    end_date = start_date + pd.Timedelta(days=expected_steps)
    if start_date not in df_working.index:
        return None
    if end_date not in df_working.index or end_date > df_working.index[-1]:
        return None
    try:
        start_value = df_working.loc[start_date, '累计净值']
        end_value = df_working.loc[end_date, '累计净值']
    except KeyError:
         return None
    if end_value > start_value:
        return "positive"
    elif end_value < start_value:
        return "negative"
    else:
        return "neutral"

def get_df_by_path(path):
    df = pd.read_csv(path)
    return df


def fourier_summary(weights, t):
    intercept = weights['intercept']
    result = intercept  # 截距项
    for period, weight_dict in weights.items():
        if period == 'intercept':  # 跳过截距项
            continue
        period_days = float(period.split('.')[0])  # 获取周期的天数，例如243.00_days -> 243.00
        sin_weight = weight_dict['sin_weight']
        cos_weight = weight_dict['cos_weight']
        result += sin_weight * np.sin(2 * np.pi * t / period_days) + cos_weight * np.cos(2 * np.pi * t / period_days)
    return result

class PlotWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.initUI()
    def initUI(self):
        layout = QVBoxLayout(self)
        figure, ax = plt.subplots(figsize=(8, 6))
        ax.plot(self.data['时间'], self.data['净值'], label='净值')
        ax.set_xlabel('时间')
        ax.set_ylabel('净值')
        ax.set_title('时间与净值变化图')
        ax.legend()
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        label = QLabel("基金净值走势图", self)
        layout.addWidget(label)
        self.setLayout(layout)



def is_low_and_go_up(code, df=None, window_days=120):
    """
    判断当前基金在 window_days 内所处位置，并推测是否有上涨趋势。
    参数:
        code: 基金代码
        df: 获取的基金数据，包含 '净值日期' 和 '累计净值' 的 DataFrame，默认从 akshare 获取
        window_days: 用来计算位置的窗口大小
    返回:
        str: 'Low'（低位），'Medium'（中位），'High'（高位），'Up'（上涨趋势）
    """
    if df is None:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    
    # 设置日期列为索引
    df = df.set_index('净值日期')
    df = df[-window_days:]
    
    # 如果数据长度不足，返回提示
    if len(df) < window_days:
        return "Data insufficient"
    
    # 使用时间序列数据进行线性回归
    df['Time'] = np.arange(len(df))  # 以时间戳为自变量（从 0 开始递增）
    X = df['Time'].values.reshape(-1, 1)  # 自变量：时间
    y = df['累计净值'].values  # 因变量：基金净值
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 预测的回归线
    df['Fitted'] = model.predict(X)
    
    # 计算每个数据点与回归线的距离
    df['Distance'] = np.abs(df['累计净值'] - df['Fitted'])
    
    # 计算标准差（波动性）
    std_dev = df['累计净值'].std()
    
    # 设定低位、中位和高位的更动态的边界
    low_threshold = df['Fitted'].iloc[-1] - std_dev * 0.5  # 回归线下方半个标准差
    high_threshold = df['Fitted'].iloc[-1] + std_dev * 0.5  # 回归线上方半个标准差
    
    current_value = df['累计净值'].iloc[-1]  # 当前基金净值
    fitted_value = df['Fitted'].iloc[-1]  # 当前回归线值
    
    # 判断当前位置
    if current_value <= low_threshold:
        position = 'Low'
    elif current_value >= high_threshold:
        position = 'High'
    else:
        position = 'Medium'
    
    # 判断趋势：回归线的斜率决定了趋势
    trend = "Up" if model.coef_[0] > 0 else "Down"
    
    # 如果当前在低位且趋势向上，认为是“低位且有上涨趋势”
    if position == 'Low' and trend == 'Up':
        return "Low and Up"
    
    return position







if __name__ == "__main__":
    # result =year_rate_sliding('000309')
    # print(result)
    # risk=get_max_annualized_volatility('000216',get_df_by_path(r'A:\projects\money2\my_types\Qdii\000216.csv'),'2023-4-1',60)
    # print(risk)
    # rolling_prediction = fourier_worm_rolling('005698', '2025-4-10', '2025-10-1', sampling_frequency='D', order=5, window_size=40, prediction_steps=10, trend_added=True)
    # print(rolling_prediction)
    # best_cycle=find_top_n_cycles(code='000216', start_date='2024-9-29', end_date='2025-9-28')
    # print(best_cycle)
    # cycles=find_top_n_cycles(code='000216', start_date='2024-4-01', end_date='2025-10-10', n_cycles=1, min_cycle=5.0)
    # optput=fourier_worm_rolling_classic(get_df('000216'), '2024-04-01', '2025-10-10', sampling_frequency='D', cycles=cycles, window_size=5, prediction_steps=10, add_trend=False)
    # print(optput)
    # correct_rate=real_data_direction('005698', '2025-04-24', 10)
    # print(correct_rate)
    # print(get_interpolated_fund_data('005698'))
    # prediction=fourier_worm_normal('005698', '2024-08-01', '2025-08-28', sampling_frequency='D', order=3, cycle_length=None, prediction_steps=10, trend_added=True,cycle_length=80)
    # print(prediction)
    # weights=fit_cycles_and_get_weights(code='016496', start_date='2024-9-29', end_date='2025-9-28', n_cycles=3, min_cycle=5.0, fit_intercept=True)
    # print(weights)
    # start_date = date(2024, 9, 29)
    # print(start_date)
    # dates=[]
    # values=[]
    # for t in range(0,360):
    #     delta = pd.Timedelta(days=t)
    #     newdate=start_date+delta
    #     dates.append(newdate)
    #     result=fourier_summary(weights=weights, t=t)
    #     values.append(result)
    #     print(f'{result}日期:{newdate}')
    # app = QApplication(sys.argv)
    # df=ak.fund_open_fund_info_em(symbol="000216", indicator="累计净值走势")
    # data = pd.DataFrame({
    #     '时间': dates,
    #     '净值': values
    # })
    # window = PlotWidget(data)
    # window.setWindowTitle('净值走势图')
    # window.resize(800, 600)
    # window.show()

    # sys.exit(app.exec_())

    # max_volatility = get_max_annualized_volatility('000216', 60)
    # print(max_volatility)
    # position=is_low_and_go_up(code='501005',df=None,window_days=100)
    # print(position)
    output=yearly_return_since_start(code='000216',df=get_df_by_path(r'A:\projects\money2\my_types\Qdii\000216.csv'))
    print(output)

    