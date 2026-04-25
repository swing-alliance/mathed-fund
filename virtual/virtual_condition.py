from virtual_calculate import (max_sharp_ratio_for_days,yearly_return_since_start,get_annualized_volatility_for_period,get_annualized_volatility_for_period,get_lowest_point_after_high,
                        get_highest_point_by_period)
from virtual_df_split import split_dataframe
from datetime import datetime


class VirtualCondition:
    def __init__(self, dataframes: dict, current_date):
        """虚拟条件类，基于数据帧和当前日期计算满足条件的标的"""
        self.dataframes = dataframes
        self.codes = list(dataframes.keys())
        if isinstance(current_date, str):
            self.current_date = datetime.strptime(current_date, "%Y-%m-%d")
        else:
            self.current_date = current_date
        for name, df in self.dataframes.items():
            if df is not None and not df.empty:# 增加保护：确保 df 不为空再 iloc
                start_dt = df.iloc[0]['净值日期']
                end_dt = self.current_date.strftime("%Y-%m-%d")
                self.dataframes[name] = split_dataframe(df, start_time=start_dt, end_time=end_dt)
            else:
                # print(f"警告：{name} 数据为空，跳过裁剪")
                pass

    def sharp_ratio_condition(self, days=60):
        """当前夏普比最大的一个"""
        print(f"正在计算 {self.current_date.strftime('%Y-%m-%d')} 的 {days} 日夏普比率...")
        sharpe_codes = {} 
        for name, df in self.dataframes.items():
            # --- 新增筛选逻辑 ---
            # 如果当前 DataFrame 的行数不足以支撑计算周期，直接跳过
            if df is None or len(df) < days:
                print(f"{name} 数据量不足 {days} 行 (当前仅有 {len(df) if df is not None else 0} 行)，跳过计算")
                continue 
            # ------------------
            sharp_ratio = max_sharp_ratio_for_days(df, period_days=days)
            if sharp_ratio is not None and sharp_ratio > 1.0:
                sharpe_codes[name] = sharp_ratio
        
        if not sharpe_codes:
            print("今日没有符合条件的标的")
            return []
        sorted_sharpe = sorted(sharpe_codes.items(), key=lambda item: item[1], reverse=True)
        top_code = sorted_sharpe[0][0]
        return [top_code]
    

    def volatility_lowpoint_ratio_condition(self,days):
        """高波动，且在低位,返回前三个"""
        draw_down_threahold=0.10
        v_codes={}
        for name, df in self.dataframes.items():
            if df is None or len(df) < days:
                continue
            max_annualized_volatility,_,_,_=get_annualized_volatility_for_period(code=None,df=df,period_days=365)
            lowest_point_in_period_value, _ = get_lowest_point_after_high(df, period_days=60)
            highest_point_in_period_value, _ = get_highest_point_by_period(df, period_days=60)
            if lowest_point_in_period_value and highest_point_in_period_value*(1-draw_down_threahold)>lowest_point_in_period_value:
                v_codes[name]=max_annualized_volatility
        if not v_codes:
            print("今日没有符合条件的标的")
            return []
        v_codes=sorted(v_codes.items(), key=lambda item: item[1], reverse=True)
        top_three_keys = [key[0] for key in v_codes[:10]]
        return top_three_keys
            


    def temperature_sharpe_condition(self,days):
        """更具市場溫度做返回"""
        t_s_codes={}
        total_nums=len(self.codes)
        up_nums=0
        down_nums=0
        for name, df in self.dataframes.items():
            if df is None or len(df) < days:
                continue
            if yearly_return_since_start(code=None,df=df,expected_interval_days=40)>=0:
                up_nums+=1
            else:
                down_nums+=1
        up_ratio=up_nums/total_nums
        down_ratio=down_nums/total_nums
        if (down_ratio-up_ratio)>0.1:
            print("市場溫度低，不參與")
            return []
        for name, df in self.dataframes.items():
            # --- 新增筛选逻辑 ---
            # 如果当前 DataFrame 的行数不足以支撑计算周期，直接跳过
            if df is None or len(df) < days:
                
                continue 
            # ------------------
            sharp_ratio = max_sharp_ratio_for_days(df, period_days=days)
            if sharp_ratio is not None and sharp_ratio > 1.0:
                t_s_codes[name] = sharp_ratio#高溫下的所有可能

        t_s_codes=sorted(t_s_codes.items(), key=lambda item: item[1], reverse=True)
        top_code=t_s_codes[0][0]
        return [top_code]            

