import os
from openai import OpenAI
import json
import requests
import time

# ================== ⚠️ 配置部分 ⚠️ ==================
# 1. API Key 配置
DEEPSEEK_API_KEY = ""  # 替换为你的 DeepSeek API Key
SERPER_API_KEY = ""  # 替换为你从图中复制的 Serper API Key
SERPER_URL = "https://google.serper.dev/search"

# 2. 代理配置
PROXY_ADDRESS = "http://127.0.0.1:10809" 
PROXIES = {
    "http": PROXY_ADDRESS,
    "https": PROXY_ADDRESS,
}

# 3. 初始化客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# ================== 联网搜索函数 (使用 Serper) ==================
def serper_search(query: str):
    """使用 Serper API 进行 Google 搜索"""
    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({"q": query, "num": 3}) # num: 返回结果数量
        
        # 🌟 通过代理发送请求到 Serper
        response = requests.post(SERPER_URL, headers=headers, data=payload, timeout=15, proxies=PROXIES) 
        
        if response.status_code == 200:
            data = response.json()
            
            # 格式化搜索结果 (从 Serper 的 Organic Results 中提取)
            results = []
            if "organic" in data:
                for i, item in enumerate(data["organic"]):
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    results.append(f"[{i+1}] 标题: {title}\n摘要: {snippet}\n链接: {link}")
            
            return "\n\n".join(results) if results else "未找到相关信息"
        else:
            try:
                error_details = response.json().get('message', '无详细错误信息')
            except:
                error_details = response.text
            return f"Serper 搜索失败 (状态码: {response.status_code})，原因: {error_details}"
            
    except requests.exceptions.Timeout:
        return f"Serper 搜索出错: 请求超时（15秒）。请检查代理是否工作 ({PROXY_ADDRESS})"
    except Exception as e:
        return f"Serper 搜索出错: {str(e)}"

# ================== 主对话函数 (强制搜索 + 持续对话) ==================
def simple_chat():
    """使用 Serper 搜索的持续对话"""
    # ... (其余代码保持不变，除了调用 serper_search 替代 google_search) ...
    
    # 强制搜索的系统提示词，用于指导 DeepSeek 基于搜索结果回答
    system_prompt = "你是一位专业的资讯助理。你的任务是基于我提供的最新搜索结果，给出准确、简洁的回答。不要重复搜索内容，只总结和回答用户的问题。"
    
    messages_history = [{"role": "system", "content": system_prompt}]
    
    print("--- 🤖 DeepSeek 联网助手 (使用 Serper API) 启动 ---")
    print(f"📡 代理设置: {PROXY_ADDRESS}")
    print("提示：你的每一个问题都会自动触发 Serper 搜索。")
    print("输入 '退出' 或 'exit' 结束对话\n" + "="*50)
    
    while True:
        try:
            # 用户输入
            user_input = input("👤 问: ").strip()
            
            if user_input.lower() in ['退出', 'exit', 'quit']:
                print("\n👋 对话结束，感谢使用！")
                break
                
            if not user_input:
                continue
                
            # 1. 执行搜索 (使用新的 serper_search 函数)
            print(f"🔍 搜索 '{user_input}' 中...", end="", flush=True)
            search_result = serper_search(user_input)
            print(" 完成")
            
            # 2. 检查搜索是否成功
            if "Serper 搜索失败" in search_result or "Serper 搜索出错" in search_result:
                print(f"❌ 搜索失败。无法继续回答。错误信息: {search_result}")
                continue # 跳过本轮提问

            # 3. 将搜索结果和用户问题整合成最终 Prompt
            final_prompt = f"""
                当前对话历史：
                {json.dumps(messages_history[-5:])} 
                
                请基于以下**最新的搜索结果**，回答用户的问题：【{user_input}】

                --- 最新搜索结果 ---
                {search_result}
                
                请严格遵循系统提示词的要求，给出回答。
            """
            
            # 4. 调用 DeepSeek API
            print("🤖 正在生成回答...", end="", flush=True)
            
            # 每次调用只发送系统提示词和包含上下文、搜索结果的用户Prompt
            response = client.chat.completions.create(
                model="deepseek-chat", # 使用 DeepSeek 的聊天模型
                messages=[{"role": "user", "content": final_prompt}],
                stream=True
            )
            
            # 5. 流式输出回答
            print("\n🤖 答: ", end="", flush=True)
            full_response = ""
            
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n")  # 换行
            
            # 6. 更新历史记录
            messages_history.append({"role": "user", "content": user_input})
            messages_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            print(f"\n❌ DeepSeek API 或其他错误: {e}")
            time.sleep(1) 

# ================== 程序入口 ==================
if __name__ == "__main__":
    # 检查配置是否已替换
    if DEEPSEEK_API_KEY == "YOUR_DEEPSEEK_API_KEY" or SERPER_API_KEY == "YOUR_SERPER_API_KEY":
        print("❌ 请检查配置部分的 DEEPSEEK_API_KEY 和 SERPER_API_KEY 是否已替换。")
    else:
        simple_chat()