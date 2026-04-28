"""
这里是系统核心追踪器的实现，通过追踪器卖和买，通过追踪器实现对冻结资金的控制模拟和基金持仓的浮动价值追踪
"""
import json
import os
from datetime import datetime
import pandas as pd
from virtual_account import virtual_account

from virtual_df_split import get_dataframe_by_path,split_dataframe
from pathlib import Path
import secrets
import string
from datetime import datetime
def generate_order_id(length=10):
    # 包含大写字母和数字
    characters = string.ascii_uppercase + string.digits
    # 使用 secrets 模块比 random 更安全
    return ''.join(secrets.choice(characters) for _ in range(length))

#所有买入卖出申请随时间都要checked，发现随时间uncheck或者failed属于严重问题

current_path = Path(__file__).resolve()
target_dir = current_path.parent.parent / "my_types" / "Equity"

transaction_confirmed_path=os.path.join(os.getcwd(),'virtual_track',"virtual_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'virtual_track',"virtual_transaction_onsubmit.json")
frozen_cash_path=os.path.join(os.getcwd(),'virtual_track',"virtual_frozen.json")

def r_json(path):
    try:
        # 1. 检查文件是否存在，不存在直接返回空字典
        if not os.path.exists(path):
            return {}
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # 2. 如果文件是空的，返回空字典，否则解析 JSON
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"路径 {path} 下的 JSON 格式损坏")
        return {}
    except Exception as e:
        raise(e)

def w_json(path, data): # 将参数名 json 改为 data
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True # 执行成功返回 True 是个好习惯
    except Exception as e:
        print(f"json写回严重错误: {e}")
        raise(e)
        

def get_dfs(target_dir):
    try:
        names=os.listdir(target_dir)
        dfs={}
        for name in names:
            df=get_dataframe_by_path(os.path.join(target_dir,name))
            name=name.split(".")[0]
            dfs[name]=df
        return dfs
    except Exception as e:
        print("加载dfs出错",e)

# "2025-10-02": {
#         "HU5B6Q6QY5": {
#             "action": "buy",
#             "code": "000061",
#             "buy_price": 900.0,
#             "status": "checked"
#         }
#     },

    
        
def pause(info):
    # 将变量直接嵌入字符串中
    input(f"\n程序: {info}")



class global_virtual_tracker():
    """用于仓库追踪和冻结追踪的整个控制"""
    def __init__(self,dfs,date,account:virtual_account):
        self.dfs=dfs
        self.portfolio_tracker=global_Portfolio_tracker()
        self.account=account
        self.freeze_tracker=global_frozen_cash_tracker(self.account)
        
        if isinstance(date, str):
            self.date = datetime.strptime(date, "%Y-%m-%d")
        else:
            self.date = date
    
    
    def global_transaction_submit(self,code,buy_date:str, buy_price, sell_date, sell_ratio,action,t):
        """提交按照code,buy_price, sell_date, sell_ratio,action,t,其中t代表此交易会冻结多久"""
        order_id = generate_order_id()
        if action == "buy":
            try:
                buy_date =str(buy_date)[:10]#切片[:10]可以保留日期部分，去掉时间部分
                submit_buy_price = buy_price
                if not os.path.exists(transaction_onsubmit_path):
                    with open(transaction_onsubmit_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=4)
                transactions=r_json(transaction_onsubmit_path)
                if buy_date not in transactions:
                    transactions[buy_date] = {}
                transaction_record = {
                "action":"buy",
                "code":code,
                "buy_price": submit_buy_price,
                "status":"unchecked"
                }
                transactions[buy_date][order_id]=(transaction_record)
                self.freeze_tracker.create_freeze_cash(order_id,submit_buy_price,t=0)
                w_json(transaction_onsubmit_path,transactions)
                print(f"买入申请记录已添加：{transaction_record}")
            except Exception as e:
                raise RuntimeError(f"提交买入失败: {e}")
        if action == "sell":
            try:
                sell_date =str(sell_date)[:10]  
                transactions=r_json(transaction_onsubmit_path)
                if sell_date not in transactions:
                    transactions[sell_date] = {}
                if sell_date in transactions:
                    transaction_record = {
                        "action":"sell",
                        "code": code,
                        "sell_ratio": sell_ratio,
                        "status":"unchecked"
                    }
                    transactions[sell_date][order_id]=(transaction_record)
                try:
                    confirm_date,confirm_single_value=self.find_to_confirm_dayinfo(code=code,submit_date=sell_date)
                    confirm_date = str(confirm_date)[:10]
                    left_nums=self.portfolio_tracker.get_a_portfolio_nums(code=code)
                    cut_nums=left_nums*sell_ratio
                    freeze_cash=cut_nums*confirm_single_value
                
                    if freeze_cash==0:
                        print("检查大脑或逻辑,试图卖出冻结为零")
                    self.portfolio_tracker.create_p(code,confirm_date,confirm_single_value,cut_nums,"sell")
                    self.freeze_tracker.create_return_freeze_cash(order_id,freeze_cash,t=t)
                except Exception as e:
                    raise RuntimeError(f"卖出提交的行情原子化错误: {e}")
                w_json(transaction_onsubmit_path,transactions)
                print(f"卖出申请记录已添加：{transaction_record},账户资金已经冻结")
            except Exception as e:
                raise RuntimeError(f"提交卖出失败: {e}")
                

    def get_unchecked_submits(self):
        """获取所有未检查的记录"""
        try:
            data=r_json(transaction_onsubmit_path)
            returnlist=[]#返回元祖，通过元组直接得到具体的
            for date, orders in data.items():
                for order_id, detail in orders.items():
                    if detail["status"]=="unchecked":
                        return_v=(date,order_id)
                        returnlist.append(return_v)
            return returnlist
        except Exception as e:
            print("获取所有未检查的记录错误",e)

    def get_df(self, code):
        try:
            # 1. 检查 code 是否在字典里
            if code not in self.dfs:
                print(f"追踪器：错误: dfs 字典里找不到代码 {code}")
                return None
            df = self.dfs[code].copy() # 使用 copy 防止修改原始数据
            
            # 2. 统一列名：确认你的原始列名到底是 'date' 还是 '净值日期'
            target_col = 'date' if 'date' in df.columns else '净值日期'
            
            df['净值日期'] = pd.to_datetime(df[target_col])
            df = df.sort_values(by='净值日期', ascending=True).reset_index(drop=True)
            return df
            
        except Exception as e:
            import traceback
            print(f"追踪器：获取并清洗代码 {code} 时崩溃:")
            traceback.print_exc() # 这行能告诉你到底是哪一行、因为什么报错
            return None




    
    def global_transaction_confirming(self):
        """系统调用用于一天的确认进程"""
        try:
            all_data=r_json(transaction_onsubmit_path)
            unchecked_list=self.get_unchecked_submits()
            for item in unchecked_list:
                submit_date=item[0]
                submit_id=item[1]
                detail=all_data[submit_date][submit_id]
                code=detail["code"]
                if detail["action"]=="buy":#主要追踪器执行买入确认
                    buy_price=detail["buy_price"]
                    
                    if self.freeze_tracker.check_frozen(submit_id) and self.find_to_confirm_dayinfo(code=code,submit_date=submit_date):#这里会自己解冻一天
                        try:
                            print("开始尝试原子化确认买入")
                            confirm_date,confirm_single_value=self.find_to_confirm_dayinfo(code=code,submit_date=submit_date)
                            confirm_date = str(confirm_date)[:10]
                            buy_amount=buy_price/confirm_single_value
                            self.freeze_tracker.de_frozen(submit_id)
                            self.portfolio_tracker.create_p(code,confirm_date,confirm_single_value,nums=buy_amount,action="buy")
                            all_data[submit_date][submit_id]["status"]="checked"
                            print("买入原子化确认成功")
                            continue
                        except Exception as e:
                            raise RuntimeError(f"买入确认原子化失败{e}")
                    print(f"订单{submit_id},仍然unchecked")
                    all_data[submit_date][submit_id]["status"]="unchecked"
                    continue
                if detail["action"]=="sell":#主要追踪器执行卖出确认
                    if self.freeze_tracker.check_frozen(submit_id) and self.find_to_confirm_dayinfo(code=code,submit_date=submit_date):#这里会自己解冻一天,如果已经冻上了就减去一天
                        try:
                            print("开始尝试原子化确认卖出")
                            
                            self.freeze_tracker.de_frozen(submit_id)
                            to_account_cash=self.freeze_tracker.get_amount_info(submit_id)
                            self.account.increase_cash(to_account_cash)
                            all_data[submit_date][submit_id]["status"]="checked"
                            print("卖出原子化确认成功")
                            continue
                        except Exception as e:
                            raise RuntimeError(f"卖出确认原子化失败: {e}")
                    continue
            w_json(transaction_onsubmit_path,all_data)
           
            print("一天的确认完成了")
        except Exception as e:
            print("系统调用用于一天的确认失败",e)


    def find_to_confirm_dayinfo(self, code, submit_date):
        """行情查询方法，向后"""
        try:
            df = self.get_df(code)
            if df is None or df.empty:
                raise ValueError("代码对应的df不存在")
            # 确保日期格式一致（建议统一转为 pd.to_datetime）
            result = df[df['净值日期'] >= submit_date]  
            if result.empty:
                raise ValueError(f"行情数据尚未覆盖到日期: {submit_date}")
            single_value = result.iloc[0]['累计净值']
            confirm_date = result.iloc[0]["净值日期"]
            return confirm_date, single_value
            
        except Exception as e:
            # 这里一定要 raise，外层才能抓到具体的错误信息
            raise RuntimeError(f"向后行情查询失败,尝试下次再卖: {e},关于{code}的报错")

class global_Portfolio_tracker():
    """直接仓位管理，最基本的code:{action:buy/sell,confirm_date:date,confirm_value=value,operate_nums,left_nums}"""
    def __init__(self):
        self.c_p_path=transaction_confirmed_path

    def create_p(self,code,confirm_date,confirm_single_value,nums,action):
        """创建仓库和仓库管理的关键方法"""
        try:
            p_info=r_json(self.c_p_path)
            if action == "buy":
                left_nums=self.get_a_portfolio_nums(code)
                left_nums+=nums
                if code not in p_info:
                    p_info[code]=[]
                single_record={
                    "confirm_date":confirm_date,
                    "confirm_single_value":confirm_single_value,
                    "operate_nums":nums,
                    "left_nums":left_nums,
                    "action":"buy"
                }
                p_info[code].append(single_record)
                w_json(self.c_p_path,p_info)
                return True
            if action =="sell":
                left_nums=self.get_a_portfolio_nums(code)
                left_nums-=nums
                if left_nums<0:
                    raise ValueError("严重错误，卖出后为负数")
                if code not in p_info:
                    raise ValueError("严重错误，代码没有任何相关交易却尝试确认卖出")
                single_record={
                    "confirm_date":confirm_date,
                    "confirm_single_value":confirm_single_value,
                    "operate_nums":-nums,
                    "left_nums":left_nums,
                    "action":"sell"
                }
                p_info[code].append(single_record)
                w_json(self.c_p_path,p_info)
                return True
        except Exception as e:
            print("创建持仓时严重错误",e)
            raise (e)
        

    def get_a_portfolio_nums(self,code):
        """获取目前代码最终剩余数量"""
        try:
            p_info=r_json(self.c_p_path)
            if code not in p_info:
                return 0
            last_item=p_info[code][-1]
            return last_item["left_nums"]
        except Exception as e:
            raise RuntimeError(f"获取目前代码{code}最终剩余数量严重错误",e)

    
    
    def get_all_holding_p(self):
        """获取所有目前持仓不为0的代码返回"""
        try:
            list=[]
            p_info=r_json(self.c_p_path)
            for code,data in p_info.items():
                last_data=data[-1]
                if last_data["left_nums"]>0:
                    list.append(code)
            return list
        except Exception as e:
            raise RuntimeError(f"获取所有目前持仓不为0的代码返回",e)
        
    # def find_to_confirm_dayinfo(self, code, submit_date):
    #     """行情查询方法,向前"""
    #     try:
    #         df = self.get_df(code)
    #         if df is None or df.empty:
    #             raise ValueError("代码对应的df不存在")
    #         # 确保日期格式一致（建议统一转为 pd.to_datetime）
    #         result = df[df['净值日期'] <= submit_date]  
    #         if result.empty:
    #             raise ValueError(f"行情数据尚未覆盖到日期: {submit_date}")
    #         single_value = result.iloc[-1]['累计净值']
    #         confirm_date = result.iloc[-1]["净值日期"]
    #         return confirm_date, single_value
    #     except Exception as e:
    #         # 这里一定要 raise，外层才能抓到具体的错误信息
    #         raise RuntimeError(f"行情查询失败,尝试下次再卖: {e}")
    
    # def get_one_holind_p_value(self,code,submit_date):
    


class global_frozen_cash_tracker():
    def __init__(self,account:virtual_account):
        """格式freeze_info[submit_id] = {
                    "amount": amount,
                    "action": "buy",
                    "status": "frozen",
                    "t": t}冻结追踪是持仓仓库和现金账户的媒介"""
        self.account=account
        self.freezen_amount=0

    def create_freeze_cash(self, submit_id, amount, t=0):
        """面向账户冻结, 发生在买入提交"""
        try:
            # 1. 尝试扣款
            if not self.account.decrease_cash(amount):#已经执行扣款
                print(f"扣款失败：余额不足。ID: {submit_id}")
                return False
            try:
                freeze_info = r_json(frozen_cash_path)
                freeze_info[submit_id] = {
                    "amount": amount,
                    "action": "buy",
                    "status": "frozen",
                    "t": t
                }
                w_json(frozen_cash_path, freeze_info)
                return True 
            except Exception as file_error:
                print(f"致命错误：记录冻结信息失败，执行资金回滚。{file_error}")
                self.account.increase_cash(amount) # 假设你有增加余额的方法
                return False
        except Exception as e:
            print(f"账户冻结流程发生未知错误: {e}")
            return False
        
    def create_return_freeze_cash(self,submit_id,amount,t=0):
        "面向持仓，创建持仓回款冻结，发生在卖出提交"
        try:
            freeze_info = r_json(frozen_cash_path)
            freeze_info[submit_id] = {
                "amount": amount,
                "action": "sell",
                "status": "frozen",
                "t": t
            }
            w_json(frozen_cash_path, freeze_info)
            return True 
        except Exception as file_error:
            raise(f"致命错误：持仓回款冻结流程失败。{file_error}")



    def check_frozen(self,submit_id):
        "检查封印的是否解冻"
        try:
            freeze_info=r_json(frozen_cash_path)
            if freeze_info[submit_id]["t"]==0:
                w_json(frozen_cash_path, freeze_info)
                return True
            else:
                freeze_info[submit_id]["t"]-=1
                w_json(frozen_cash_path, freeze_info)
                return False
        except Exception as e:
            print("检查封印的是否解冻时严重错误",e)
            return False
        
    def de_frozen(self,submit_id):
        """解冻逻辑"""
        try:
            freeze_info=r_json(frozen_cash_path)
            if freeze_info[submit_id]["status"]=="frozen" and freeze_info[submit_id]["t"]==0:
                if freeze_info[submit_id]["action"]=="buy":
                    freeze_info[submit_id]["status"]="unfreeze"
                    w_json(frozen_cash_path, freeze_info)
                    return True
                if freeze_info[submit_id]["action"]=="sell" and freeze_info[submit_id]["t"]==0:
                    freeze_info[submit_id]["status"]="unfreeze"
                    w_json(frozen_cash_path, freeze_info)
                    return True
            return False
        except Exception as e:
            raise RuntimeError(f"解冻时严重错误{e}")
    
    def get_amount_info(self, submit_id):
        """
        根据平铺结构的 JSON 获取金额,仅仅在卖出确认时调用
        数据结构示例: {"56ICDK5KZV": {"amount": 9866.14, "action": "sell", ...}}
        """
        try:
            freeze_info = r_json(frozen_cash_path)
            if submit_id in freeze_info:
                order_detail = freeze_info[submit_id]
                # 校验是否为卖出回款
                if order_detail.get("action") == "sell":
                    return float(order_detail["amount"])
                else:
                    raise ValueError(f"订单 {submit_id} 的动作为 {order_detail.get('action')}，非卖出回款")
            raise ValueError(f"未找到订单 ID: {submit_id}")
        except Exception as e:
            raise RuntimeError(f"获取金额失败: {e}")
        
    def get_goout_frozen(self):
        """获取所有从账户飞到持仓冻结的,只读"""
        try:
            freeze_info = r_json(frozen_cash_path)
            total_amount = sum(item['amount'] for item in freeze_info.values() 
                   if item.get('status') == 'freeze' and item.get('action') == 'buy')
            return total_amount
        except Exception as e:
            raise(f"获取获取所有从账户飞到持仓冻结的严重失败,{e}")

    def get_goin_frozen(self):
        """获取所有从持仓飞回账户冻结的,只读"""
        try:
            freeze_info = r_json(frozen_cash_path)
            total_amount = sum(item['amount'] for item in freeze_info.values() 
                   if item.get('status') == 'freeze' and item.get('action') == 'sell')
            return total_amount
        except Exception as e:
            raise(f"获取所有从持仓飞回账户冻结的严重失败,{e}")
    
    def get_all_frozen(self):
        """获取所有冻结的,只读"""
        try:
            freeze_info = r_json(frozen_cash_path)
            total_amount = sum(item['amount'] for item in freeze_info.values() 
                   if item.get('status') == 'freeze')
            return total_amount
        except Exception as e:
            raise(f"获获取所有冻结的严重失败,{e}")


def reset_tracker():
    """重置追踪器，清空所有记录"""
    try:
        with open(transaction_confirmed_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        with open(transaction_onsubmit_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        with open(frozen_cash_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        print("追踪器已重置，所有记录已清空")
    except Exception as e:
        print(f"重置追踪器失败: {e}")
        return



if __name__=="__main__":
    reset_tracker()
    vc=virtual_account(10000)
    vt=global_virtual_tracker(dfs=get_dfs(target_dir),date=None,account=vc)
    vt.global_transaction_submit(code="000011",buy_price=1000,buy_date="2024-09-14",sell_date=None,sell_ratio=None,action="buy")
    # vt.global_transaction_submit(code=123545,buy_price=10500,buy_date="2024-09-25",sell_date=None,sell_ratio=None,action="buy")
    #vt.global_transaction_submit(code=1345,buy_price=None,buy_date=None,sell_date="2024-09-28",sell_ratio=1,action="sell")
    pause(f"{vt.account.get_balance()}")
    vt.global_transaction_confirming()
    pause(f"{vt.account.get_balance()}")
    vt.global_transaction_submit(code="000011",buy_price=1000,buy_date="2024-09-15",sell_date=None,sell_ratio=None,action="buy")
    pause(f"{vt.account.get_balance()}")
    vt.global_transaction_confirming()
    pause(f"{vt.account.get_balance()}")
    vt.global_transaction_submit(code="000011",buy_price=1000,buy_date="2024-09-17",sell_date=None,sell_ratio=None,action="buy")
    pause(f"{vt.account.get_balance()}")

    # vt.global_transaction_confirming()
    
