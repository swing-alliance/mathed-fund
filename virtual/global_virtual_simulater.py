from virtual_canvas import virtualcanvas
from virtual_df_split import get_dataframe_by_path,split_dataframe
from global_virtual_tracker import pause,global_virtual_tracker
from virtual_tracker import reset_tracker
from virtual_condition import VirtualCondition
from virtual_account import virtual_account
from PyQt5.QtCore import QThread
from datetime import datetime, timedelta
from collections import deque
from thread_support import SimulationThread
from pathlib import Path
import time
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import sys
import os

current_path = Path(__file__).resolve()
target_dir = current_path.parent.parent / "my_types" / "Equity"







class virtual_simulater:
    def __init__(self,paths,initial_cash=10000,start_date=None,end_date=None):
        self.paths=paths
        self.virtual_account=virtual_account(initial_cash=initial_cash)
        self.end_date=datetime.strptime(end_date, "%Y-%m-%d")
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.transaction_orders = deque(maxlen=50)
        self.df_names=[path.split("\\")[-1].split(".")[0] for path in paths]
        self.row_dfs={}
        self.dataframes={}
        self.get_row_dfs()
        
        self.get_trimmed_dataframes()
        self.transaction_trakers={}
        self.global_vt=global_virtual_tracker(dfs=self.dataframes,date=self.current_date,account=self.virtual_account)



    def time_flow(self):
        """模拟时间流动，每调用一次，日期前进一天，并更新所有 tracker 的日期"""
        if self.current_date<self.end_date:
            self.current_date += timedelta(days=1)
            self.update_tracker()
            
            return True
        return False

    def update_tracker(self):
        """时间流逝后，需要更新tracker 的日期，并让它们处理新的日期逻辑"""
        self.get_trimmed_dataframes()
        self.global_vt.dfs=self.dataframes
        self.global_vt.date=self.current_date

    def get_row_dfs(self):
        for name, path in zip(self.df_names, paths):
            raw_df = get_dataframe_by_path(path)
            self.row_dfs[name]=raw_df


    def get_trimmed_dataframes(self):
        """根据当前日期修剪数据"""
        try:
            # 修正 1: 使用 .items() 遍历字典
            for name, row_df in self.row_dfs.items():
                # 修正 2: 仅在需要时转换，或者确保在读取 CSV 时已经转过日期
                # 如果日期已经是 datetime 类型，这一行会自动跳过，不影响速度
                if not pd.api.types.is_datetime64_any_dtype(row_df['净值日期']):
                    row_df['净值日期'] = pd.to_datetime(row_df['净值日期'])
                
                # 过滤数据
                df_clipped = row_df[row_df['净值日期'] <= self.current_date].copy()
                self.dataframes[name] = df_clipped
                
        except Exception as e:
            # 修正 3: 打印具体的错误原因和位置
            import traceback
            print(f"❌ 裁剪时发生具体错误: {e}")
            traceback.print_exc() 
            # 建议抛出异常，让主程序知道出大事了，不要盲目跑下去
            raise e


    # def get_specific_dataframe(self,end_date):
    #     """获取特定日期的 DataFrame，用于计算指标等"""
    #     special_dfs = {}
    #     for name, df in self.row_dfs.items():
    #         try:
    #             if df.empty:
    #                 continue
                    
    #             # 修正：从原始 df 中提取起始日期，而不是从还没创建的 special_dfs 中提
    #             start_time_val = df.iloc[0]['净值日期']
                
    #             special_dfs[name] = split_dataframe(
    #                 df.copy(), 
    #                 start_time=start_time_val, 
    #                 end_time=end_date
    #             )
    #         except (KeyError, IndexError) as e:
    #             print(f"无法获取 {name} 的特定数据: {e}")
    #             continue
    #     return special_dfs

    def virtual_system_confirm(self):
        "开始一天的确认"
        self.global_vt.global_transaction_confirming()



    def virtual_buy(self,code,ratio):
        """模拟买入操作，考虑当前余额和持仓比例"""
        cash=self.virtual_account.get_balance()
        if cash<=0:
            print("余额不足，无法执行买入操作")
            return
        buy_amount=cash*ratio
        self.global_vt.global_transaction_submit(code,self.current_date, buy_amount, None, None,"buy")


    def virtual_sell(self,code,ratio):
        """模拟卖出操作，考虑当前持仓数量和卖出比例"""
        self.global_vt.global_transaction_submit(code,None,None,self.current_date,ratio,"sell")


    
 

    def start(self):
        """执行全局追踪器架构的测试代码"""
        try:
            reset_tracker()
            time_count=1
            while self.time_flow():
                self.virtual_buy("000011",1)
                if time_count%8==0:
                    self.virtual_sell("000011",1)
                pause(info=f"当前日期{self.current_date}, 计数器{time_count%4}, 当前df数量{len(self.dataframes)}")
                self.virtual_system_confirm()
                
                time_count+=1

                
        except Exception as e:
            import traceback
            traceback.print_exc()




    def end(self):
        """结束模拟，清理资源等"""
        print("模拟已结束")
            



if __name__ == "__main__":
    names = os.listdir(target_dir)
    paths = [os.path.join(target_dir, name) for name in names if name.endswith(".csv")]
    
    simulater = virtual_simulater(
        paths=paths, 
        initial_cash=10000, 
        start_date="2024-9-24", 
        end_date="2026-4-1"
    )
    simulater.start()

