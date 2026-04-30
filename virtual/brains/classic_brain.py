""""
经典的动量追涨模型，全仓单调一只基金，如果a股熊市则全仓单调最强的全球市场,否则单调a股中最强，每22天调整持仓，
回测后发现在a股板块轮动时，容易冲高回落，反复挨打，测率稳定性差,受进场时间影响大,如果在牛市末期进会陷入漫长回本路,熊市末期进入，一开始就能表现良好,但长期会概率收敛，两年后收益率近似
"""

from global_time_ticker import time_ticker
from datetime import datetime
from global_virtual_tracker import global_virtual_tracker
from global_virtual_brain_support import fund_mannager
from virtual_account import virtual_account
from global_date_manager import date_mannager


class global_brain():
    def __init__(self,dfs:dict,vt:global_virtual_tracker,account:virtual_account,date_mannager:date_mannager):
        self.awake=True 
        self.d_m=date_mannager
        self.time_ticker=time_ticker(self.d_m)
        self.dfs=dfs
        self.vt=vt
        self.account=account
        self.fund_mannager=fund_mannager(self.dfs,self.d_m)
        self.rang_called_times=0


    def check_trade_day(self):
        return self.fund_mannager.is_trade_day()


    def rang_wake_up(self):
        if self.time_ticker.is_ranging():
            self.awake=True
            return True
        return False

        
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
            raise RuntimeError("自动大脑构建卖出失败，检查大脑设计",e)
        
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
                    value=self.fund_mannager.check_fund_value_former(code=code)
                    p_v=num*value
                    holding_p_value+=p_v
            total_v=holding_p_value+cash+frozen_cash
            return round(total_v, 8)
        except Exception as e:
            raise RuntimeError("自动大脑构建全部价值快照失败，检查大脑设计",e)
        
    def brain_peek_p_value(self):
        """大脑生成此刻的仓库浮动价值快照"""
        try:
            all_holding_p=self.vt.portfolio_tracker.get_all_holding_p()
            holding_p_value=0
            if all_holding_p:
                for code in all_holding_p:
                    num=self.vt.portfolio_tracker.get_a_portfolio_nums(code)
                    value=self.fund_mannager.check_fund_value_former(code=code)
                    total_v=num*value
                    holding_p_value+=total_v
            return round(holding_p_value, 8)
        except Exception as e:
            raise RuntimeError(f"自动大脑构建浮动仓库价值快照失败，检查大脑设计{e}")
        
    def brain_peek_holding_ps(self):
        """查找所有持仓不为0的基金代码"""
        return self.vt.portfolio_tracker.get_all_holding_p()

        
    def brain_peek_account_value(self):
        """大脑生成当前账户现金的快照"""
        try:
            holding_cash_value=self.account.get_balance()
            return round(holding_cash_value, 8)
        except Exception as e:
            raise RuntimeError(f"自动大脑生成当前账户现金的快照失败，检查大脑设计{e}")
        
    def brain_peek_frozen_value(self):
        """大脑生成当前冻结资金的快照"""
        try:
            frozen_cash=self.vt.freeze_tracker.get_all_frozen()
            return round(frozen_cash,8)
        except Exception as e:
            raise RuntimeError(f"自动大脑生成当前冻结资金的快照失败，检查大脑设计{e}")
        

    def brief_think(self):
        """外层系统事件循环调用"""
        if self.rang_called_times==0 and self.check_trade_day():
            """"执行初试化思考"""
            self.rang_called_times+=1
            self.time_ticker.set_alarm_clock_duty(22,"think_selling_all")
            self.init_deep_think()
            return
        if self.rang_wake_up() and not self.check_trade_day():
            """如果闹钟响了但是不是交易日，任务延期"""
            self.time_ticker.postphone_a_duty()
            return
        if self.rang_wake_up() and self.check_trade_day():
            try:
                if self.time_ticker.get_today_duty()=="think_selling_all":
                    result=self.time_ticker.check_and_execute(self)
                    print("卖出决定下一次任务",result)
                    if result is not None:
                        self.time_ticker.set_alarm_clock_duty(result,"init_deep_think")
                        return
                    else:
                        self.time_ticker.set_alarm_clock_duty(22,"think_selling_all")
                        return
                elif self.time_ticker.get_today_duty()=="init_deep_think":
                    result=self.time_ticker.check_and_execute(self)
                    self.time_ticker.set_alarm_clock_duty(result,"think_selling_all")
                    return
                print("what the fuck?")
                return

            except Exception as e:
                self.time_ticker.postphone_a_duty()
                print("闹钟执行任务挫败,尝试延期")
                # raise RuntimeError(f"闹钟执行任务挫败{e}")

    

    def think_selling_all(self):
        isbear=self.fund_mannager.check_bear(120)
        if not isbear:
            best_code=next(iter(self.fund_mannager.get_sorted_sharpe_return_dict(60)))
            holding_ps=self.brain_peek_holding_ps()
            if best_code in holding_ps:
                return None
            self.brain_sell(holding_ps[0],1)
            sell_t=self.fund_mannager.get_selltime_t(holding_ps[0])
            return sell_t+1
        else:
            best_code=next(iter(self.fund_mannager.get_sorted_sharpe_return_dict(60)))
            holding_ps=self.brain_peek_holding_ps()
            if best_code in holding_ps:
                return None
            self.brain_sell(holding_ps[0],1)
            sell_t=self.fund_mannager.get_selltime_t(holding_ps[0])
            return sell_t+1


    def init_deep_think(self):
        """初始化思考"""
        isbear=self.fund_mannager.check_bear(30)
        if isbear:
            best_code_dict=self.fund_mannager.get_sorted_sharpe_return_dict(60)
            for code in best_code_dict.keys():
                t=self.fund_mannager.get_selltime_t(code)
                if t>4:
                    self.brain_buy(code,self.brain_peek_account_value())
                    break
            return 22
        else:
            best_code=next(iter(self.fund_mannager.get_sorted_sharpe_return_dict(60)))
            self.brain_buy(best_code,self.brain_peek_account_value())
            return 22

            

            
        
        


                








