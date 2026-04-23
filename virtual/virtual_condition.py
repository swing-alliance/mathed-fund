from virtual_calculate import max_sharp_ratio_for_days
from virtual_df_split import split_dataframe
from datetime import datetime

class VirtualCondition:
    def __init__(self, dataframes: dict, current_date):
        self.dataframes = dataframes
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
                print(f"警告：{name} 数据为空，跳过裁剪")

    def sharp_ratio_condition(self, days=60):
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