"""最终决策层,拿到一支数据后，计算其未来的走向并做正确率计算，给出决策"""
from calculate_data import (get_interpolated_fund_data, fourier_worm_rolling, 
                            real_data_direction,fourier_worm_rolling_classic,
                            linear_regression_sliding_window,get_df,find_top_n_cycles, year_rate_sliding,yearly_return_since_start
                            ,how_long_since_start,get_annualized_volatility_for_period,get_lowest_point_by_period,get_highest_point_by_period,short_term_daily_return)
import pandas as pd
import akshare as ak
from sklearn.linear_model import LinearRegression
from datetime import date,timedelta,datetime
import os
import json

transaction_confirmed_path=os.path.join(os.getcwd(),'track',"transaction_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'track',"transaction_onsubmit.json")

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
    """决策类，封装各种计算方法,计算一直基金的各类数据"""
    def __init__(self, fund_code,path,df):
        self.fund_code=fund_code
        self.today=date.today().strftime('%Y-%m-%d')
        self.ayear_ago_date=pd.to_datetime(self.today)-pd.Timedelta(days=365)
        self.ayear_ago_date=self.ayear_ago_date.strftime('%Y-%m-%d')
        self.df=df.copy() if df is not None else pd.DataFrame()
        self.path=path
        if self.fund_code and self.df.empty:
            self.df=ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
        if path and self.df.empty and not fund_code:
            self.df=pd.read_csv(path)
            self.fund_code=os.path.basename(path).split('.')[0]
        self.df['净值日期']=pd.to_datetime(self.df['净值日期'])
        self.newest_date=self.df['净值日期'].max().strftime('%Y-%m-%d')
        self.max_annualized_volatility,_=get_annualized_volatility_for_period(code=None,df=self.df,period_days=365)
        self.sharp_constant = self.year_rate_since_start_this() / self.max_annualized_volatility if self.max_annualized_volatility != 0 else 0
        self.total_days=how_long_since_start(self.fund_code,self.df)

    def year_rate_since_start_this(self,expected_interval_days=None):
        """计算成立以来的年化收益率"""
        if expected_interval_days is not None:
            return yearly_return_since_start(code=None,df=self.df,expected_interval_days=expected_interval_days)
        return yearly_return_since_start(code=None,df=self.df)


    def short_term_return(self,days=3):
        """计算短期收益率"""
        return short_term_daily_return(code=None,df=self.df,days=days)

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
        pass
    def get_risky_reward(self,yearly_return_since_start=0.012,max_annualized_volatility=0.4):
        """短期，高风险高回报"""
        if self.yearly_return_since_start>yearly_return_since_start and self.max_annualized_volatility>max_annualized_volatility:
            return True
        else:
            return False
        
    
    def get_long_term_return(self,days_since_start=1618):
        """长期回报,定投"""
        if self.yearly_return_since_start>0.2 and self.max_annualized_volatility<0.3 and self.total_days>days_since_start if days_since_start is not None else True:
            return True
        else:
            return False
        
    def get_low_point(self,max_annualized_volatility=0.4,days_since_start=1618):
        """超低点"""
        if self.yearly_return_since_start<0.001 and self.max_annualized_volatility>max_annualized_volatility and self.total_days>days_since_start if days_since_start is not None else True:
            return True
        else:
            return False
        
    def is_consider_lowpoint(self):
        """
        判断是否处于低点买入的考虑范围，基于严格的日期、回撤和波动率条件。
        """
        MINIMUM_DAYS_BETWEEN_PEAKS = 3  # 最低点必须在最高点之后至少 N 天
        DRAWDOWN_PERCENTAGE_THRESHOLD = 0.1  # 回撤百分比阈值 (5%)
        VOLATILITY_THRESHOLD = 0.28  # 年化波动率阈值 (28%)
        # 1. 获取过去40天的极值和日期
        # 假设 these are already calculated and stored in self.*
        self.lowest_point_in_period_value, self.lowest_point_date = get_lowest_point_by_period(self.df, period_days=40)
        self.highest_point_in_period_value, self.highest_point_date = get_highest_point_by_period(self.df, period_days=40)
        if self.df.empty:
            return False
        current_net_value = self.df['累计净值'].iloc[-1]
        current_annualized_volatility = self.max_annualized_volatility # 假设此属性存在
        time_difference = self.lowest_point_date - self.highest_point_date
        is_low_after_high = time_difference >= timedelta(days=MINIMUM_DAYS_BETWEEN_PEAKS)

        if not is_low_after_high:
            return False
        if self.highest_point_in_period_value <= 0:
            return False
        drawdown = (self.highest_point_in_period_value - current_net_value) / self.highest_point_in_period_value
        has_sufficient_drawdown = drawdown >= DRAWDOWN_PERCENTAGE_THRESHOLD
        if not has_sufficient_drawdown:
            return False
        has_high_volatility = current_annualized_volatility >= VOLATILITY_THRESHOLD
        if not has_high_volatility:
            return False
        is_current_net_value_the_low_point = (current_net_value == self.lowest_point_in_period_value)
        if is_low_after_high and has_sufficient_drawdown and has_high_volatility and is_current_net_value_the_low_point:
            return True
        return False

    def onedayprofitconclusion(self):
        """一天的收益结论"""
        lasttwo=self.df.tail(2)
        if len(lasttwo)<2:
            print("数据不足，无法计算一天收益结论。")
            return
        if lasttwo['累计净值'].iloc[-1]>lasttwo['累计净值'].iloc[-2]:
            return "up" ,lasttwo['净值日期'].iloc[-1].strftime('%Y-%m-%d')
        else:
            return "down",lasttwo['净值日期'].iloc[-1].strftime('%Y-%m-%d')

class buy_tracker:
    """追踪完整的交易过程"""
    def __init__(self, code=None, transaction_confirmed_path=transaction_confirmed_path, transaction_onsubmit_path=transaction_onsubmit_path):
      self.code = code
      self.transaction_confirmed_path = transaction_confirmed_path
      self.transaction_onsubmit_path = transaction_onsubmit_path
      self.today_date = date.today().strftime('%Y-%m-%d')
    def on_submit_transaction(self, buy_date, buy_price, sell_date, sell_nums,action):
        if action == "buy":
            try:
                self.buy_date =buy_date or self.today_date
                self.buy_price = buy_price
                if not os.path.exists(self.transaction_onsubmit_path):
                    with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=4)
                with open(self.transaction_onsubmit_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    if not file_content:
                            transactions = {}
                    else:
                        transactions = json.loads(file_content)
                if self.code not in transactions:
                    transactions[self.code] = []
                transaction_record = {
                "buy_date": self.buy_date,
                "buy_price": self.buy_price,
                "status":"unchecked"
                }
                transactions[self.code].append(transaction_record)
                with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                    json.dump(transactions, f, ensure_ascii=False, indent=4)
                print(f"买入记录已添加：{transaction_record}")
            except Exception as e:
                print(f"买入失败: {e}")
                return
        if action == "sell":
            try:
                self.sell_date =sell_date or self.today_date
                self.sell_nums = sell_nums
                with open(self.transaction_onsubmit_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    if not file_content:
                        transactions = {}
                    else:
                        transactions = json.loads(file_content)
                if self.code in transactions:
                    transaction_record = {
                        "sell_date": self.sell_date,
                        "sell_nums": self.sell_nums,
                        "status":"unchecked"
                    }
                    transactions[self.code].append(transaction_record)
                with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                    json.dump(transactions, f, ensure_ascii=False, indent=4)
                print(f"卖出记录已添加：{transactions[self.code][-1]}")
            except Exception as e:
                print(f"卖出失败: {e}")
                return

    def transaction_confirming(self, n=1):
        """交易确认，确认之前的交易"""
        try:
            with open(self.transaction_onsubmit_path, 'r', encoding='utf-8') as f:
                onsubmit_data = json.load(f)
                for code, group in onsubmit_data.items():
                    if code == self.code:
                        for transaction in group:
                            if transaction["status"]=="unchecked":
                                try:
                                    if "buy_price" in transaction:#买入
                                        buy_price = transaction["buy_price"]
                                        buy_date = transaction["buy_date"]
                                        confirm_result= get_next_trading_day(on_submit_date=buy_date, code=str(self.code),n=n)
                                        if confirm_result is None:
                                            print("无法获取下一个交易日")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                            print(f"下一个交易日：{next_trading_day}, 单位净值：{single_value}")
                                        record = {
                                            "buy_price": buy_price,
                                            "confirmed_date": next_trading_day,
                                            "single_value": single_value
                                        }
                                        with open(self.transaction_confirmed_path, 'r', encoding='utf-8') as f:
                                            confirmed_data = json.load(f)
                                        if code not in confirmed_data:
                                            confirmed_data[code] = []
                                            confirmed_data[code].append(record)
                                        else:
                                            confirmed_data[code].append(record)
                                        with open(self.transaction_confirmed_path, 'w', encoding='utf-8') as f:
                                            json.dump(confirmed_data, f, ensure_ascii=False, indent=4)
                                        transaction["status"] = "checked"
                                    elif "sell_nums" in transaction:#卖出
                                        sell_nums = transaction["sell_nums"]
                                        sell_date = transaction["sell_date"]
                                        confirm_result= get_next_trading_day(on_submit_date=sell_date, code=str(self.code),n=n)
                                        if confirm_result is None:
                                            print("无法获取下一个交易日")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                            print(f"下一个交易日：{next_trading_day}, 单位净值：{single_value}")
                                            total_nums=self.get_repository()
                                            if total_nums<sell_nums:
                                                print("仓库数量不足,不执行卖出操作")
                                                transaction["status"] = "Failed"
                                                continue
                                        record = {
                                            "sell_nums": sell_nums,
                                            "confirmed_date": next_trading_day,
                                            "single_value": single_value
                                        }
                                        with open(self.transaction_confirmed_path, 'r', encoding='utf-8') as f:
                                            confirmed_data = json.load(f)
                                        if code not in confirmed_data:
                                            confirmed_data[code] = []
                                            confirmed_data[code].append(record)
                                        else:
                                            confirmed_data[code].append(record)
                                        with open(self.transaction_confirmed_path, 'w', encoding='utf-8') as f:
                                            json.dump(confirmed_data, f, ensure_ascii=False, indent=4)
                                        transaction["status"] = "checked"
                                except Exception as e:
                                    print(f"最后买入确认失败: {e}")
                                    return
                            else:
                                continue
                with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                    json.dump(onsubmit_data, f, ensure_ascii=False, indent=4)
                
            print("交易确认成功！")
        except Exception as e:
            print(f"买入确认失败: {e}")
            return

    def get_repository(self):
        """获取仓库目前的数量"""
        try:
            with open(self.transaction_confirmed_path, 'r', encoding='utf-8') as f:
                confirmed_data = json.load(f)
                confirmed_nums=0
                for code, group in confirmed_data.items():
                    if code == self.code:
                        for transaction in group:
                            if "buy_price" in transaction:
                                buy_price = transaction["buy_price"]
                                single_value = transaction["single_value"]
                                confirmed_nums=confirmed_nums+buy_price/single_value
                            elif "sell_nums" in transaction:
                                sell_nums = transaction["sell_nums"]
                                confirmed_nums=confirmed_nums-sell_nums
                if confirmed_nums<0:
                    print("严重错误：仓库中的数量为负数")
                    return -1
                return confirmed_nums #目前仓库中的数量
        except Exception as e:
            print(f"获取仓库失败: {e}")
            return

    

def get_next_trading_day(on_submit_date, code, n=1):
    """返回 on_submit_date 后的第 n 个交易日"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'], format="%Y-%m-%d")
        on_submit_date_obj = datetime.strptime(on_submit_date, "%Y-%m-%d")
        future_trading_days = df[df['净值日期'] > on_submit_date_obj]
        if future_trading_days.empty:
            print("没有找到有效的交易日数据。")
            return None
        if len(future_trading_days) >= n:
            next_trade_day = future_trading_days.iloc[n - 1]  # n-1，因为索引从0开始
            return next_trade_day['净值日期'].strftime("%Y-%m-%d"),next_trade_day['单位净值']
        else:
            print(f"只有 {len(future_trading_days)} 个交易日，无法找到第 {n} 个交易日。")
            return None
    except Exception as e:
        print(f"获取下一个交易日失败: {e}")
        return None





if __name__=="__main__":
    # get_correct_rate(fund_code = '000216',obeserve_start_date='2025-08-01',observe_end_date='2025-09-20',expected_steps=10)
    # result=fourier_predict(code="000216",end_date='2025-10-10',window_size=10,prediction_steps=10,add_trend=True)
    # instance=decison_maker(fund_code="000216",path=r'A:\projects\money2\my_types\Qdii\000216.csv',df=None)
    # print(instance.newest_date)
    # result=instance.is_instant_bounce(window_size=10)

    # instance.caculate_year_rate_sliding()
    transaction_worker=buy_tracker(code="000216")
    transaction_worker.on_submit_transaction(buy_date="2025-10-20",buy_price=500,sell_date="2025-10-18",sell_nums=149,action="buy")
    transaction_worker.transaction_confirming(n=1)
    confirmed_nums=transaction_worker.get_repository()
    print(confirmed_nums)
