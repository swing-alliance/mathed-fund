"""最终决策层,拿到一支数据后，计算其未来的走向并做正确率计算，给出决策"""
from calculate_data import get_interpolated_fund_data, fourier_worm_rolling, real_data_direction,fourier_worm_rolling_classic,get_df,find_top_n_cycles
import pandas as pd
import akshare as ak
from sklearn.linear_model import LinearRegression

def get_correct_rate(fund_code:str = '005698',obeserve_start_date:str='2025-06-24',observe_end_date:str='2025-09-06',expected_steps=20):
    """获取基金趋势并计算正确率,基于真实数据的校验回测。"""
    errordays=[]
    df = get_interpolated_fund_data(fund_code)
    row_df= ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
    if df is None:
        print("获取基金数据失败，程序终止。")
        return
    df_indexed = df.set_index('净值日期')
    # 示例日期范围
    dates = pd.date_range(start=obeserve_start_date, end=observe_end_date, freq='D')
    # 打印标题
    print(f"--- 基金 {fund_code} 10日趋势 (start 至 end) ---")
    time=0
    right=0
    df=get_df('000216')
    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        real_rate = real_data_direction(code=fund_code, date=date_str, expected_steps=expected_steps, df=df_indexed)
        fourier_rate=fourier_worm_rolling_classic(df, '2024-08-01', '2025-9-29', sampling_frequency='D', cycles=184, window_size=180, prediction_steps=10, add_trend=True)
        time+=1
        if fourier_rate == real_rate:
            print(f"正确:{date_str}")
            right+=1
        else:
            print(f"错误:{date_str}")
            errordays.append(date_str)
    print(f"正确率为:{right/time}")
    print(f"错误日期为：{errordays}")


def fourier_predict(code, end_date, window_size, prediction_steps=10, add_trend=True):
    """基于傅里叶滑动窗口变换预测未来走势,实验性，不保证准确性。"""
    df = get_df(code)
    end_date = pd.to_datetime(end_date)
    window_size = int(window_size)
    cycles = find_top_n_cycles(code=code, start_date=end_date - pd.Timedelta(days=window_size), end_date=end_date, n_cycles=1, min_cycle=2.0)
    predict_result = fourier_worm_rolling_classic(
        df_series=df,
        start_date=end_date - pd.Timedelta(days=window_size),
        end_date=end_date,
        sampling_frequency='D',
        cycles=cycles,
        window_size=window_size,
        prediction_steps=prediction_steps,
        add_trend=add_trend
    )
    return predict_result






if __name__=="__main__":
    # get_correct_rate(fund_code = '000216',obeserve_start_date='2025-08-01',observe_end_date='2025-09-20',expected_steps=10)
    result=fourier_predict(code="000216",end_date='2025-10-10',window_size=10,prediction_steps=10,add_trend=True)
    print(result)