import requests
import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API基本URL
BASE_URL = "https://flash-api.xuangubao.com.cn/api/surge_stock/stocks"

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

# 测试日期：今天
today = datetime.datetime.now()
date_str = today.strftime("%Y%m%d")
print(f"测试日期: {date_str}")

# 构建API URL
url = f"{BASE_URL}?date={date_str}&normal=true&uplimit=true"
print(f"API URL: {url}")

try:
    # 发送API请求
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    # 解析JSON数据
    data = response.json()
    
    print(f"API响应状态码: {response.status_code}")
    print(f"API响应内容: {data}")
    
    if data.get("code") == 20000:
        print("API调用成功!")
        items = data["data"].get("items", [])
        print(f"获取到{len(items)}条股票数据")
        if items:
            print("第一条数据示例:", items[0])
    else:
        print(f"API调用失败: {data.get('message', '未知错误')}")
        
except requests.exceptions.RequestException as e:
    print(f"请求API失败: {e}")
    
except Exception as e:
    print(f"处理数据时出错: {e}")
