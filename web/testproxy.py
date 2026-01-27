import socket

def check_port_listening(host: str = "127.0.0.1", port: int = 10809, timeout: float = 2.0) -> bool:
    """
    检查指定主机的指定端口是否有监听
    
    Args:
        host: 目标主机IP，默认本机(127.0.0.1)
        port: 目标端口，默认10809
        timeout: 连接超时时间（秒），默认2秒
    
    Returns:
        bool: 端口有监听返回True，无监听返回False
    """
    # 创建TCP socket对象
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # 设置连接超时
            s.settimeout(timeout)
            # 尝试连接端口
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            # 超时/连接被拒绝/系统错误，均判定为端口未监听
            return False

# 主程序执行
if __name__ == "__main__":
    # 测试本机10809端口
    is_listening = check_port_listening(port=10809)
    if is_listening:
        print(f"✅ 10809端口有程序监听")
    else:
        print(f"❌ 10809端口未监听（或连接超时）")