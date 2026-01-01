"""
检查数据库中的description字段内容
"""
import sqlite3

# 数据库文件路径
DB_PATH = "stock_data.db"

def check_descriptions():
    """检查数据库中的description字段"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有股票表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC LIMIT 1")
        latest_table = cursor.fetchone()
        
        if not latest_table:
            print("没有找到股票表")
            return
        
        table_name = latest_table[0]
        print(f"检查表: {table_name}")
        print("=" * 80)
        
        # 获取前10条记录的description
        cursor.execute(f"SELECT id, code, name, description FROM {table_name} LIMIT 10")
        rows = cursor.fetchall()
        
        for row in rows:
            record_id = row[0]
            code = row[1]
            name = row[2]
            description = row[3]
            
            print(f"ID: {record_id}, 代码: {code}, 名称: {name}")
            print(f"Description: {description[:200] if description else '(空)'}")
            print("-" * 80)
        
    except Exception as e:
        print(f"检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_descriptions()
