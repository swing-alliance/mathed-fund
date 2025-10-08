"""计算层"""
import os
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import statsmodels.api as sm
from numpy.polynomial.polynomial import Polynomial
from typing import Optional, Tuple
path=os.path.join(os.getcwd(),'found')

def readcsv(path):
    df = pd.read_csv(path)
    return df


# fund_info_df = ak.fund_individual_basic_info_xq(symbol="000309")，返回基金信息
# df_new = ak.fund_open_fund_info_em(symbol="000216", indicator="累计净值走势")，返回累计净值走势

#年化比率

#滑动窗口年化比率
def year_rate_sliding(code, window_size_days=540, step_size_days=30):
    """滑动窗口年化，反应大方向的趋势，具有延后性，不够敏感"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    except Exception as e:
        print(f"获取基金 {code} 数据失败: {e}")
        return None, None
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
        end_date = end_date - pd.Timedelta(days=step_size_days)
    return annualized_returns, window_dates


#夏普比率(暂时不实现)
# def sharp_ratio(annualized_returns):
#     return np.mean(annualized_returns) / np.std(annualized_returns)

#最高年化波动
def get_max_annualized_volatility(code: str, window_size: int) -> tuple[float, pd.Timestamp]:
    """
    计算并返回基金在指定滑动天数内的最高年化波动率。
    参数:
    - code (str): 基金代码，例如 '001211'。
    - window_size (int): 滑动窗口天数，例如 60。
    返回:
    - tuple[float, pd.Timestamp]: 一个元组，包含最高年化波动率和其发生的日期。
                                  如果数据获取失败，则返回 (None, None)。
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df.set_index('净值日期', inplace=True)

        df['累计净值'] = pd.to_numeric(df['累计净值'], errors='coerce')
        df.dropna(subset=['累计净值'], inplace=True)

    except Exception as e:
        print(f"获取基金 {code} 数据失败：{e}")
        return None, None

    # 计算每日百分比收益率
    daily_returns = df['累计净值'].pct_change().dropna()
    
    # 使用滑动窗口计算每日收益率的标准差
    daily_volatility = daily_returns.rolling(window=window_size).std()
    
    # 将标准差年化 (乘以 sqrt(252))
    annualized_volatility = daily_volatility * np.sqrt(252)
    
    # 找到最高年化波动率及其对应的日期
    if not annualized_volatility.empty:
        max_volatility = annualized_volatility.max()
        max_date = annualized_volatility.idxmax()
        return max_volatility, max_date
    else:
        print("无法计算波动率，数据不足或窗口大小过大。")
        return None, None


#最大回撤率

#最大回撤天数

def fourier_worm_rolling(
    code: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    sampling_frequency: str,
    order: int,
    df_row: pd.DataFrame =None,
    window_size: Optional[int] = None,
    prediction_steps: int = 10,  # Adjusted to ensure 10 days for trend analysis
    trend_added: bool = True,
    max_daily_volatility: float = 0.02,
    global_trend_weight: float = 0.2,
    cycle_length: Optional[float] = 30
) -> Tuple[pd.DatetimeIndex, pd.Series, str]:
    # 验证 sampling_frequency
    valid_frequencies = ['D', 'W', 'M', 'Q', 'Y']
    df = None
    if sampling_frequency not in valid_frequencies:
        print(f"无效的重采样频率: {sampling_frequency}。支持的频率: {valid_frequencies}")
        return None, None, None
    # 转换为 pd.Timestamp（如果传入字符串）
    try:
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
    except Exception as e:
        print(f"日期转换失败: {e}")
        return None, None, None
    # 获取数据
    if df_row is not None:
        df = df_row.copy()

    if df_row is None:
        try:
            df: pd.DataFrame = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
        except Exception as e:
            print(f"获取基金 {code} 数据失败: {e}")
            return None, None, None
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
    # 获取时间序列
    series = df['累计净值']
    t = np.arange(len(series))
    # 设置默认 window_size
    if window_size is None:
        window_size = max(30, len(series) // 5)
    if window_size <= 0 or window_size > len(series):
        print(f"无效的窗口大小: {window_size}。数据长度为 {len(series)}。")
        return None, None, None
    # 设置 cycle_length
    if cycle_length is None:
        cycle_length = window_size
    cycle_length = max(5, min(cycle_length, window_size))  # 限制周期长度
    # 计算全局趋势
    if trend_added:
        coeffs_global = np.polyfit(t, series.values, 1)
        trend_last_global = np.polyval(coeffs_global, t[-1])
        offset_global = series.iloc[-1] - trend_last_global
        global_trend_func = lambda t_vals: np.polyval(coeffs_global, t_vals) + offset_global
        print(f"全局趋势斜率: {coeffs_global[0]}, 偏移校正: {offset_global}")
    else:
        global_trend_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)
    # 设置预测日期，从 end_date 的下一天开始
    future_dates = pd.date_range(start=end_date + pd.Timedelta(days=1), periods=prediction_steps, freq=sampling_frequency)
    forecast_results = []
    # 获取最后一天的实际净值
    last_value = series.iloc[-1]
    if len(series) < window_size:
        print(f"数据长度 {len(series)} 小于窗口大小 {window_size}，无法进行滚动预测。")
        return None, None, None
    current_series = series.copy()
    current_t = t.copy()
    for i in range(prediction_steps):
        current_window = current_series[-window_size:]
        t_window = np.arange(len(current_window))
        if trend_added:
            coeffs_local = np.polyfit(t_window, current_window.values, 1)
            trend_last_local = np.polyval(coeffs_local, t_window[-1])
            offset_local = current_window.iloc[-1] - trend_last_local
            local_trend_func = lambda t_vals: np.polyval(coeffs_local, t_vals) + offset_local
            trend_predict_func = lambda t_vals: (
                global_trend_weight * global_trend_func(t_vals + [t[-1] - t_window[-1]]) +
                (1 - global_trend_weight) * local_trend_func(t_vals)
            )
            y_detrended = current_window.values - trend_predict_func(t_window)
        else:
            y_detrended = current_window.values
            trend_predict_func = lambda t_vals: np.zeros_like(t_vals, dtype=float)

        n = len(y_detrended)
        k = np.arange(1, order + 1)
        t_grid = t_window[:, np.newaxis]
        X = np.hstack([
            np.ones((n, 1)),
            np.sin(2 * np.pi * k * t_grid / cycle_length),
            np.cos(2 * np.pi * k * t_grid / cycle_length)
        ])
        try:
            coef, _, _, _ = np.linalg.lstsq(X, y_detrended, rcond=None)
        except np.linalg.LinAlgError as e:
            print(f"傅里叶拟合失败: {e}")
            return None, None, None
        t_future = np.array([len(t_window)])
        X_future = np.hstack([
            np.ones((1, 1)),
            np.sin(2 * np.pi * k * t_future[:, np.newaxis] / cycle_length),
            np.cos(2 * np.pi * k * t_future[:, np.newaxis] / cycle_length)
        ])
        y_future = X_future @ coef + trend_predict_func([len(t_window)])
        # 控制单日波动率
        if i == 0:
            prev_value = last_value
        else:
            prev_value = forecast_results[-1]
        y_future = np.clip(
            y_future,
            prev_value * (1 - max_daily_volatility),
            prev_value * (1 + max_daily_volatility)
        )
        forecast_results.append(y_future[0])
        current_series = pd.concat([
            current_series,
            pd.Series([y_future[0]], index=[future_dates[i]])
        ])
        current_t = np.append(current_t, t_future[0])
    forecast = pd.Series(forecast_results, index=future_dates)
    # 分析10天趋势方向
    trend_direction = "positive" if forecast.iloc[-1] > forecast.iloc[0] else "negative"
    return trend_direction  #,future_dates, forecast


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








if __name__ == "__main__":
    # result =year_rate_sliding('000309')
    # print(result)
    # risk=get_max_annualized_volatility('000216',60)
    # print(risk)
    # rolling_prediction = fourier_worm_rolling('005698', '2024-10-25', '2025-04-24', sampling_frequency='D', order=5, window_size=40, prediction_steps=10, trend_added=True)
    # print(rolling_prediction)
    # correct_rate=real_data_direction('005698', '2025-04-24', 10)
    # print(correct_rate)
    # print(get_interpolated_fund_data('005698'))
    # prediction=fourier_worm_normal('005698', '2024-08-01', '2025-08-28', sampling_frequency='D', order=3, cycle_length=None, prediction_steps=10, trend_added=True,cycle_length=80)
    # print(prediction)
    # max_volatility = get_max_annualized_volatility('000216', 60)
    # print(max_volatility)
    pass