"""最终决策层,拿到一支数据后，计算其未来的走向并做正确率计算，给出决策"""
from calculate_data import get_interpolated_fund_data, fourier_worm_rolling, real_data_direction
import pandas as pd
import akshare as ak

def get_correct_rate(fund_code:str = '005698',obeserve_start_date:str='2025-06-24',observe_end_date:str='2025-09-06',expected_steps=20):
    """获取基金趋势并计算正确率。"""
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
    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        real_rate = real_data_direction(code=fund_code, date=date_str, expected_steps=expected_steps, df=df_indexed)
        fourier_rate=fourier_worm_rolling(code=fund_code, start_date="2024-07-06", end_date=date_str, sampling_frequency='D', order=3,df_row=row_df, window_size=4, prediction_steps=expected_steps, trend_added=True)
        time+=1

        if fourier_rate == real_rate:
            print(f"正确:{date_str}")
            right+=1
        else:
            print(f"错误:{date_str}")
            errordays.append(date_str)
    print(f"正确率为:{right/time}")
    print(f"错误日期为：{errordays}")

"""结果抖动不是bug,代表市场重大变化。"""
if __name__=="__main__":
    get_correct_rate(fund_code = '005698',obeserve_start_date='2025-01-06',observe_end_date='2025-06-20',expected_steps=10)