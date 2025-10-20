"""最终决策层,拿到一支数据后，计算其未来的走向并做正确率计算，给出决策"""
from calculate_data import (get_interpolated_fund_data, fourier_worm_rolling, 
                            real_data_direction,fourier_worm_rolling_classic,
                            linear_regression_sliding_window,get_df,find_top_n_cycles, year_rate_sliding,yearly_return_since_start
                            ,how_long_since_start,get_annualized_volatility_for_period)
import pandas as pd
import akshare as ak
from sklearn.linear_model import LinearRegression
from datetime import date

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


class decison_maker:
    """决策类，封装各种决策方法"""
    def __init__(self, fund_code,path,df):
        self.fund_code=fund_code
        self.today=date.today().strftime('%Y-%m-%d')
        self.ayear_ago_date=pd.to_datetime(self.today)-pd.Timedelta(days=365)
        self.ayear_ago_date=self.ayear_ago_date.strftime('%Y-%m-%d')
        self.df=df.copy() if df is not None else pd.DataFrame()
        if self.fund_code and self.df.empty:
            self.df=ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
        if path and self.df.empty and not fund_code:
            self.df=pd.read_csv(path)
        self.yearly_return_since_start=yearly_return_since_start(self.fund_code,self.df)
        self.max_annualized_volatility,_=get_annualized_volatility_for_period(self.fund_code,self.df,period_days=365)
        self.sharp_constant = self.yearly_return_since_start / self.max_annualized_volatility if self.max_annualized_volatility != 0 else 0
        self.total_days=how_long_since_start(self.fund_code,self.df)

    def self_check(self,min_year_rate=0.08,sharp_ratio_threshold=None):
        """检查这是不是一支合格的基金"""
        if self.yearly_return_since_start<min_year_rate:
            print(f"基金 {self.fund_code} 成立以来年化收益率为 {self.yearly_return_since_start:.2%}，低于{min_year_rate:.2%}，不合格。")
            return False
        if self.sharp_constant<sharp_ratio_threshold:
            print(f"基金 {self.fund_code} 夏普比率为 {self.sharp_constant:.2f}，低于{sharp_ratio_threshold}，不合格。")
            return False
        return True

    def caculate_year_rate_sliding(self):
        result=year_rate_sliding(self.fund_code,self.df,base_date=self.ayear_ago_date,window_size_days=20,step_size_days=2)
        print(result)
    

    def is_instant_bounce(self,window_size=None):
        """多模态针对下降趋势的基金，在近几个交易日检查是否有回调，触底反弹的情况"""
        func_str,yearly_return_index,slope=linear_regression_sliding_window(code=self.fund_code,df=self.df,window_size=window_size)
        if slope<0:
            try:
                worker_date=self.df['净值日期'].max()
                last_day_data = self.df[self.df['净值日期'] == worker_date]
                yesterday_date = worker_date - pd.Timedelta(days=1)
                yesterday_data = self.df[self.df['净值日期'] == yesterday_date]
                if not last_day_data.empty and not yesterday_data.empty:
                    latest_day_value = last_day_data['累计净值'].values[0]
                    yesterday_value = yesterday_data['累计净值'].values[0]
                    if latest_day_value > yesterday_value*1.001:  # 假设反弹阈值为0.1%
                        print(f"基金 {self.fund_code} 在 {worker_date.strftime('%Y-%m-%d')} 出现触底反弹，建议关注。")
                        return True
                    else:
                        print(f"基金 {self.fund_code} 在 {worker_date.strftime('%Y-%m-%d')} 未出现触底反弹。")
                        return False
                else:
                    print(f"无法获取基金 {self.fund_code} 的最近两天数据，无法判断是否触底反弹。")
                    return
            except Exception as e:
                print(f"试图检查是否触底反弹失败: {e}")
                return
        else:
            print(f"基金 {self.fund_code} 处于上升趋势，暂时不考虑反弹。")

    def evaluate_invested():
        """评估当前持有的基金持续关注"""
        pass
if __name__=="__main__":
    # get_correct_rate(fund_code = '000216',obeserve_start_date='2025-08-01',observe_end_date='2025-09-20',expected_steps=10)
    # result=fourier_predict(code="000216",end_date='2025-10-10',window_size=10,prediction_steps=10,add_trend=True)
    instance=decison_maker(fund_code="000216",path=r'A:\projects\money2\my_types\Qdii\000216.csv',df=None)
    print(instance.max_annualized_volatility)
    result=instance.is_instant_bounce(window_size=10)
    # instance.caculate_year_rate_sliding()



