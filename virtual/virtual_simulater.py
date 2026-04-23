from virtual_canvas import virtualcanvas
from virtual_df_split import get_dataframe_by_path,split_dataframe
from virtual_tracker import virtual_tracker,reset_tracker
from virtual_condition import VirtualCondition
from virtual_account import virtual_account
from datetime import datetime, timedelta
from thread_support import SimulationThread
from pathlib import Path
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import sys
import os

current_path = Path(__file__).resolve()
target_dir = current_path.parent.parent / "my_types" / "Equity"


def get_pathes():
    pathes=[]
    for i in range(1,6):
        pathes.append(f"A:\\projects\\money2\\my_types\\Qdii\\50{i}018.csv")
    return pathes




class virtual_simulater:
    def __init__(self,pathes,initial_cash=10000,start_date=None,end_date=None):
        self.pathes=pathes
        self.virtual_account=virtual_account(initial_cash=initial_cash)
        self.end_date=datetime.strptime(end_date, "%Y-%m-%d")
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.df_names=[path.split("\\")[-1].split(".")[0] for path in pathes]
        self.dataframes={}
        self.get_trimed_dataframes(end_date,pathes)
        self.transaction_trakers={}
        for name in self.df_names:
            self.transaction_trakers[name]=virtual_tracker(code=name, df=self.dataframes[name], date=self.current_date, virtual_account=self.virtual_account)

    def time_flow(self):
        """模拟时间流动，每调用一次，日期前进一天，并更新所有 tracker 的日期"""
        if self.current_date<self.end_date:

            self.current_date += timedelta(days=1)
            self.update_trackers()
            return True
        return False

    def update_trackers(self):
        for name in self.df_names:
            self.transaction_trakers[name]=virtual_tracker(code=name, df=self.dataframes[name], date=self.current_date, virtual_account=self.virtual_account)


    def get_trimed_dataframes(self,end_date,pathes):
        """根据当前日期修剪数据，确保每个 DataFrame 只包含当前日期之前的数据"""
        for name,path in zip(self.df_names,pathes):
            self.dataframes[name]=get_dataframe_by_path(path)
            self.dataframes[name]=split_dataframe(self.dataframes[name],start_time=self.current_date.strftime("%Y-%m-%d"),end_time=end_date)

    def get_specific_dataframe(self,end_date,pathes):
        """获取特定日期的 DataFrame，用于计算指标等"""
        special_dfs={}
        for name,path in zip(self.df_names,pathes):
            special_dfs[name]=get_dataframe_by_path(path)
            special_dfs[name]=split_dataframe(special_dfs[name],start_time=special_dfs[name].iloc[0]['净值日期'],end_time=end_date)
        return special_dfs

    
    def virtual_buy(self,code,date,ratio):
        """模拟买入操作，考虑当前余额和持仓比例"""
        cash=self.virtual_account.get_balance()
        if cash<=0:
            print("余额不足，无法执行买入操作")
            return
        buy_amount=cash*ratio
        self.transaction_trakers[code].on_submit_transaction(buy_date=date, buy_price=buy_amount, sell_date=None, sell_nums=None, action="buy")
        self.transaction_trakers[code].transaction_confirming(n=1)  # 确认交易，更新账户余额


    def virtual_sell(self,code,date,ratio):
        """模拟卖出操作，考虑当前持仓数量和卖出比例"""
        repository = self.transaction_trakers[code].get_repository(purpose="sell")
        if repository <= 0:
            print("当前未持有该股票，无法执行卖出操作")
            return
        sell_amount = repository * ratio
        self.transaction_trakers[code].on_submit_transaction(buy_date=None, buy_price=None, sell_date=date, sell_nums=sell_amount, action="sell")
        self.transaction_trakers[code].transaction_confirming(n=1)  # 确认交易，更新账户余额

    def get_account_balance(self):
        """获取当前账户余额(现金+持仓价值)"""
        return self.virtual_account.get_dynamic_balance(trackers=self.transaction_trakers.values())
    
    def get_account_cash(self):
        """获取当前账户现金余额"""
        return self.virtual_account.get_balance()

    def get_repository(self,code):
        """获取当前持仓数量"""
        return self.transaction_trakers[code].get_repository(purpose="sell")
    
 
    def start(self, callback=None):
        try:
            day_counter = 0
            current_holding_code = None 
            
            while self.time_flow():
                # --- 1. 策略逻辑 (保持原有频率) ---
                if day_counter % 7 == 0:
                    dfs = self.get_specific_dataframe(self.current_date, self.pathes)
                    cond_inst = VirtualCondition(dataframes=dfs, current_date=self.current_date)
                    to_buy_list = cond_inst.sharp_ratio_condition(days=60)
                    new_code = to_buy_list[0] if to_buy_list else None

                    # 原子换仓：内部已处理 confirmation
                    if new_code != current_holding_code:
                        if current_holding_code:
                            self.virtual_sell(code=current_holding_code, date=self.current_date, ratio=1)
                        if new_code:
                            self.virtual_buy(code=new_code, date=self.current_date, ratio=1)
                        current_holding_code = new_code

                # --- 2. 删除了循环内的 transaction_confirming ---
                # 直接进入数据回传阶段

                # --- 3. UI 数据回传与性能优化 ---
                if callback:
                    # 只有当资产发生变化或者每隔几天才回传，能极大减轻 UI 负担
                    # 这里我们保持每天回传，但必须配合 sleep 释放 CPU
                    date_str = self.current_date.strftime('%Y-%m-%d')
                    balance = float(self.get_account_balance()) 
                    callback(date_str, balance)
                    
                    # 强制微休眠：这是防止 PyQt 界面卡死的核心
                    # 即使是 0.0001 秒，也能让系统进行上下文切换去处理绘图
                    time.sleep(0.001) 

                day_counter += 1

            print(f"回测核心运行完毕。")
                
        except Exception as e:
            import traceback
            traceback.print_exc()





    def end(self):
        """结束模拟，清理资源等"""
        reset_tracker()
        print("模拟已结束")
            



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. UI 准备
    main_win = QMainWindow()
    main_win.setWindowTitle("基金回测实时监控 (多线程版)")
    main_win.resize(800, 500)
    central_widget = QWidget()
    main_win.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    canvas = virtualcanvas() # 你的绘图类
    layout.addWidget(canvas)
    main_win.show()

    # 2. 模拟器准备
    names = os.listdir(target_dir)
    pathes = [os.path.join(target_dir, name) for name in names if name.endswith(".csv")]
    
    simulater = virtual_simulater(
        pathes=pathes, 
        initial_cash=10000, 
        start_date="2025-02-15", 
        end_date="2026-02-15"
    )

    # 3. 创建并配置线程
    sim_thread = SimulationThread(simulater)
    
    # --- 关键：将子线程信号连接到画布的更新方法 ---
    sim_thread.update_signal.connect(canvas.update_data)
    
    # 模拟结束后的处理
    sim_thread.finished_signal.connect(lambda val: print(f"回测圆满结束，终值: {val}"))
    sim_thread.finished.connect(simulater.end)

    # 4. 启动线程
    sim_thread.start()

    sys.exit(app.exec_())

