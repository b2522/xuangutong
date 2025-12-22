import datetime

def get_current_time():
    """获取当前时间（时分，24小时制）"""
    now = datetime.datetime.now()
    return now.hour, now.minute

def is_valid_crawl_time():
    """检查是否在允许的抓取时间范围内（15:00到9:00）"""
    hour, minute = get_current_time()
    print(f"当前时间: {hour:02d}:{minute:02d}")
    
    # 允许的时间范围：15:00到第二天9:00
    # 即hour >= 15 或者 hour < 9
    result = hour >= 15 or hour < 9
    print(f"是否在允许的抓取时间范围内: {result}")
    return result

if __name__ == "__main__":
    is_valid_crawl_time()