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



current_path = Path(__file__).resolve()
target_dir = current_path.parent.parent / "my_types" / "Equity"

transaction_confirmed_path=os.path.join(os.getcwd(),'virtual_track',"virtual_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'virtual_track',"virtual_transaction_onsubmit.json")

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
        print(f"json读取失败严重错误: {e}")
        return {}


def w_json(path, data): # 将参数名 json 改为 data
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True # 执行成功返回 True 是个好习惯
    except Exception as e:
        print(f"json写回严重错误: {e}")
        return False

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



    
        
def pause(info):
    # 将变量直接嵌入字符串中
    input(f"\n程序已暂停, 暂停信息: {info}")



class global_virtual_tracker():
    def __init__(self,dfs,date,account:virtual_account):
        self.dfs=dfs
        self.account=account
        if isinstance(date, str):
            self.date = datetime.strptime(date, "%Y-%m-%d")
        else:
            self.date = date
    
    
    def global_transaction_submit(self,code,buy_date:str, buy_price, sell_date, sell_ratio,action):
        """提交"""
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
                w_json(transaction_onsubmit_path,transactions)
                print(f"买入记录已添加：{transaction_record}")
            except Exception as e:
                print(f"提交买入失败: {e}")
                return
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
                w_json(transaction_onsubmit_path,transactions)
                print(f"卖出记录已添加：{transaction_record}")
            except Exception as e:
                print(f"提交卖出失败: {e}")
                return

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
            confirmmed_data=r_json(transaction_confirmed_path)
            all_data=r_json(transaction_onsubmit_path)
            unchecked_list=self.get_unchecked_submits()
            for item in unchecked_list:
                submit_date=item[0]
                sumbit_id=item[1]
                detail=all_data[submit_date][sumbit_id]
                code=detail["code"]
                if detail["action"]=="buy":
                    avaliable_cash=self.account.get_balance()
                    if avaliable_cash<detail["buy_price"]:
                        print("哥们买不起")
                        all_data[submit_date][sumbit_id]["status"]="failed"
                    df=self.get_df(code)
                    if df is None or df.empty:
                        all_data[submit_date][sumbit_id]["status"]="failed"
                        raise ValueError("系统调用用于一天买入的确认时代码相对的df不存在，严重错误")
                    result = df[df['净值日期'] == submit_date]
                    if not result.empty:
                        single_value=result.iloc[0]['累计净值']
                        nums=detail["buy_price"]/single_value
                        self.account.decrease_cash(detail["buy_price"])
                        confirmmed_data[code]={"nums":nums}
                        all_data[submit_date][sumbit_id]["status"]="checked"
                        print("买入成功，账户已经转换为筹码")
                        continue
                    print(f"订单{sumbit_id},仍然unchecked")
                    continue
                if detail["action"]=="sell":
                    sell_code=detail["code"]
                    
                    sell_ratio=detail["sell_ratio"]
                    if sell_code not in confirmmed_data:
                        all_data[submit_date][sumbit_id]["status"]="failed"
                        print("卖出确认时发现未知记录,错误")
                        
                    df=self.get_df(code)
                    
                    if df is None or df.empty:
                        all_data[submit_date][sumbit_id]["status"]="failed"
                        raise ValueError("系统调用用于一天卖出的确认时代码相对的df不存在，严重错误")
                    result = df[df['净值日期'] == submit_date]
                    if not result.empty:
                        single_value=result.iloc[0]['累计净值']
                        nums=confirmmed_data[code]["nums"]
                        left_nums=nums*(1-sell_ratio)
                        confirmmed_data[code]["nums"]=left_nums
                        all_data[submit_date][sumbit_id]["status"]="checked"
                        return_value=(nums-left_nums)*single_value
                        self.account.increase_cash(return_value)
                        print("卖出成功，筹码变现回账户")
                        continue
                    print(f"订单{sumbit_id},仍然unchecked")
                    continue
            w_json(transaction_onsubmit_path,all_data)
            w_json(transaction_confirmed_path,confirmmed_data)
            print("一天的确认完成了")
        except Exception as e:
            print("系统调用用于一天的确认失败",e)











if __name__=="__main__":
    vc=virtual_account(1000)
    vt=global_virtual_tracker(dfs=get_dfs(target_dir),date=None,account=vc)
    # vt.global_transaction_submit(code=000011,buy_price=1000,buy_date="2024-09-14",sell_date=None,sell_nums=None,action="buy")
    # vt.global_transaction_submit(code=123545,buy_price=10500,buy_date="2024-09-25",sell_date=None,sell_nums=None,action="buy")
    vt.global_transaction_submit(code=1345,buy_price=None,buy_date=None,sell_date="2024-09-28",sell_ratio=1,action="sell")
    # vt.global_transaction_confirming()
    
