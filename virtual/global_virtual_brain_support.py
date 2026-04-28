#定义用于帮助大脑的辅助方法
from global_virtual_tracker import r_json,w_json
from virtual_calculate import yearly_return_since_start,get_annualized_volatility_for_period,max_sharp_ratio_for_days
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
    def __init__(self,dfs:dict,date_mannager:date_mannager):
        self.fund_name_map=get_fund_dict(mappint_name_dir)
        self.dfs=dfs
        self.d_m=date_mannager
        

    def search_name(self,fund_code):
        return self.fund_name_map.get(fund_code,fund_code)
    
    def get_selltime_t(self,fund_code):
        """动态获取卖出时冻结时间的t"""
        if fund_code is not None:
            name=self.search_name((fund_code))
            clean_name = name.replace('（', '(').replace('）', ')')
            if "qdii" in clean_name:
                # 针对 QDII 的逻辑，比如设置更高的数据延迟容忍度
                return 10
            if "美国" in clean_name or "标普" in clean_name or "纳斯达克" in clean_name or "全球" in clean_name or "德国" in clean_name or "日本" in clean_name:
                return 10
            else:
                return 2
        else:
            print("基金管理器的获取t时出现严重错误")
            return 0
    
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
    
    def check_fund_value_former(self, code):
        """查询今天fund最新价值，如果今天没数据，自动向后找之前最近的一天"""
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
        

    def get_sorted_yearly_return_dict(self,interval_days:int):
        """返回按照年化收益排名的代码名字字典，数据结构为("代码":"收益率"),计算量沉重"""
        try:
            return_dict={}
            for code,df in self.dfs.items():
                if not df.empty:
                    interval_days_yearly_return=yearly_return_since_start(code=None,df=df,expected_interval_days=interval_days)
                if interval_days_yearly_return:
                    return_dict[code]=interval_days_yearly_return
                continue
            sorted_dict = sorted(return_dict.items(), key=lambda x: x[1], reverse=True)
            sorted_dict=dict(sorted_dict)
            return sorted_dict
        except Exception as e:
            raise RuntimeError(f"返回按照年化收益排名的代码名字字典错误,{e}")
        
    
    def get_sorted_sharpe_return_dict(self,interval_days:int):
        """返回按照夏普排名的代码名字字典，数据结构为("代码":"夏普率"),计算量沉重"""
        try:
            return_dict={}
            for code,df in self.dfs.items():
                if code == "004371":
                    print(df)
                if not df.empty:
                    interval_days_sharpe_return=max_sharp_ratio_for_days(df,interval_days)
                if interval_days_sharpe_return:
                    return_dict[code]=interval_days_sharpe_return
                continue
            sorted_dict = sorted(return_dict.items(), key=lambda x: x[1], reverse=True)
            sorted_dict=dict(sorted_dict)
            return sorted_dict
        except Exception as e:
            raise RuntimeError(f"返回按照夏普排名的代码名字字典错误，{e}")
        

    def check_bear(self,interval_days:int):
        """检查是否为熊市,计算量繁重"""
        sorted_yearly_return_dict=self.get_sorted_yearly_return_dict(interval_days)
        total_count=0
        bad_count=0
        for value in sorted_yearly_return_dict.values():
            total_count+=1
            if value<0:
                bad_count+=1
        bad_ratio=bad_count/total_count
        if bad_ratio>0.55:
            return True
        return False
    









if __name__=="__main__":
    fund_map=get_fund_dict(mappint_name_dir)
    
    print(fund_map["900001"])