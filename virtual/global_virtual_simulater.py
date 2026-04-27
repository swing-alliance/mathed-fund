#这是系统的入口，事件循环的起点
from virtual_canvas import virtualcanvas
from virtual_df_split import get_dataframe_by_path,split_dataframe
from global_virtual_tracker import pause,global_virtual_tracker
from global_virtual_tracker import reset_tracker
from virtual_condition import VirtualCondition
from virtual_account import virtual_account
from PyQt5.QtCore import QThread
from datetime import datetime, timedelta
from collections import deque
from global_virtual_brain import global_brain
from thread_support import SimulationThread
from pathlib import Path
import time
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import sys
import os
from global_date_manager import date_mannager
current_path = Path(__file__).resolve()
target_dir = current_path.parent.parent / "my_types" / "Equity"



    




class virtual_simulater:
    def __init__(self,paths,initial_cash=10000,start_date=None,end_date=None):
        self.paths=paths
        self.virtual_account=virtual_account(initial_cash=initial_cash)
        self.start_date=datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date=datetime.strptime(end_date, "%Y-%m-%d")
        self.date_mannager=date_mannager(start_date)
        self.current_date = self.date_mannager.get_date()
        self.df_names=[path.split("\\")[-1].split(".")[0] for path in paths]
        self.row_dfs={}
        self.dataframes={}
        self.get_row_dfs()
        
        self.get_trimmed_dataframes()
        self.transaction_trakers={}
        self.global_vt=global_virtual_tracker(dfs=self.dataframes,date=self.current_date,account=self.virtual_account)



    def time_flow(self):
        """模拟时间流动，每调用一次，日期前进一天，并更新所有 tracker 的日期"""
        if self.date_mannager.get_date()<self.end_date:
            self.date_mannager.daypass()
            self.current_date = self.date_mannager.get_date()
            self.update_tracker()
            return True
        return False

    def update_tracker(self):
        """时间流逝后，需要更新tracker 的日期，并让它们处理新的日期逻辑"""
        self.get_trimmed_dataframes()
        self.global_vt.dfs=self.dataframes
        self.global_vt.date=self.date_mannager.get_date()

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
                df_clipped = row_df[row_df['净值日期'] <= self.date_mannager.get_date()].copy()#这会把当天的数据裁剪进去，卖出时可以直接使用其净值冻结
                self.dataframes[name] = df_clipped
                
        except Exception as e:
            # 修正 3: 打印具体的错误原因和位置
            import traceback
            print(f"❌ 裁剪时发生具体错误: {e}")
            traceback.print_exc() 
            # 建议抛出异常，让主程序知道出大事了，不要盲目跑下去
            raise e


    def virtual_system_confirm(self):
        "开始一天的确认"
        self.global_vt.global_transaction_confirming()



    def virtual_buy(self,code,ratio,t):
        """模拟买入操作，考虑当前余额和持仓比例,t设置为0"""
        try:
            cash=self.virtual_account.get_balance()
            if cash<=0:
                print("余额不足，无法执行买入操作")
                return
            buy_amount=cash*ratio
            self.global_vt.global_transaction_submit(code,self.current_date, buy_amount, None, None,"buy",t)
        except Exception as e:
            raise RuntimeError(f"买入时发生了意外{e}")


    def virtual_sell(self,code,ratio,t):
        """模拟卖出操作，考虑当前持仓数量和卖出比例,卖出的冻结时间"""
        try:
            self.global_vt.global_transaction_submit(code,None,None,self.current_date,ratio,"sell",t)
        except Exception as e:
            raise RuntimeError(f"卖出时发生了意外{e}")

    
    def user_operate(self):
        """
        灵活交互模式：
        输入格式：[动作] [代码] [比例] [t]
        例子：
        b 000061 0.5 0  -> 买入 000061，比例 0.5，t=0
        s 000061 1 1    -> 卖出 000061，全仓，t=1
        回车            -> 直接跳过
        """
        print(f"\n>>>> 暂停中 [当前日期: {self.current_date}] <<<<")
        user_input = input("请输入指令 (动作 代码 比例 t) 或直接回车跳过: ").strip().lower()

        if not user_input:
            print(">>> 跳过操作。")
            return

        parts = user_input.split()
        action = parts[0]
        if action not in ['b', 's']:
            print(f"❌ 错误：无效动作 '{action}'，请输入 b (买) 或 s (卖)")
            return
        try:
            code = parts[1] if len(parts) > 1 else "000061"
            ratio = float(parts[2]) if len(parts) > 2 else 0.1
            t = int(parts[3]) if len(parts) > 3 else 0
            if action == 'b':
                print(f"执行：买入 {code}, 比例 {ratio}, t={t}")
                self.virtual_buy(code, ratio, t)
            elif action == 's':
                print(f"执行：卖出 {code}, 比例 {ratio}, t={t}")
                self.virtual_sell(code, ratio, t)
        except ValueError:
            print("❌ 错误：比例应为数字，t 应为整数。例如: b 000061 0.5 0")
        except Exception as e:
            print(f"❌ 指令执行失败: {e}")

    def start(self):
        """执行全局追踪器架构的测试代码,手动版入口"""
        try:
            reset_tracker()
            time_count=1
            while self.time_flow():
                if time_count%2==0:
                    pause(info=f"程序:当前是{str(self.date_mannager.get_date())[:10]}三点前,选择操作")
                    self.user_operate()
                pause(info=f"当前日期{str(self.date_mannager.get_date())[:10]}三点后, 计数器{time_count%4}, 当前df数量{len(self.dataframes)}，账户剩余{self.virtual_account.get_balance()},即将度过今天")
                self.virtual_system_confirm()
                
                time_count+=1
        except Exception as e:
            import traceback
            traceback.print_exc()





    def start_auto_brain(self):
        """执行全局追踪器架构的测试代码,自动化回测入口"""
        try:
            reset_tracker()
            brain=global_brain(dfs=self.dataframes,vt=self.global_vt,account=self.virtual_account,date_mannager=self.date_mannager)
            brain.fund_mannager.date = self.current_date
            while self.time_flow():
                brain.date=self.current_date
                if brain.isawake():
                    brain.think()
                print("系统检查账户余额",self.virtual_account.get_balance())
                #这里是三点的分水岭
                time.sleep(1)#慢1秒
                self.virtual_system_confirm()
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
        start_date="2025-6-1", 
        end_date="2026-3-1"
    )
    simulater.start_auto_brain()

