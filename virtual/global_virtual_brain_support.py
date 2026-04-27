#定义用于帮助大脑的辅助方法
from global_virtual_tracker import r_json,w_json
import csv
import pandas as pd
import os
from pathlib import Path
from global_date_manager import date_mannager
cwd = os.getcwd()
current_path = Path(__file__).resolve()
mappint_name_dir = current_path.parent.parent / "mapping" / "mapping.csv"

def get_fund_dict(csv_path):
    fund_name_map = {}
    try:
        # 使用 utf-8 或 gbk 编码打开，取决于你 CSV 文件的保存格式
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 假设 CSV 的表头是 "基金代码" 和 "基金全称"
                code = row['基金代码'].strip()
                name = row['基金全称'].strip()
                fund_name_map[code] = name
            return fund_name_map
    except Exception as e:
        print(f"读取文件出错: {e}")
    return fund_name_map

class fund_mannager():
    def __init__(self,dfs,date_mannager:date_mannager):
        self.fund_name_map=get_fund_dict(mappint_name_dir)
        self.dfs=dfs
        self.d_m=date_mannager
        

    def search_name(self,fund_code):
        return self.fund_name_map.get(fund_code,fund_code)
    
    def is_trade_day(self):
        """检查是否为交易日"""
        first_df = next(iter(self.dfs.values()))
        # 将当前日期转为 pandas 的 Timestamp，确保类型兼容
        target_date = pd.to_datetime(self.d_m.get_date())
        # 检查该日期是否在序列中
        if (first_df['净值日期'] == target_date).any():
            return True
        print(f"{target_date} 不是交易日")
        return False
    
    def check_fund_value(self, code):
        """查询今天fund最新价值，如果今天没数据，自动找之前最近的一天"""
        df = self.dfs[code]
        search_date = pd.to_datetime(self.d_m.get_date())
        if not pd.api.types.is_datetime64_any_dtype(df['净值日期']):
            df['净值日期'] = pd.to_datetime(df['净值日期'])
        past_df = df[df['净值日期'] <= search_date]
        if not past_df.empty:
            latest_row = past_df.iloc[-1]
            nav_value = latest_row['累计净值']
            return nav_value
        else:
            print(f"代码 {code} 在 {search_date} 之前没有任何行情数据")
            return None







if __name__=="__main__":
    fund_map=get_fund_dict(mappint_name_dir)
    
    print(fund_map["900001"])