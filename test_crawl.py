#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试数据抓取功能
"""

import crawler
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_manual_crawl():
    """测试手动触发抓取（绕过时间检查）"""
    logging.info("=== 测试手动触发数据抓取（绕过时间检查） ===")
    
    # 调用crawl_stock_data，设置bypass_time_check=True
    result = crawler.crawl_stock_data(
        crawl_today_only=True,
        force_update=True,
        bypass_time_check=True
    )
    
    logging.info(f"测试结果: {result}")
    return result

def test_time_restricted_crawl():
    """测试受时间限制的抓取"""
    logging.info("\n=== 测试受时间限制的数据抓取 ===")
    
    # 调用crawl_stock_data，不绕过时间检查
    result = crawler.crawl_stock_data(
        crawl_today_only=True,
        force_update=True,
        bypass_time_check=False
    )
    
    logging.info(f"测试结果: {result}")
    return result

if __name__ == "__main__":
    # 测试手动触发（应该成功）
    manual_result = test_manual_crawl()
    
    # 测试时间限制（根据当前时间可能成功或失败）
    time_restricted_result = test_time_restricted_crawl()
    
    print(f"\n=== 最终测试结果 ===")
    print(f"手动触发（绕过时间检查）: {'成功' if manual_result['status'] == 'success' else '失败'}")
    print(f"受时间限制的触发: {'成功' if time_restricted_result['status'] == 'success' else '失败'}")
