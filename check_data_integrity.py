#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查12月1日至今的数据完整性脚本，并支持自动补充缺失数据

功能特性：
1. 检查12月1日至今所有工作日的数据完整性
2. 自动识别和跳过周末数据检查
3. 支持自动补充缺失的历史数据
4. 根据时间规则自动调整抓取行为（9:00-15:00不抓取当天数据）
5. 提供详细的数据统计和日志输出
"""

import datetime
import db
import crawler
import logging
import time
import argparse
import sys

try:
    from tqdm import tqdm  # 进度条显示
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    logging.warning("未安装tqdm库，将不显示进度条")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 开始日期：12月1日
START_DATE = datetime.datetime.now().replace(month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
# 结束日期：今天
END_DATE = datetime.datetime.now()

def is_weekday(date):
    """判断日期是否为工作日（周一到周五）"""
    return date.weekday() < 5  # 0-4表示周一到周五

def is_weekend(date):
    """判断日期是否为周末（周六到周日）"""
    return date.weekday() >= 5  # 5-6表示周六到周日

def format_date(date):
    """将日期格式化为YYYYMMDD格式"""
    return date.strftime("%Y%m%d")

def get_current_time():
    """获取当前时间（时分，24小时制）"""
    now = datetime.datetime.now()
    return now.hour, now.minute

def is_valid_crawl_time_for_today():
    """检查当前时间是否适合抓取今天的数据
    根据要求：9:00到15:00不抓取今天的数据
    
    Returns:
        bool: 是否适合抓取今天的数据
    """
    hour, minute = get_current_time()
    
    # 不适合抓取的时间范围：9:00到15:00
    return hour < 9 or hour >= 15

def get_date_weekday_name(date):
    """获取日期的星期名称"""
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekdays[date.weekday()]

def check_data_integrity(start_date=None, end_date=None, silent=False):
    """
    检查指定日期范围内的数据完整性
    
    Args:
        start_date: 开始日期，默认12月1日
        end_date: 结束日期，默认今天
        silent: 是否静默模式，不输出详细日志
    
    Returns:
        dict: 包含检查结果的字典
    """
    # 使用默认值
    if start_date is None:
        start_date = START_DATE
    if end_date is None:
        end_date = END_DATE
    
    if not silent:
        logging.info(f"开始检查{format_date(start_date)}至{format_date(end_date)}的数据完整性")
    
    # 统计信息
    stats = {
        'total_days': 0,
        'weekdays': 0,
        'weekends': 0,
        'has_data': 0,
        'no_data': 0,
        'missing_days': [],  # 缺失数据的工作日列表
        'details': []        # 详细信息列表
    }
    
    # 计算总天数用于进度条
    total_days_count = (end_date - start_date).days + 1
    
    # 创建进度条
    if HAS_TQDM and not silent:
        progress_bar = tqdm(total=total_days_count, desc="检查进度", unit="天")
    
    try:
        # 预先获取所有有数据的日期，减少数据库连接次数
        available_dates = set(db.get_available_dates())
        
        # 遍历日期范围
        current_date = start_date
        while current_date <= end_date:
            stats['total_days'] += 1
            date_str = format_date(current_date)
            weekday_name = get_date_weekday_name(current_date)
            
            detail = {
                'date': date_str,
                'weekday': weekday_name,
                'has_data': False,
                'data_count': 0
            }
            
            if is_weekday(current_date):
                stats['weekdays'] += 1
                # 检查该工作日是否有数据（使用预获取的日期集合，避免重复连接数据库）
                has_data = date_str in available_dates
                
                if has_data:
                    stats['has_data'] += 1
                    # 获取数据量 - 只在需要时连接数据库
                    try:
                        data = db.get_stock_data_by_date(date_str)
                        data_count = len(data)
                        detail['has_data'] = True
                        detail['data_count'] = data_count
                        if not silent:
                            logging.info(f"📅 {date_str} ({weekday_name}): 有数据，共{data_count}条")
                    except Exception as e:
                        logging.error(f"获取{date_str}的数据量时出错: {e}")
                else:
                    stats['no_data'] += 1
                    stats['missing_days'].append(date_str)
                    if not silent:
                        logging.warning(f"❌ {date_str} ({weekday_name}): 无数据")
            else:
                stats['weekends'] += 1
                if not silent:
                    logging.info(f"📅 {date_str} ({weekday_name}): 周末，无需数据")
            
            stats['details'].append(detail)
            
            # 更新进度条
            if HAS_TQDM and not silent:
                progress_bar.update(1)
            
            # 日期加1天
            current_date += datetime.timedelta(days=1)
            
            # 短暂休眠避免CPU占用过高
            if stats['total_days'] % 10 == 0:
                time.sleep(0.01)
    finally:
        # 确保进度条关闭
        if HAS_TQDM and not silent and 'progress_bar' in locals():
            progress_bar.close()
    
    # 输出统计结果
    logging.info("\n===== 数据完整性检查统计 =====")
    logging.info(f"总天数: {stats['total_days']}")
    logging.info(f"工作日数: {stats['weekdays']}")
    logging.info(f"周末数: {stats['weekends']}")
    logging.info(f"已有数据的工作日数: {stats['has_data']}")
    logging.info(f"缺失数据的工作日数: {stats['no_data']}")
    
    if stats['missing_days']:
        logging.warning(f"\n缺失数据的工作日列表:")
        for missing_day in stats['missing_days']:
            logging.warning(f"  - {missing_day}")
    else:
        logging.info("\n✅ 所有工作日数据完整!")
    
    return stats

def retry_on_error(max_retries=3, delay_seconds=2):
    """
    错误重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay_seconds: 重试间隔时间（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"尝试 {attempt+1}/{max_retries} 失败: {e}，将在 {delay_seconds} 秒后重试...")
                        time.sleep(delay_seconds)
                    else:
                        logging.error(f"尝试 {max_retries}/{max_retries} 失败: {e}")
            raise last_exception
        return wrapper
    return decorator

@retry_on_error(max_retries=3, delay_seconds=3)
def crawl_single_date_data(date_obj, date_str, force_update=False, bypass_time_check=False):
    """
    抓取单个日期的数据（带重试机制）
    """
    # 临时修改crawler模块的START_DATE和END_DATE以抓取特定日期
    original_start_date = crawler.START_DATE
    original_end_date = crawler.END_DATE
    
    try:
        crawler.START_DATE = date_obj
        crawler.END_DATE = date_obj
        
        # 调用爬虫函数抓取单个日期的数据
        return crawler.crawl_stock_data(
            crawl_today_only=False,
            force_update=force_update,
            bypass_time_check=bypass_time_check
        )
    finally:
        # 恢复原始日期
        crawler.START_DATE = original_start_date
        crawler.END_DATE = original_end_date

def supplement_missing_data(missing_days, force_update=False, bypass_time_check=False, auto_supplement=False):
    """
    补充缺失的数据
    
    Args:
        missing_days: 缺失数据的日期列表（格式为YYYYMMDD）
        force_update: 是否强制更新已有数据
        bypass_time_check: 是否绕过时间检查
        auto_supplement: 是否自动补充（无需用户确认）
    
    Returns:
        dict: 补充结果统计
    """
    if not missing_days:
        logging.info("没有缺失的数据需要补充")
        return {'status': 'success', 'supplemented': 0, 'failed': 0, 'skipped': 0}
    
    # 如果不是自动模式，且用户未确认，则询问是否继续
    if not auto_supplement:
        print(f"\n发现{len(missing_days)}个缺失数据的工作日，是否继续补充？(y/n): ")
        choice = input().strip().lower()
        if choice != 'y':
            print("已取消数据补充")
            return {'status': 'cancelled', 'supplemented': 0, 'failed': 0, 'skipped': 0}
    
    logging.info(f"开始补充{len(missing_days)}个日期的缺失数据")
    
    # 统计结果
    result = {
        'status': 'success',
        'supplemented': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    # 获取今天的日期字符串
    today_str = format_date(datetime.datetime.now())
    
    # 创建进度条
    if HAS_TQDM:
        progress_bar = tqdm(total=len(missing_days), desc="补充进度", unit="个")
    
    try:
        # 遍历缺失的日期
        for date_str in missing_days:
            try:
                # 解析日期字符串
                date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
                weekday_name = get_date_weekday_name(date_obj)
                
                # 检查是否为周末
                if is_weekend(date_obj):
                    logging.info(f"⏩ 跳过{date_str} ({weekday_name}): 周末不应该有数据")
                    result['skipped'] += 1
                    result['details'].append({
                        'date': date_str,
                        'status': 'skipped',
                        'message': '周末不应该有数据'
                    })
                    if HAS_TQDM:
                        progress_bar.update(1)
                    continue
                
                # 如果是今天，检查时间是否适合抓取
                current_bypass = bypass_time_check
                if date_str == today_str and not bypass_time_check:
                    if not is_valid_crawl_time_for_today():
                        hour, minute = get_current_time()
                        logging.warning(f"⏩ 跳过今天({date_str})的数据抓取: 当前时间 {hour:02d}:{minute:02d} 不在允许的时间范围内")
                        logging.warning("根据要求，9:00到15:00之间不抓取今天的数据")
                        result['skipped'] += 1
                        result['details'].append({
                            'date': date_str,
                            'status': 'skipped',
                            'message': f'当前时间 {hour:02d}:{minute:02d} 不适合抓取今天的数据（9:00-15:00不抓取）'
                        })
                        if HAS_TQDM:
                            progress_bar.update(1)
                        continue
                
                logging.info(f"开始补充{date_str} ({weekday_name})的数据")
                
                # 对于历史数据，始终绕过时间检查
                if date_str != today_str:
                    current_bypass = True
                    
                # 使用带重试机制的函数抓取数据
                crawl_result = crawl_single_date_data(
                    date_obj, 
                    date_str, 
                    force_update=force_update, 
                    bypass_time_check=current_bypass
                )
                
                if crawl_result['status'] == 'success':
                    result['supplemented'] += 1
                    logging.info(f"✅ 成功补充{date_str}的数据")
                else:
                    result['failed'] += 1
                    logging.error(f"❌ 补充{date_str}的数据失败: {crawl_result.get('message', '未知错误')}")
                
                # 添加详细信息
                result['details'].append({
                    'date': date_str,
                    'status': 'success' if crawl_result['status'] == 'success' else 'failed',
                    'message': crawl_result.get('message', '')
                })
                
                # 添加延时，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                result['failed'] += 1
                logging.error(f"❌ 处理{date_str}时发生错误: {e}")
                result['details'].append({
                    'date': date_str,
                    'status': 'failed',
                    'message': str(e)
                })
            finally:
                # 更新进度条
                if HAS_TQDM:
                    progress_bar.update(1)
    finally:
        # 确保进度条关闭
        if HAS_TQDM and 'progress_bar' in locals():
            progress_bar.close()
    
    # 输出补充结果
    logging.info("\n===== 数据补充统计 =====")
    logging.info(f"总缺失日期数: {len(missing_days)}")
    logging.info(f"成功补充: {result['supplemented']}")
    logging.info(f"补充失败: {result['failed']}")
    logging.info(f"跳过: {result['skipped']} (周末或时间不适合)")
    
    if result['failed'] > 0:
        result['status'] = 'partial_success'
        logging.warning("部分数据补充失败，请检查错误信息")
    
    return result

def display_time_rules(verbose=True):
    """显示数据抓取的时间规则"""
    if verbose:
        print("\n📋 数据抓取时间规则:")
        print("1. 周六周日不应该有股票数据")
        print("2. 9:00到15:00之间不抓取今天的数据")
        print("3. 建议在15:00之后或9:00之前抓取当天数据")
    
    # 显示当前时间和是否适合抓取今天的数据
    hour, minute = get_current_time()
    is_valid = is_valid_crawl_time_for_today()
    
    if verbose:
        print(f"\n🕒 当前时间: {hour:02d}:{minute:02d}")
        print(f"✅ 是否适合抓取今天的数据: {'是' if is_valid else '否'}")
        if not is_valid:
            print("  (提示: 当前处于9:00-15:00之间，不建议抓取今天的数据)")
        print()
    
    return is_valid

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票数据完整性检查和补充工具')
    
    parser.add_argument('--check-only', action='store_true', 
                       help='仅检查数据完整性，不补充缺失数据')
    parser.add_argument('--auto-supplement', action='store_true', 
                       help='自动补充缺失数据，无需用户确认')
    parser.add_argument('--force-update', action='store_true', 
                       help='强制更新已有数据')
    parser.add_argument('--bypass-time-check', action='store_true', 
                       help='绕过时间检查限制')
    parser.add_argument('--start-date', type=str, 
                       help='开始日期，格式为YYYYMMDD，默认为12月1日')
    parser.add_argument('--end-date', type=str, 
                       help='结束日期，格式为YYYYMMDD，默认为今天')
    parser.add_argument('--quiet', action='store_true', 
                       help='静默模式，减少输出信息')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    if args.quiet:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 解析日期参数
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.datetime.strptime(args.start_date, "%Y%m%d")
        except ValueError:
            logging.error("开始日期格式错误，应为YYYYMMDD")
            sys.exit(1)
    
    if args.end_date:
        try:
            end_date = datetime.datetime.strptime(args.end_date, "%Y%m%d")
        except ValueError:
            logging.error("结束日期格式错误，应为YYYYMMDD")
            sys.exit(1)
    
    # 显示时间规则（静默模式下不显示详细信息）
    if not args.quiet:
        display_time_rules()
    
    try:
        # 先检查数据完整性
        stats = check_data_integrity(start_date=start_date, end_date=end_date, silent=args.quiet)
        
        # 输出统计结果
        if not args.quiet:
            print("\n===== 数据完整性检查统计 =====")
            print(f"总天数: {stats['total_days']}")
            print(f"工作日数: {stats['weekdays']}")
            print(f"周末数: {stats['weekends']}")
            print(f"已有数据的工作日数: {stats['has_data']}")
            print(f"缺失数据的工作日数: {stats['no_data']}")
            
            if stats['missing_days']:
                print(f"\n缺失数据的工作日列表:")
                for i, missing_day in enumerate(stats['missing_days'], 1):
                    print(f"  {i}. {missing_day}")
            else:
                print("\n✅ 所有工作日数据完整!")
        
        # 如果有缺失的数据，且不是仅检查模式，则补充数据
        if stats['missing_days'] and not args.check_only:
            # 补充缺失数据
            supplement_result = supplement_missing_data(
                stats['missing_days'], 
                force_update=args.force_update,
                bypass_time_check=args.bypass_time_check,
                auto_supplement=args.auto_supplement
            )
            
            # 再次检查数据完整性，验证补充效果
            if not args.quiet and supplement_result['supplemented'] > 0:
                print("\n===== 验证补充结果 =====")
                final_stats = check_data_integrity(start_date=start_date, end_date=end_date, silent=args.quiet)
                
                # 输出最终统计
                print(f"\n===== 最终数据完整性统计 =====")
                print(f"总工作日数: {final_stats['weekdays']}")
                print(f"已有数据的工作日数: {final_stats['has_data']}")
                print(f"仍缺失数据的工作日数: {final_stats['no_data']}")
                
                if final_stats['no_data'] == 0:
                    print("\n🎉 恭喜！所有工作日数据已完整补充!")
                else:
                    print(f"\n仍有{final_stats['no_data']}个工作日的数据缺失，请检查错误日志")
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
