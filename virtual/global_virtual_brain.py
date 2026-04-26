#这里是策略的决策中心，大脑每次醒来会观察dfs环境和持仓，持仓盈亏情况，并通过追踪器，做出接下来的买和卖操作
import random
from datetime import datetime

class global_brain():
    def __init__(self,dfs:dict,vt,date:datetime):
        self.awake=True
        self.date=date
        self.dfs=dfs
        self.vt=vt
        
    def isawake(self):
        return self.awake
    

    def go_bed(self):
        self.awake=False

    def think(self):
        all_df_name=[]
        # holding_portfolio=self.vt.portfolio_tracker.get_all_holding_p()
        account_cash=self.vt.account.get_balance()
        for name,df in self.dfs.items():
            if not df.empty:
                # 只有不为空时才打印或处理最后一行
                last_row = df.iloc[-1]
                print(f"鸡 {name} 的最新数据：\n{last_row}")
                all_df_name.append(name)
        every_count=account_cash/5
        for i in range(5):
            name=random.choice(all_df_name)
            self.vt.global_transaction_submit(name,self.date,every_count,None,None,"buy",0)
        self.go_bed()
                








