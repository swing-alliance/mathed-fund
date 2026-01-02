"""用于记录 Top 100 名单"""
import os
import time
import json
log_path = os.path.join(os.getcwd(), 'log','log100.json')
today = time.strftime('%Y-%m-%d', time.localtime(time.time()))

def save_to_log(namelist):
    """用于记录 Top 100 名单,同时保证文件不超过30条"""
    try:
        data = {}
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        length = len(data)
        while(length >= 30):
            first_key = next(iter(data))
            del data[first_key]
            length = len(data)
        last_value=list(data.values())[-1]
        if last_value == namelist:
            return
        data[today] = namelist 
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"成功记录 {today} 的 Top {len(namelist)} 名单")
    except Exception as e:
        print("{e}")
        pass
