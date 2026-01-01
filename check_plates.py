import sqlite3
import glob

# 连接数据库
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

# 获取所有的stock表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'stock_%' ORDER BY name DESC")
tables = cursor.fetchall()

if tables:
    # 获取最新的表名
    latest_table = tables[0][0]
    print(f"使用最新表: {latest_table}")
    
    # 查询plates字段的不同值，看是否包含异常内容
    cursor.execute(f"SELECT DISTINCT plates FROM {latest_table} LIMIT 50")
    rows = cursor.fetchall()
    
    print(f"\n查询到 {len(rows)} 种不同的题材内容:")
    print("=" * 50)
    
    # 输出前20个结果，看看是否有异常内容
    for i, row in enumerate(rows[:20]):
        plates = row[0]
        print(f"{i+1}. {plates}")
        # 检查是否包含代码片段
        if '<' in plates or '>' in plates or 'function' in plates or 'var' in plates:
            print(f"   ⚠️  包含异常内容！")
    
    print("=" * 50)
    
    # 检查是否有包含代码的记录
    cursor.execute(f"SELECT COUNT(*) FROM {latest_table} WHERE plates LIKE '%<script%' OR plates LIKE '%function%' OR plates LIKE '%var %'")
    code_count = cursor.fetchone()[0]
    print(f"\n包含可能代码内容的记录数: {code_count}")
    
    if code_count > 0:
        # 查看具体的异常记录
        cursor.execute(f"SELECT plates FROM {latest_table} WHERE plates LIKE '%<script%' OR plates LIKE '%function%' OR plates LIKE '%var %' LIMIT 5")
        code_rows = cursor.fetchone()
        print(f"\n异常内容示例: {code_rows}")
else:
    print("没有找到stock表")

# 关闭连接
conn.close()