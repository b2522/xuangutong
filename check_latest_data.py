#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查最新的股票数据
"""

import db
import datetime

def check_latest_data():
    """检查最新的股票数据"""
    # 获取今天的日期
    today = datetime.datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    print(f"=== 检查{date_str}的股票数据 ===")
    
    # 检查该日期是否有数据
    if db.date_has_data(date_str):
        print(f"✅ {date_str}已有数据")
        
        # 获取该日期的数据
        data = db.get_stock_data_by_date(date_str)
        print(f"✅ 共找到{len(data)}条股票数据")
        
        # 打印前5条数据作为示例
        print("\n📊 前5条数据示例:")
        for i, stock in enumerate(data[:5], 1):
            print(f"{i}. {stock['name']} ({stock['code']}) - {stock['description']}")
    else:
        print(f"❌ {date_str}没有数据")
    
    print("\n=== 检查完成 ===")

if __name__ == "__main__":
    check_latest_data()
