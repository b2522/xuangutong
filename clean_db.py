"""
清理数据库中包含JavaScript代码的description字段
"""
import sqlite3
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 数据库文件路径
DB_PATH = "stock_data.db"

# 定义需要过滤的关键词（JavaScript代码特征）
filter_keywords = ['function', 'var ', 'const ', 'let ', 'return ', 'if (', 'else {', 'console.log', '// ', 'document.', 'fetch(', '.then(', '.catch(']

def is_valid_description(desc):
    """检查description是否有效（不包含JavaScript代码）"""
    if not desc:
        return True
    desc_lower = desc.lower()
    for keyword in filter_keywords:
        if keyword in desc_lower:
            return False
    return True

def clean_database():
    """清理数据库中的JavaScript代码"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有股票表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name")
        tables = cursor.fetchall()
        
        total_cleaned = 0
        
        for table in tables:
            table_name = table[0]
            logging.info(f"处理表: {table_name}")
            
            # 获取所有包含JavaScript代码的记录
            cursor.execute(f"SELECT id, code, name, description FROM {table_name}")
            rows = cursor.fetchall()
            
            cleaned_count = 0
            for row in rows:
                record_id = row[0]
                code = row[1]
                name = row[2]
                description = row[3]
                
                # 检查是否包含JavaScript代码
                if not is_valid_description(description):
                    logging.info(f"发现脏数据 - 表: {table_name}, ID: {record_id}, 代码: {code}, 名称: {name}")
                    
                    # 清空description字段
                    cursor.execute(f"UPDATE {table_name} SET description = '' WHERE id = ?", (record_id,))
                    cleaned_count += 1
                    total_cleaned += 1
            
            if cleaned_count > 0:
                logging.info(f"表 {table_name} 清理了 {cleaned_count} 条记录")
        
        # 提交更改
        conn.commit()
        logging.info(f"总共清理了 {total_cleaned} 条包含JavaScript代码的记录")
        
    except Exception as e:
        logging.error(f"清理数据库失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_database()
