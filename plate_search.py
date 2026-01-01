import sqlite3
import logging
import time
from datetime import datetime
import json
from typing import Dict, List, Any

# 数据库路径
DB_PATH = "c:/Users/b2522/Documents/trae_projects/xuangutong_web/stock_data.db"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 题材计数缓存
plate_counts_cache = {
    'data': {},
    'timestamp': 0,
    'cache_duration': 30000  # 缓存30秒
}

def sort_stocks_by_plates(stocks):
    """按照题材数量和同一题材股票数量对股票数据进行排序"""
    if not stocks:
        return []
    
    # 检查缓存是否有效
    current_time = time.time() * 1000
    if (current_time - plate_counts_cache['timestamp'] < plate_counts_cache['cache_duration'] and 
        plate_counts_cache['data']):
        # 使用缓存的题材计数
        plate_counts = plate_counts_cache['data']
    else:
        # 获取所有股票数据来统计题材出现次数
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 统计每个题材出现的总次数（基于所有股票）
        plate_counts = {}
        
        try:
            # 获取最新的几个股票表（只统计最近的10个表，减少计算量）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC LIMIT 10")
            tables = cursor.fetchall()
            
            # 遍历表，统计题材出现次数
            for table in tables:
                table_name = table[0]
                
                # 查询表中的所有数据
                cursor.execute(f"SELECT plates FROM {table_name}")
                rows = cursor.fetchall()
                
                # 统计每个题材的出现次数
                for row in rows:
                    plates = row[0]
                    if plates:
                        plate_list = plates.split('、')
                        for plate in plate_list:
                            plate_counts[plate] = plate_counts.get(plate, 0) + 1
        finally:
            conn.close()
        
        # 更新缓存
        plate_counts_cache['data'] = plate_counts
        plate_counts_cache['timestamp'] = current_time
    
    # 创建一个列表，包含股票和它们的排序键
    stocks_with_keys = []
    for stock in stocks:
        plates = stock.get('plates', '')
        if plates:
            # 计算题材数量
            plate_list = plates.split('、')
            plate_count = len(plate_list)
            
            # 计算该股票所属题材的总出现次数
            total_plate_occurrences = sum(plate_counts.get(plate, 0) for plate in plate_list)
        else:
            # 没有题材的股票排在最后
            plate_count = 0
            total_plate_occurrences = 0
        
        # 存储股票和排序键
        stocks_with_keys.append((
            stock,  # 股票数据
            (-plate_count, -total_plate_occurrences)  # 排序键
        ))
    
    # 排序
    stocks_with_keys.sort(key=lambda x: x[1])
    
    # 提取排序后的股票
    sorted_stocks = [stock for stock, key in stocks_with_keys]
    
    return sorted_stocks

def search_all_dates_plate_data(plate):
    """
    搜索所有日期中的题材数据，并确保每个股票只保留最新的记录
    
    Args:
        plate: 题材关键词
        
    Returns:
        list: 包含符合条件的股票数据列表，每个股票只保留最新记录
    """
    if not plate:
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有股票表，并按日期降序排列
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
        tables = cursor.fetchall()
        
        # 使用字典存储每个股票的最新记录
        latest_stock_records = {}
        
        # 遍历所有表，搜索符合条件的数据
        # 因为表是按日期降序排列的，所以一旦某个股票代码被添加到字典中，就可以跳过后续表中的该股票
        for table in tables:
            table_name = table[0]
            
            # 构建搜索SQL，先使用SQL过滤包含关键词的记录
            search_sql = f"""
            SELECT DISTINCT code, name, description, plates, m_days_n_boards, date 
            FROM {table_name}
            WHERE plates LIKE ?
            """
            
            # 执行搜索（SQL层面的模糊匹配）
            cursor.execute(search_sql, (f"%{plate}%",))
            rows = cursor.fetchall()
            
            # 转换为字典格式
            for row in rows:
                code = row[0]
                
                # 如果这个股票代码还没有记录，就添加到字典中
                if code not in latest_stock_records:
                    stock_plates = row[3]
                    
                    # 分割股票代码和市场
                    code_part = code
                    market = ""
                    if "." in code:
                        code_part, market = code.split(".")
                    
                    latest_stock_records[code] = {
                        "code": code,
                        "code_part": code_part,
                        "market": market,
                        "name": row[1],
                        "description": row[2],
                        "plates": stock_plates,
                        "m_days_n_boards": row[4],
                        "date": row[5]
                    }
        
        # 将字典转换为列表
        result_list = list(latest_stock_records.values())
        
        # 应用排序规则：按照题材数量和同一题材股票数量排序
        sorted_results = sort_stocks_by_plates(result_list)
        
        logger.info(f"成功搜索到{len(sorted_results)}条符合题材'{plate}'的股票数据（每个股票只保留最新记录）")
        
        return sorted_results
        
    except Exception as e:
        logger.error(f"搜索题材数据失败: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    # 查看数据库结构和示例数据
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有股票表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
        tables = cursor.fetchall()
        
        print(f"数据库中有 {len(tables)} 个股票表")
        if tables:
            latest_table = tables[0][0]
            print(f"最新的表是: {latest_table}")
            
            # 查看表结构
            cursor.execute(f"PRAGMA table_info({latest_table})")
            columns = cursor.fetchall()
            print("\n表结构:")
            for col in columns:
                print(f"  {col[1]} - {col[2]}")
            
            # 查看前3条数据作为示例
            cursor.execute(f"SELECT code, name, plates, date FROM {latest_table} LIMIT 3")
            sample_data = cursor.fetchall()
            print("\n前3条示例数据:")
            for row in sample_data:
                print(f"  代码: {row[0]}, 名称: {row[1]}")
                print(f"  题材: {row[2]}")
                print(f"  日期: {row[3]}\n")
                
            # 如果有题材数据，获取一些常见题材词
            cursor.execute(f"SELECT DISTINCT plates FROM {latest_table} WHERE plates IS NOT NULL AND plates != '' LIMIT 5")
            plate_examples = cursor.fetchall()
            if plate_examples:
                print("\n示例题材:")
                for i, plate in enumerate(plate_examples):
                    print(f"  {i+1}. {plate[0]}")
                    # 提取一些可能的关键词用于测试
                    if '、' in plate[0]:
                        keywords = plate[0].split('、')[:3]  # 取前3个关键词
                        print(f"    可能的关键词: {', '.join(keywords)}")
    finally:
        if conn:
            conn.close()
    
    # 然后尝试搜索
    # 使用实际的题材词进行测试
    test_plates = ['航天', '国产芯片', 'DRAM']
    
    for test_plate in test_plates:
        print(f"\n尝试搜索题材: '{test_plate}'")
        results = search_all_dates_plate_data(test_plate)
        print(f"找到{len(results)}条与'{test_plate}'相关的股票")
        if results:
            print(f"前5条结果：")
            for i, stock in enumerate(results[:5]):
                # 只保留code的数字部分
                code_number = stock['code']
                if '.' in code_number:
                    code_number = code_number.split('.')[0]
                
                print(f"{i+1}. 代码: {code_number}, 名称: {stock['name']}, 日期: {stock['date']}")
                print(f"   几天几板: {stock['m_days_n_boards'] or '未记录'}")
                print(f"   题材: {stock['plates']}")
                print(f"   描述: {stock['description'] or '无描述'}")