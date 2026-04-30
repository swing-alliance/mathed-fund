from datetime import datetime,timedelta
from global_date_manager import date_mannager


class time_ticker():
    def __init__(self,d_m:date_mannager):
        self.d_m=d_m
        self.ranging_list=[]




    def is_ranging(self):
        """检查今天是否有任何待办任务"""
        current_time = self.d_m.get_date()
        return any(item[0] == current_time for item in self.ranging_list)
    

    def check_and_execute(self, brain_obj):
        """
        检查今天是否有任务，如果有则执行对应的 think_way。
        brain_obj: 实际包含这些方法的类实例
        """
        current_time = self.d_m.get_date()
        results = [] # 如果一天可能有多个任务，用列表装结果
        for item in self.ranging_list[:]:
            scheduled_date, think_way = item
            if current_time == scheduled_date:
                if hasattr(brain_obj, think_way):
                    func = getattr(brain_obj, think_way)
                    res = func() # 拿到方法执行后的返回值
                    results.append(res)
                self.ranging_list.remove(item)
        return results[0] if results else None
    


    def postphone_a_duty(self):
        """将最近添加（列表最后）的一个任务延后一天"""
        if not self.ranging_list:
            print("没有待办任务可以延后")
            return
        last_item = self.ranging_list[-1]
        old_date, think_way = last_item
        new_date = old_date + timedelta(days=1)
        if any(item[0] == new_date for item in self.ranging_list):
            print(f"延后失败：{new_date} 已经有其他任务了")
            return
        self.ranging_list[-1] = (new_date, think_way)
        print(f"任务已延后：从 {old_date} 移至 {new_date}")


    def set_alarm_clock_duty(self, days, think_way):
        """实际做任务的响应"""
        # 1. 计算触发时间
        current_time = self.d_m.get_date() 
        add_date = current_time + timedelta(days=days)
        self.ranging_list.append((add_date, think_way))

    def get_today_duty(self):
        """获取并返回今天待办任务"""
        current_time = self.d_m.get_date()
        # 筛选出日期匹配的任务名
        today_tasks = [item[1] for item in self.ranging_list if item[0] == current_time]
        today_task=today_tasks[0]
        return today_task
    
    def pending_duty(self):
        current_time = self.d_m.get_date()
        # 筛选出日期匹配的任务名
        pending_tasks = [item[1] for item in self.ranging_list if item[0] >= current_time]
        return  pending_tasks