#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试日期选择修复
验证20251223日期的数据是否能正确获取
"""

import requests
import time
import json


def test_20251223_data_availability():
    """测试20251223日期数据是否可用"""
    print("开始测试20251223日期数据可用性...")
    
    # 测试get_available_dates API
    print("\n1. 测试get_available_dates API")
    try:
        response = requests.get("http://localhost:5000/available-dates", headers={
            'Cache-Control': 'no-cache'
        })
        response.raise_for_status()
        available_dates = response.json()
        print(f"  获取到 {len(available_dates)} 个可用日期")
        print(f"  20251223 是否在可用日期列表中: {'20251223' in available_dates}")
    except Exception as e:
        print(f"  调用get_available_dates API失败: {e}")
    
    # 直接测试get-data-by-date API
    print("\n2. 直接测试get-data-by-date API")
    try:
        response = requests.get("http://localhost:5000/get-data-by-date?date=20251223", headers={
            'Cache-Control': 'no-cache'
        })
        response.raise_for_status()
        date_data = response.json()
        print(f"  20251223 日期数据量: {len(date_data)}")
        
        if date_data:
            print("  前5条数据样本:")
            for i, item in enumerate(date_data[:5]):
                print(f"  {i+1}. {item['name']} ({item['code_part']}.{item['market'].upper()})")
        else:
            print("  警告: 未能获取到20251223的数据")
            
    except Exception as e:
        print(f"  调用get-data-by-date API失败: {e}")
    
    print("\n测试完成!")


if __name__ == "__main__":
    print("=== 日期验证修复测试 ===\n")
    
    # 确保服务器正在运行
    print("请确保Flask服务器已启动在http://localhost:5000/")
    input("按Enter键继续测试...")
    
    # 执行测试
    test_20251223_data_availability()
