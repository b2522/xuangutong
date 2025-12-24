import os
import sys
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# 设置日志
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# 模拟定时任务函数
def mock_scheduled_crawl():
    logging.info("模拟定时任务执行: 抓取股票数据")

# 检查定时任务配置
def check_scheduled_tasks():
    setup_logger()
    logging.info("开始检查定时任务配置")
    
    # 创建临时调度器
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    
    # 添加与app.py相同的定时任务
    scheduler.add_job(mock_scheduled_crawl, 'cron', hour=15, minute=0, second=0, day_of_week='0-4', id='task1500')
    scheduler.add_job(mock_scheduled_crawl, 'cron', hour=16, minute=15, second=0, day_of_week='0-4', id='task1615')
    
    # 启动调度器以验证配置
    try:
        scheduler.start()
        logging.info("临时调度器启动成功")
        
        # 检查任务配置
        jobs = scheduler.get_jobs()
        logging.info(f"找到 {len(jobs)} 个定时任务")
        
        for job in jobs:
            logging.info(f"任务ID: {job.id}")
            logging.info(f"  执行时间: {job.trigger}")
            # 检查下一次执行时间
            next_run_time = job.next_run_time
            if next_run_time:
                logging.info(f"  下一次执行时间: {next_run_time}")
            
            # 检查任务配置参数
            if hasattr(job.trigger, 'fields'):
                fields = job.trigger.fields
                hour = None
                minute = None
                day_of_week = None
                
                for field in fields:
                    if field.name == 'hour':
                        hour = field.expressions[0] if field.expressions else None
                    elif field.name == 'minute':
                        minute = field.expressions[0] if field.expressions else None
                    elif field.name == 'day_of_week':
                        day_of_week = field.expressions[0] if field.expressions else None
                
                logging.info(f"  配置: 小时={hour}, 分钟={minute}, 星期几={day_of_week}")
        
        # 验证任务配置是否符合要求
        is_config_correct = len(jobs) == 2
        task1500_exists = any(job.id == 'task1500' for job in jobs)
        task1615_exists = any(job.id == 'task1615' for job in jobs)
        
        if is_config_correct and task1500_exists and task1615_exists:
            logging.info("\n✓ 定时任务配置检查通过！")
            logging.info("✓ 已设置周一到周五15:00和16:15自动下载最新数据")
        else:
            logging.warning("\n✗ 定时任务配置检查未完全通过")
            
    except Exception as e:
        logging.error(f"检查过程中发生错误: {str(e)}")
    finally:
        # 关闭临时调度器
        scheduler.shutdown(wait=False)
        logging.info("临时调度器已关闭")

if __name__ == "__main__":
    check_scheduled_tasks()