import os

transaction_confirmed_path=os.path.join(os.getcwd(),'virtual_track',"virtual_confirmed.json")
transaction_onsubmit_path=os.path.join(os.getcwd(),'virtual_track',"virtual_transaction_onsubmit.json")
base_path = r"A:\projects\money2\my_types\Qdii"
class virtual_account:
    """虚拟账户类，模拟资金的增减"""
    def __init__(self, initial_cash=0):
        self.cash = initial_cash

    def increase_cash(self, amount):
        """增加现金"""
        if amount is not None:
            self.cash += amount

    def decrease_cash(self, amount):
        """减少现金"""
        print(f"尝试减少现金: {amount}, 当前余额: {self.cash}")
        if amount is not None:
            cash=self.cash-amount
            if cash<0:
                print("现金不足，无法完成操作")
                return False
            self.cash = cash
            return True
        print("尝试账户扣款数量为零，已经失败")
        return False

    def get_balance(self):
        """获取当前余额"""
        return self.cash
    
    

    
if __name__ == "__main__":
    pass