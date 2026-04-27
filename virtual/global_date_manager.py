from datetime import datetime, timedelta

class date_mannager:
    def __init__(self, init_date):
        # 增加保险：如果传进来的是字符串，自动转为 datetime
        if isinstance(init_date, str):
            self.current_date = datetime.strptime(init_date, "%Y-%m-%d")
        else:
            self.current_date = init_date

    def daypass(self):
        self.current_date += timedelta(days=1)
    
    def get_date(self):
        return self.current_date