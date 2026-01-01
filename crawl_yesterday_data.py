import datetime
import crawler
import logging
import requests
import db
import sqlite3

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def crawl_yesterday_data():
    """抓取昨天的股票数据"""
    # 获取昨天的日期
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y%m%d")
    
    logging.info(f"开始抓取昨天({yesterday_str})的股票数据")
    
    # 检查昨天是否是工作日
    if crawler.is_weekday(yesterday):
        logging.info(f"开始抓取昨天({yesterday_str})的股票数据")
        
        # 检查昨天的数据是否已经存在
        if db.date_has_data(yesterday_str):
            logging.info(f"昨天({yesterday_str})的数据已经存在，将删除旧表并重新创建")
            # 删除旧表
            try:
                conn = sqlite3.connect(db.DB_PATH)
                cursor = conn.cursor()
                table_name = f"stock_{yesterday_str}"
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                conn.close()
                logging.info(f"成功删除旧表{table_name}")
            except Exception as e:
                logging.error(f"删除旧表失败: {e}")
                return
        else:
            logging.info(f"昨天({yesterday_str})的数据不存在，开始抓取")
        
        # 构建API URL
        url = f"{crawler.BASE_URL}?date={yesterday_str}&normal=true&uplimit=true"
        
        try:
            # 发送API请求
            response = requests.get(url, headers=crawler.HEADERS)
            response.raise_for_status()
            
            # 解析JSON数据
            data = response.json()
            
            if data.get("code") == 20000 and data.get("data"):
                # 获取股票数据项
                items = data["data"].get("items", [])
                
                if items:
                    logging.info(f"成功获取{yesterday_str}的{len(items)}条股票数据")
                    # 处理并存储数据
                    crawler.process_and_store_data(yesterday_str, items)
                    logging.info(f"成功将昨天({yesterday_str})的股票数据存储到数据库")
                else:
                    logging.info(f"昨天({yesterday_str})没有股票数据")
            else:
                logging.error(f"API返回错误: {data.get('message', '未知错误')}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"请求API失败: {e}")
        except Exception as e:
            logging.error(f"处理数据时出错: {e}")
    else:
        logging.info(f"昨天({yesterday_str})是周末，不需要抓取数据")

if __name__ == "__main__":
    crawl_yesterday_data()