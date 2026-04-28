"""
这里是策略的决策中心,大脑每次醒来会通过观察dfs,全局账户,追踪器vt发出的环境和持仓,持仓盈亏情况快照，并通过追踪器，做出接下来的买和卖操作,小心追踪器bug,尽量提前定好,
系统禁止孤儿订单,所有提交的订单一定会出现在frozen,一定会冻结,且系统不允许回退订单,所有订单必须checked,大脑不要发出不存在的订单
卖单只能在交易日才能发出，如果提交的当天没有净值，将无法创建卖单,所以需要做交易日检查
所有资金要么在浮动仓库随净值波动，要么在冻结中，要么在账户下的现金中
"""
import random
from datetime import datetime
from global_virtual_tracker import global_virtual_tracker
from global_virtual_brain_support import fund_mannager
from virtual_account import virtual_account
from global_date_manager import date_mannager


class global_brain():
    def __init__(self,dfs:dict,vt:global_virtual_tracker,account:virtual_account,date_mannager:date_mannager):
        self.awake=True 
        self.d_m=date_mannager
        self.dfs=dfs
        self.vt=vt
        self.account=account
        self.fund_mannager=fund_mannager(self.dfs,self.d_m)


    def check_trade_day(self):
        return self.fund_mannager.is_trade_day()


        
    def isawake(self):
        return self.awake
    
    def go_bed(self):
        self.awake=False

    def brain_check_date(self):
        """大脑返回当前的日期"""
        return str(self.d_m.get_date())[:10]
    
    
    def brain_buy(self,code,buy_cash):
        """创建买单"""
        try:
            self.vt.global_transaction_submit(code,self.d_m.get_date(),buy_cash,None,None,"buy",0)
        except Exception as e:
            raise RuntimeError("自动大脑构建买入失败，检查大脑设计",e)

    def brain_sell(self,code,sell_ratio):
        """创建卖单,自动构建t"""
        try:
            t=self.fund_mannager.get_selltime_t(code)
            self.vt.global_transaction_submit(code,None,None,self.d_m.get_date(),sell_ratio,"sell",t=t)
        except Exception as e:
            raise("自动大脑构建卖出失败，检查大脑设计",e)
        
    def brain_peek_all_value(self):
        """大脑生成此刻的所有价值快照,包括浮动仓库，冻结的，账户上的"""
        try:
            frozen_cash=self.vt.freeze_tracker.get_all_frozen()
            cash=self.account.get_balance()
            all_holding_p=self.vt.portfolio_tracker.get_all_holding_p()
            holding_p_value=0
            total_v=0
            if all_holding_p:
                for code in all_holding_p:
                    num=self.vt.portfolio_tracker.get_a_portfolio_nums(code)
                    value=self.fund_mannager.check_fund_value(code=code)
                    p_v=num*value
                    holding_p_value+=p_v
            total_v=holding_p_value+cash+frozen_cash
            return total_v
        except Exception as e:
            raise("自动大脑构建全部价值快照失败，检查大脑设计",e)
        
    def brain_peek_p_value(self):
        """大脑生成此刻的仓库浮动价值快照"""
        try:
            all_holding_p=self.vt.portfolio_tracker.get_all_holding_p()
            holding_p_value=0
            if all_holding_p:
                for code in all_holding_p:
                    num=self.vt.portfolio_tracker.get_a_portfolio_nums(code)
                    value=self.fund_mannager.check_fund_value(code=code)
                    total_v=num*value
                    holding_p_value+=total_v
            return holding_p_value
        except Exception as e:
            raise(f"自动大脑构建浮动仓库价值快照失败，检查大脑设计{e}")
        
    def brain_peek_account_value(self):
        """大脑生成当前账户现金的快照"""
        try:
            holding_cash_value=self.account.get_balance()
            return holding_cash_value
        except Exception as e:
            raise(f"自动大脑生成当前账户现金的快照失败，检查大脑设计{e}")
        
    def brain_peek_frozen_value(self):
        """大脑生成当前冻结资金的快照"""
        try:
            frozen_cash=self.vt.freeze_tracker.get_all_frozen()
            return frozen_cash
        except Exception as e:
            raise(f"自动大脑生成当前冻结资金的快照失败，检查大脑设计{e}")
        

    

    def think(self):
        print(f"{str(self.d_m.get_date())[:10]}三点前","大脑思考日期")
        
        if not self.check_trade_day() and self.isawake():
            return
        print("大脑说仓库价值",self.brain_peek_p_value())
        if self.brain_peek_p_value()<=1000:
            all_df_name=[]
            # holding_portfolio=self.vt.portfolio_tracker.get_all_holding_p()
            self.brain_buy("018957",9000)
            account_cash=self.vt.account.get_balance()
            for name,df in self.dfs.items():
                if not df.empty:
                    all_df_name.append(name)
            every_count=account_cash/5
            for i in range(5):
                name=random.choice(all_df_name)
                self.brain_buy(name,every_count)
        if self.brain_peek_all_value()>=13000:
            all_holding_p=self.vt.portfolio_tracker.get_all_holding_p()
            for p in all_holding_p:
                self.brain_sell(p,1,3)
            print("大脑休眠")
            self.go_bed()


                








