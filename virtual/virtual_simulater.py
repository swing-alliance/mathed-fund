from virtual_calculate import max_sharp_ratio_for_days
from virtual.virtual_df_split import get_dataframe_by_path,split_dataframe
from virtual.virtual_tracker import virtual_tracker
import pandas as pd


class virtual_simulater:
    def __init__(self,pathes):
        self.df_names=[path.split("\\")[-1].split(".")[0] for path in pathes]
        self.dataframes={}
        for name,path in zip(self.df_names,pathes):
            self.dataframes[name]=get_dataframe_by_path(path)
        self.init_cash=10000
        self.transaction_traker=[]
        

    def virtual_time_flow(self,start_time,end_time):
        self.split_dfs=[split_dataframe(df,start_time,end_time) for df in self.dataframes]
        return self.split_dfs
    
    def virtual_buy(self,name,time,cash):
        try:
            if cash>self.init_cash:
                print("现金不足，无法购买")
                return False
            self.transaction_traker.append({"name":name,"time":time,"cash":cash})
            self.init_cash-=cash
            return True
        except:
            print("虚拟购买严重失败，检查输入")
            return False

    def virtual_sell(self,name,time,ratio):
        try:
            trasactions=self.get_virtual_buy_trasactions(name)
            if not trasactions:
                print(f"没有找到{name}的购买记录，无法出售")
                return False
            total_cash=0
            for transaction in trasactions:
                total_cash+=transaction["cash"]
            df = self.dataframes[name]
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            sell_date = pd.Timestamp(time)
            sell_data = df[df['净值日期'] == sell_date]
            if sell_data.empty:
                print(f"日期 {time} 找不到对应的净值数据")
                return None
            current_idx = sell_data.index[0]
            sell_price = df.loc[current_idx, '累计净值']
            cash_get = range_cash * ratio
        except:
            print("虚拟出售严重失败，检查输入")
            return False
        
    def get_virtual_buy_trasactions(self,name):
        try:
            transactions = []
            for transaction in self.transaction_traker:
                if transaction["name"]==name:
                    transactions.append(transaction)
            return transactions
        except:
            print("获取虚拟购买记录失败，检查输入")
            return []

