import os
import json
from PyQt5.QtCore import QThread, pyqtSignal


def get_config():
    """拿到config.json"""
    config_path=os.path.join(os.getcwd(), "config",'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def write_config(config):
    """写入config.json"""
    config_path=os.path.join(os.getcwd(), "config",'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f)
def get_proxy_config():
    """拿到config.json中的proxy配置"""
    try:
        config_path=os.path.join(os.getcwd(), "config",'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            proxy_config=config["proxy"]["PROXY_PORT"]
            proxy_config=int(proxy_config)
            return proxy_config
    except Exception as e:
        print(f"获取proxy配置失败：{e}")
        return None
