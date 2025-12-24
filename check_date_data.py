import sqlite3
import os

DB_PATH = "stock_data.db"

def check_date_data(date_str):
    """检查指定日期在数据库中的数据状态"""
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(DB_PATH):
            print(f"数据库文件 {DB_PATH} 不存在")
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        table_name = f"stock_{date_str}"
        
        # 检查表格是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print(f"表 {table_name} 存在")
            
            # 检查表中的数据量
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"表 {table_name} 中有 {count} 条数据")
            
            # 获取表的前5条数据样本
            cursor.execute(f"SELECT code, name, date FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            print("\n数据样本（前5条）:")
            for row in sample_data:
                print(f"代码: {row[0]}, 名称: {row[1]}, 日期: {row[2]}")
            
            # 获取所有有数据的日期列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
            tables = cursor.fetchall()
            available_dates = []
            for table in tables:
                table_name = table[0]
                # 从表名中提取日期部分，格式为YYYYMMDD
                date = table_name.replace('stock_', '')
                # 检查表中是否有数据
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    available_dates.append(date)
            
            print(f"\n数据库中有数据的日期列表（共 {len(available_dates)} 个）:")
            print(available_dates)
            
            # 检查20251223是否在可用日期列表中
            if date_str in available_dates:
                print(f"\n{date_str} 日期存在于可用日期列表中")
            else:
                print(f"\n{date_str} 日期不存在于可用日期列表中，但表中存在数据")
                print("可能的原因：在获取可用日期列表时出现问题")
                
        else:
            print(f"表 {table_name} 不存在")
            
            # 列出所有存在的股票表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
            tables = cursor.fetchall()
            if tables:
                print("\n数据库中存在的股票表:")
                for table in tables:
                    print(table[0])
            else:
                print("\n数据库中没有股票表")
                
    except Exception as e:
        print(f"检查数据库时发生错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# 检查20251223的数据状态
check_date_data('20251223')
