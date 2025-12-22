import sqlite3
import datetime

# 检查数据库文件是否存在
import os
print("数据库文件是否存在:", os.path.exists('stock_data.db'))

if os.path.exists('stock_data.db'):
    # 连接数据库
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    
    # 查询所有表
    print("\n所有表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
    
    # 查询最新表的结构和数据
    if tables:
        latest_table = tables[0][0]
        print(f"\n最新表 {latest_table} 的结构:")
        cursor.execute(f"PRAGMA table_info({latest_table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
        
        print(f"\n{latest_table} 的前5条数据:")
        cursor.execute(f"SELECT * FROM {latest_table} LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        
        # 查询该表的数据数量
        cursor.execute(f"SELECT COUNT(*) FROM {latest_table}")
        count = cursor.fetchone()[0]
        print(f"\n{latest_table} 有{count}条数据")
    
    # 查询今天的日期（YYYYMMDD格式）
    today = datetime.datetime.now().strftime("%Y%m%d")
    today_table = f"stock_{today}"
    print(f"\n今天({today})的表 {today_table}:")
    
    # 检查今天的表是否存在
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{today_table}'")
    if cursor.fetchone():
        cursor.execute(f"SELECT COUNT(*) FROM {today_table}")
        count = cursor.fetchone()[0]
        print(f"今天的表已存在，有{count}条数据")
    else:
        print("今天的表不存在")
    
    # 关闭连接
    conn.close()
