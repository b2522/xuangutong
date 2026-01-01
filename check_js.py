"""
检查数据库中是否包含JavaScript代码
"""
import sqlite3

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

def check_for_javascript():
    """检查数据库中是否包含JavaScript代码"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有股票表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name")
        tables = cursor.fetchall()
        
        total_invalid = 0
        
        for table in tables:
            table_name = table[0]
            
            # 获取所有记录
            cursor.execute(f"SELECT id, code, name, description FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                record_id = row[0]
                code = row[1]
                name = row[2]
                description = row[3]
                
                # 检查是否包含JavaScript代码
                if not is_valid_description(description):
                    print(f"发现JavaScript代码 - 表: {table_name}, ID: {record_id}, 代码: {code}, 名称: {name}")
                    print(f"Description: {description[:200]}")
                    print("-" * 80)
                    total_invalid += 1
        
        print(f"总共发现 {total_invalid} 条包含JavaScript代码的记录")
        
    except Exception as e:
        print(f"检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_for_javascript()
