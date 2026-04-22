import akshare as ak
import json
import os
from datetime import date,timedelta,datetime
import pandas as pd

transaction_confirmed_path=os.path.join(os.getcwd(),'virtual_track',"virtual_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'virtual_track',"virtual_transaction_onsubmit.json")


class virtual_tracker:
    """虚拟化追踪完整的交易过程"""
    def __init__(self, code=None, transaction_confirmed_path=transaction_confirmed_path, transaction_onsubmit_path=transaction_onsubmit_path):
      self.code = code
      self.transaction_confirmed_path = transaction_confirmed_path
      self.transaction_onsubmit_path = transaction_onsubmit_path
      self.today_date = date.today().strftime('%Y-%m-%d')
    def on_submit_transaction(self, buy_date, buy_price, sell_date, sell_nums,action):
        if action == "buy":
            try:
                self.buy_date =buy_date or self.today_date
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
                transaction_record = {
                "buy_date": self.buy_date,
                "buy_price": self.buy_price,
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
                self.sell_date =sell_date or self.today_date
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
                print(f"卖出记录已添加：{transactions[self.code][-1]}")
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
                                        confirm_result= get_next_trading_day(on_submit_date=buy_date, code=str(self.code),n=n)
                                        if confirm_result is None:
                                            print("无法获取下一个交易日")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                            print(f"下一个交易日：{next_trading_day}, 单位净值：{single_value}")
                                        record = {
                                            "buy_price": buy_price,
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
                                        transaction["status"] = "checked"
                                    elif "sell_nums" in transaction:#卖出
                                        sell_nums = transaction["sell_nums"]
                                        sell_date = transaction["sell_date"]
                                        confirm_result= get_next_trading_day(on_submit_date=sell_date, code=str(self.code),n=n-1)
                                        if confirm_result is None:
                                            print("无法获取下一个交易日")
                                            continue
                                        else:
                                            next_trading_day, single_value = confirm_result
                                            total_nums=self.get_repository()
                                            if total_nums<sell_nums:
                                                print("仓库数量不足,不执行卖出操作")
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
                                        transaction["status"] = "checked"
                                except Exception as e:
                                    print(f"最后买入确认失败: {e}")
                                    return
                            else:
                                continue
                with open(self.transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                    json.dump(onsubmit_data, f, ensure_ascii=False, indent=4)
                
            print("交易确认成功！")
        except Exception as e:
            print(f"买入确认失败: {e}")
            return

    def get_repository(self):
        """获取仓库目前的数量"""
        try:
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
        
    def export_confirmed_transactions(self):
        """导出已确认的交易记录"""
        try:
            with open(self.transaction_confirmed_path, 'r', encoding='utf-8') as f:
                confirmed_data = json.load(f)
                return confirmed_data.get(self.code, [])
        except Exception as e:
            print(f"导出已确认交易记录失败: {e}")
            return []


def get_next_trading_day(on_submit_date, code, n=1):
    """返回 on_submit_date 后的第 n 个交易日"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'], format="%Y-%m-%d")
        on_submit_date_obj = datetime.strptime(on_submit_date, "%Y-%m-%d")
        future_trading_days = df[df['净值日期'] > on_submit_date_obj]
        if future_trading_days.empty:
            print("没有找到有效的交易日数据。")
            return None
        if len(future_trading_days) >= n:
            next_trade_day = future_trading_days.iloc[n - 1]  # n-1，因为索引从0开始
            return next_trade_day['净值日期'].strftime("%Y-%m-%d"),next_trade_day['单位净值']
        else:
            print(f"只有 {len(future_trading_days)} 个交易日，无法找到第 {n} 个交易日。")
            return None
    except Exception as e:
        print(f"获取下一个交易日失败: {e}")
        return None
    


if __name__ == "__main__":
    tracker = virtual_tracker(code="501018")
    
    # tracker.on_submit_transaction(buy_date="2025-06-15", buy_price=10000, sell_date=None, sell_nums=None, action="buy")
    tracker.on_submit_transaction(buy_date=None, buy_price=None, sell_date="2025-06-20", sell_nums=1.8819292201733333, action="sell")
    tracker.transaction_confirming(n=1)
    print("我有",tracker.get_repository(),"份")