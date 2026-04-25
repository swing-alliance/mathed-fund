
import json
import os
from datetime import date,timedelta,datetime
import pandas as pd
import time
from virtual_df_split import get_dataframe_by_path,split_dataframe


transaction_confirmed_path=os.path.join(os.getcwd(),'virtual_track',"virtual_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'virtual_track',"virtual_transaction_onsubmit.json")


class virtual_tracker:
    """虚拟化追踪完整的交易过程,用户通过对每只基金的追踪器进行操作来完成交易的提交和确认，追踪器会根据当前日期和数据自动处理交易逻辑，并与虚拟账户进行交互更新资金状态"""
    def __init__(self, code=None,df=None,date=None,virtual_account=None):
        """初始化追踪器，设置基本信息和数据,一个追踪器只能追踪一个标的的所有交易,到这里的df应该已经是根据当前日期修剪过的了"""
        self.virtual_account=virtual_account
        self.code = code

        self.df = split_dataframe(df,start_time=df['净值日期'].min(),end_time="2026-03-15") if df is not None else None
        self.transaction_confirmed_path = transaction_confirmed_path
        self.transaction_onsubmit_path = transaction_onsubmit_path
        if isinstance(date, str):
            self.date = datetime.strptime(date, "%Y-%m-%d")
        else:
        # 如果已经是 datetime 对象，直接赋值即可
            self.date = date
    def on_submit_transaction(self, buy_date, buy_price, sell_date, sell_nums,action):
        if action == "buy":
            try:
                if buy_price > self.virtual_account.get_balance():
                    print("余额不足，无法申请买入操作")
                    return
                self.buy_date =str(buy_date)[:10] or str(self.today_date)[:10]#此处注意datatime对象转换为字符串时会带有时间部分，切片[:10]可以保留日期部分，去掉时间部分
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
                data=self.get_next_trading_day(on_submit_date=self.buy_date, n=1)
                price=data[1] if data else None
                transaction_record = {
                "buy_date": self.buy_date,
                "buy_price": self.buy_price,
                "nums": self.buy_price/price if price else None,
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
                self.sell_date =str(sell_date)[:10] or str(self.today_date)[:10]    
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
                print(f"卖出记录已添加：{transaction_record}")
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
                                        confirm_result= self.get_next_trading_day(on_submit_date=buy_date,n=n)
                                        if confirm_result is None:
                                            print("买入确认交易日错误")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                        record = {
                                            "buy_price": buy_price,
                                            "confirmed_date": next_trading_day,
                                            "single_value": single_value,
                                            "nums": buy_price/single_value if single_value else None
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
                                        self.virtual_account.decrease_cash(buy_price)
                                        transaction["status"] = "checked"
                                    elif "sell_nums" in transaction:#卖出
                                        sell_nums = transaction["sell_nums"]
                                        sell_date = transaction["sell_date"]
                                        confirm_result= self.get_next_trading_day(on_submit_date=sell_date, n=n)
                                        if confirm_result is None:
                                            print("无法获取下一个交易日")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                            total_nums=self.get_repository()
                                            if total_nums<sell_nums:
                                                print("仓库数量不足,不执行卖出操作",total_nums,sell_nums)
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
                                        self.virtual_account.increase_cash(sell_nums*single_value if single_value else None)
                                        print("卖出成功了,钱回到了账户")
                                        transaction["status"] = "checked"
                                        
                                except Exception as e:
                                    print(f"最后买入确认失败: {e}")
                            else:
                                continue
                with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                    json.dump(onsubmit_data, f, ensure_ascii=False, indent=4)
                
            # print("交易确认成功！")
        except Exception as e:
            print(f"买入确认失败: {e}")
            return
        
    


    def get_repository(self,purpose="sell"):
        """获取仓库目前的数量"""
        try:
            if purpose=="sell": 
                with open(self.transaction_confirmed_path, 'r', encoding='utf-8') as f:
                    confirmed_data = json.load(f)
                    confirmed_nums=0
                    for code, group in confirmed_data.items():
                        if code == self.code:
                            for transaction in group:
                                if "confirmed_date" in transaction and "buy_price" in transaction :
                                    confirmed_date = transaction["confirmed_date"]
                                    confirmed_date = datetime.strptime(confirmed_date, "%Y-%m-%d")
                                    if confirmed_date.date() >= self.date.date():
                                        continue
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
            elif purpose=="get_market_value":
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
        
    def get_today_market_value(self):
        """获取目前的基金市值"""
        try:
            repository = self.get_repository(purpose="get_market_value")
            if repository <= 0:
                return 0.0 
            res = self.get_trading_day_critical(on_submit_date=self.date.strftime("%Y-%m-%d"))
            if res is None or len(res) < 2:
                return 0.0
            current_price = res["累计净值"]
            market_value = repository * current_price
            # 确保 market_value 本身不是 None
            return market_value if market_value is not None else 0.0
            
        except Exception as e:
            print(f"获取市值失败: {e}")
            return 0.0
    
        

        
    def get_next_trading_day(self, on_submit_date, n=None):
        """返回 on_submit_date 后的第 n 个交易日"""
        try:
            df=self.df
            df['净值日期'] = pd.to_datetime(df['净值日期'], format="%Y-%m-%d")
            on_submit_date_obj = datetime.strptime(on_submit_date, "%Y-%m-%d")
            future_trading_days = df[df['净值日期'] >= on_submit_date_obj]
            if future_trading_days.empty:
                print("没有找到有效的交易日数据。")
                return None
            if len(future_trading_days) >= n:
                next_trade_day = future_trading_days.iloc[n - 1]  # n-1，因为索引从0开始
                return next_trade_day['净值日期'].strftime("%Y-%m-%d"),next_trade_day['累计净值']
            else:
                print(f"只有 {len(future_trading_days)} 个交易日，无法找到第 {n} 个交易日。")
                return None
        except Exception as e:
            print(f"获取下一个交易日失败: {e}")
            return None
        
    def get_trading_day_critical(self, on_submit_date):
        """获取交易日的临界值：在则返回当天，不在则返回最近的过去交易日"""
        try:
            # 确保日期列和输入参数都是日期格式，防止字符串比较失效
            # 假设你的 df['date'] 已经是 datetime 类型
            
            # 筛选所有小于等于提交日期的行
            past_df = self.df[self.df['净值日期'] <= on_submit_date]
            if past_df.empty:
                print(f"警告: 日期 {on_submit_date} 之前没有任何交易数据")
                return None
            # 取最后一行（即最接近 on_submit_date 的那一天）
            critical_data = past_df.iloc[-1]
            return critical_data
        except Exception as e:
            print(f"获取临界交易日失败: {e}")
            return None
    
def reset_tracker():
    """重置追踪器，清空所有记录"""
    try:
        with open(transaction_confirmed_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        with open(transaction_onsubmit_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        print("追踪器已重置，所有记录已清空。")
    except Exception as e:
        print(f"重置追踪器失败: {e}")
        return


    


if __name__ == "__main__":
    tracker = virtual_tracker(code="501018",df=get_dataframe_by_path(r"A:\projects\money2\my_types\Qdii\501018.csv"),date="2026-01-14")
    
    #tracker.on_submit_transaction(buy_date="2026-01-14", buy_price=10000, sell_date=None, sell_nums=None, action="buy")
    # tracker.on_submit_transaction(buy_date=None, buy_price=None, sell_date="2026-01-14", sell_nums=2000, action="sell")
    # tracker.transaction_confirming(n=1)
    # print("我有",tracker.get_repository(),"份")
    reset_tracker()