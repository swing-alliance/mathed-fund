from virtual_canvas import virtualcanvas
from virtual_df_split import get_dataframe_by_path,split_dataframe
from global_virtual_tracker import pause
from virtual_tracker import virtual_tracker,reset_tracker
from virtual_condition import VirtualCondition
from virtual_account import virtual_account
from PyQt5.QtCore import QThread
from datetime import datetime, timedelta
from collections import deque
from thread_support import SimulationThread
from pathlib import Path
import time
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
        self.get_trimmed_dataframes(end_date,paths)
        self.transaction_trakers={}
        for name in self.df_names:
            self.transaction_trakers[name]=virtual_tracker(code=name, df=self.dataframes[name], date=self.current_date, virtual_account=self.virtual_account)



    def time_flow(self):
        """模拟时间流动，每调用一次，日期前进一天，并更新所有 tracker 的日期"""
        if self.current_date<self.end_date:
            self.update_trackers()
            self.current_date += timedelta(days=1)
            return True
        return False

    def update_trackers(self):
        """时间流逝后，需要更新所有 tracker 的日期，并让它们处理新的日期逻辑"""
        for name in self.df_names:
            self.transaction_trakers[name].df=self.dataframes[name]
            self.transaction_trakers[name].date=self.current_date
            self.transaction_trakers[name].virtual_account=self.virtual_account


    def get_trimmed_dataframes(self,end_date,paths):
        """根据当前日期修剪数据，确保每个 DataFrame 只包含当前日期之前的数据"""
        for name, path in zip(self.df_names, paths):
            # 加载原始数据并存入 row_dfs 备用
            raw_df = get_dataframe_by_path(path)
            self.row_dfs[name] = raw_df
            
            # 复制一份用于当前计算的 dataframes
            # 确保 self.current_date 是 datetime 对象，否则无需 strftime
            start_str = self.current_date.strftime("%Y-%m-%d")
            self.dataframes[name] = split_dataframe(
                raw_df.copy(), 
                start_time=start_str, 
                end_time=end_date
            )

    def get_specific_dataframe(self,end_date):
        """获取特定日期的 DataFrame，用于计算指标等"""
        special_dfs = {}
        for name, df in self.row_dfs.items():
            try:
                if df.empty:
                    continue
                    
                # 修正：从原始 df 中提取起始日期，而不是从还没创建的 special_dfs 中提
                start_time_val = df.iloc[0]['净值日期']
                
                special_dfs[name] = split_dataframe(
                    df.copy(), 
                    start_time=start_time_val, 
                    end_time=end_date
                )
            except (KeyError, IndexError) as e:
                print(f"无法获取 {name} 的特定数据: {e}")
                continue
        return special_dfs

    def virtual_system_confirm(self):
        "开始一天的确认"
        
        if self.transaction_orders:
            for order in self.transaction_orders:
                order.transaction_confirming(n=1)

    def cheak_cash(self):
        if self.virtual_account.get_balance()>0:
            return True
        return False


    def virtual_buy(self,code,date,ratio):
        """模拟买入操作，考虑当前余额和持仓比例"""
        cash=self.virtual_account.get_balance()
        if cash<=0:
            print("余额不足，无法执行买入操作")
            return
        buy_amount=cash*ratio
        self.transaction_trakers[code].on_submit_transaction(buy_date=date, buy_price=buy_amount, sell_date=None, sell_nums=None, action="buy")
        self.transaction_orders.append(self.transaction_trakers[code])


    def virtual_sell(self,code,date,ratio):
        """模拟卖出操作，考虑当前持仓数量和卖出比例"""
        repository = self.transaction_trakers[code].get_repository(purpose="sell")
        if repository <= 0:
            print("当前未持有该股票，无法执行卖出操作")
            return
        sell_amount = repository * ratio
        self.transaction_trakers[code].on_submit_transaction(buy_date=None, buy_price=None, sell_date=date, sell_nums=sell_amount, action="sell")
        self.transaction_orders.append(self.transaction_trakers[code])


    def get_account_balance(self):
        """获取当前账户余额(现金+持仓价值)"""
        return self.virtual_account.get_dynamic_balance(trackers=self.transaction_trakers.values())
    
    def get_account_cash(self):
        """获取当前账户现金余额"""
        return self.virtual_account.get_balance()

    def get_repository(self,code):
        """获取当前持仓数量"""
        return self.transaction_trakers[code].get_repository(purpose="sell")
    
 
    # def start(self, callback=None):
    #     """执行只单调追高的回测"""
    #     try:
    #         reset_tracker()
    #         day_counter = 0
    #         current_holding_code = None 
    #         recommend_code=None
    #         while self.time_flow():
                
    #             # --- 1. 策略逻辑 (保持原有频率) ---
    #             if day_counter % 22 == 0:
    #                 print("执行策略逻辑，评估换仓机会...")
    #                 dfs = self.get_specific_dataframe(self.current_date)
    #                 cond_inst = VirtualCondition(dataframes=dfs, current_date=self.current_date)
    #                 to_buy_list = cond_inst.sharp_ratio_condition(days=22)
    #                 new_code = to_buy_list[0] if to_buy_list else None
    #                 recommend_code=new_code


    #                 if new_code != current_holding_code:
    #                     if current_holding_code:
    #                         self.virtual_sell(code=current_holding_code, date=self.current_date, ratio=1)
    #                     current_holding_code = new_code
    #             if recommend_code and self.cheak_cash():
                        
    #                     self.virtual_buy(code=recommend_code, date=self.current_date, ratio=1)

    #             # --- 2. 删除了循环内的 transaction_confirming ---
    #             # 直接进入数据回传阶段
    #             self.virtual_system_confirm()
                
    #             # --- 3. UI 数据回传与性能优化 ---
    #             if callback:
    #                 # 只有当资产发生变化或者每隔几天才回传，能极大减轻 UI 负担
    #                 date_str = self.current_date.strftime('%Y-%m-%d')
    #                 balance = float(self.get_account_balance()) 
    #                 callback(date_str, balance)
    #                 day_counter += 1
    #         print(f"最终账户余额: {self.virtual_account.get_repo_info(trackers=self.transaction_trakers.values())}, 现金余额: {self.get_account_cash()}")
    #         print(f"回测核心运行完毕。")
                
    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()

    # def start(self,callback):
    #     """执行关于波动和地点的回测"""
    #     try:
    #         reset_tracker()
    #         day_counter = 0
    #         current_holding_codes =[] 
    #         while self.time_flow():
    #             # --- 1. 策略逻辑 (保持原有频率) ---
    #             if day_counter % 22 == 0:
    #                 print("执行策略逻辑，评估换仓机会...")
    #                 dfs = self.get_specific_dataframe(self.current_date)
                    
    #                 cond_inst = VirtualCondition(dataframes=dfs, current_date=self.current_date)
    #                 suggest_buy_list = cond_inst.volatility_lowpoint_ratio_condition(days=365)
    #                 print(suggest_buy_list)
    #                 to_buy_nums=0
    #                 to_buy_list=[]
    #                 to_sell_list=[]
    #                 if suggest_buy_list:
    #                     for item in suggest_buy_list:
    #                         if item not in current_holding_codes:
    #                             to_buy_nums+=1
    #                             to_buy_list.append(item)
    #                 print("打算買入",to_buy_list)
    #                 while len(to_buy_list)+len(current_holding_codes)>4:
    #                     if current_holding_codes:
    #                         item=current_holding_codes.pop()
    #                         to_sell_list.append(item)
    #                     if to_buy_list:
    #                         to_buy_list.pop()
    #                 print("打算賣出？",to_sell_list)
    #                 for code in to_sell_list:
    #                     print("執行賣出",to_sell_list)
    #                     self.virtual_sell(code=code, date=self.current_date, ratio=1)
    #                 if to_buy_list and self.cheak_cash()<2000:
    #                     for code in to_buy_list:
    #                         self.virtual_buy(code=code,date=self.current_date,ratio=1/len(to_buy_list))
    #                         if code not in current_holding_codes:
    #                             current_holding_codes.append(code)
    #             self.virtual_system_confirm()
    #             if callback:
    #                 date_str = self.current_date.strftime('%Y-%m-%d')
    #                 balance = float(self.get_account_balance()) 
    #                 callback(date_str, balance)
    #                 day_counter += 1
    #         print(f"最终账户余额: {self.virtual_account.get_repo_info(trackers=self.transaction_trakers.values())}, 现金余额: {self.get_account_cash()}")
    #         print(f"回测核心运行完毕。")
                
    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    

    def start(self,callback):
        """执行关于溫度和夏普的回测"""
        try:
            reset_tracker()
            day_counter = 0
            current_holding_codes =[] 
            while self.time_flow():
                # --- 1. 策略逻辑 (保持原有频率) ---
                if day_counter % 22 == 0:
                    print("执行策略逻辑，评估换仓机会...")
                    dfs = self.get_specific_dataframe(self.current_date)
                    
                    cond_inst = VirtualCondition(dataframes=dfs, current_date=self.current_date)
                    suggest_buy_list = cond_inst.temperature_sharpe_condition(days=120)
                    if not suggest_buy_list:
                        for item in current_holding_codes:
                            self.virtual_sell(code=item,date=self.current_date,ratio=1)
                    if suggest_buy_list and current_holding_codes and suggest_buy_list[0]!=current_holding_codes[0]:
                        print("温度高，换着卖卖卖",current_holding_codes[0])
                        self.virtual_sell(code=current_holding_codes[0],date=self.current_date,ratio=1)

                    
                    if suggest_buy_list and self.cheak_cash()>0:
                        self.virtual_buy(code=suggest_buy_list[0],date=self.current_date,ratio=1)
                        if current_holding_codes:
                            current_holding_codes[0]=suggest_buy_list[0]
                self.virtual_system_confirm()
                if callback:
                    date_str = self.current_date.strftime('%Y-%m-%d')
                    balance = float(self.get_account_balance()) 
                    callback(date_str, balance)
                    day_counter += 1
            print(f"最终账户余额: {self.virtual_account.get_repo_info(trackers=self.transaction_trakers.values())}, 现金余额: {self.get_account_cash()}")
            print(f"回测核心运行完毕。")
                
        except Exception as e:
            import traceback
            traceback.print_exc()





    def end(self):
        """结束模拟，清理资源等"""
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
    paths = [os.path.join(target_dir, name) for name in names if name.endswith(".csv")]
    
    simulater = virtual_simulater(
        paths=paths, 
        initial_cash=10000, 
        start_date="2024-9-24", 
        end_date="2026-4-1"
    )

    # 3. 创建并配置线程
    sim_thread = SimulationThread(simulater)
    
    # --- 关键：将子线程信号连接到画布的更新方法 ---
    sim_thread.update_signal.connect(canvas.update_data)
    
    # 模拟结束后的处理
    sim_thread.finished_signal.connect(lambda val: print(f"回测圆满结束，终值: {val}"))
    sim_thread.finished.connect(simulater.end)

    # 4. 启动线程
    sim_thread.start(QThread.HighestPriority)
    sys.exit(app.exec_())

