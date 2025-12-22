from flask import Flask, render_template, request, jsonify, make_response
import crawler
import db
import os
import requests
import logging
import hashlib
from pypinyin import lazy_pinyin, FIRST_LETTER
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    # 默认只显示最新一天的数据
    latest_data = db.get_latest_day_data()
    return render_template('index.html', stocks=latest_data, search_mode=False)

@app.route('/crawl', methods=['POST'])
def crawl_data():
    # 触发数据抓取，强制更新最新数据
    crawler.crawl_stock_data(crawl_today_only=True, force_update=True)
    return "数据抓取完成！"

@app.route('/search')
def search_stocks():
    # 获取搜索关键词
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify([])
    
    try:
        # 使用search_stocks_by_keyword获取所有匹配的股票数据
        # 这个函数已经包含了对name、description、plates和code字段的模糊匹配
        matched_stocks = db.search_stocks_by_keyword(keyword)
        
        # 从搜索结果中提取股票名称
        stock_names = []
        seen_names = set()
        
        for stock in matched_stocks:
            name = stock['name']
            if name not in seen_names:
                seen_names.add(name)
                stock_names.append(name)
        
        # 如果没有结果，再尝试拼音搜索作为补充
        if not stock_names:
            all_stock_info = db.get_all_stock_names_and_codes()
            matched_results = []
            
            for name, code in all_stock_info:
                # 转换为拼音首字母
                pinyin = ''.join(lazy_pinyin(name))
                # 转换为拼音首字母缩写
                pinyin_abbr = ''.join(lazy_pinyin(name, style=FIRST_LETTER))
                
                # 计算匹配度分数
                score = 0
                if keyword in name:
                    score += 100  # 名称完全匹配权重最高
                if keyword.lower() in pinyin.lower():
                    score += 50   # 拼音匹配权重次之
                if keyword.lower() in pinyin_abbr.lower():
                    score += 30   # 拼音缩写匹配权重再次之
                if keyword in code:
                    score += 80   # 代码匹配权重较高
                
                # 如果有匹配，添加到结果列表
                if score > 0:
                    matched_results.append((name, score))
            
            # 按匹配度分数降序排序
            matched_results.sort(key=lambda x: x[1], reverse=True)
            
            # 提取排序后的股票名称（去重）
            for name, score in matched_results:
                if name not in seen_names:
                    seen_names.add(name)
                    stock_names.append(name)
        
        # 返回排序后的所有匹配结果
        return jsonify(stock_names)
        
    except Exception as e:
        logging.error(f"搜索股票失败: {e}")
        return jsonify([])

@app.route('/search-results')
def search_results():
    # 获取搜索关键词
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        # 如果没有关键词，返回最新一天的数据
        latest_data = db.get_latest_day_data()
        return render_template('index.html', stocks=latest_data, search_mode=False)
    
    # 搜索所有日期的相关数据
    search_results = db.search_stocks_by_keyword(keyword)
    return render_template('index.html', stocks=search_results, search_mode=True, search_keyword=keyword)

@app.route('/get-data-by-date')
def get_data_by_date():
    # 获取指定日期
    date_str = request.args.get('date', '').strip()
    
    if not date_str:
        return jsonify([])
    
    # 获取指定日期的数据
    data = db.get_stock_data_by_date(date_str)
    return jsonify(data)

@app.route('/available-dates')
def get_available_dates():
    # 获取所有有数据的日期
    dates = db.get_available_dates()
    
    # 创建响应并设置缓存头
    response = make_response(jsonify(dates))
    response.headers['Cache-Control'] = 'public, max-age=300'  # 缓存5分钟
    
    # 生成ETag
    data_str = str(dates)
    etag = hashlib.md5(data_str.encode()).hexdigest()
    response.headers['ETag'] = etag
    
    return response

@app.route('/stock/<stock_code>')
def stock_detail(stock_code):
    # 获取股票历史数据
    history_data = db.get_stock_history_data(stock_code)
    return render_template('stock_detail.html', stock_code=stock_code, history_data=history_data)

@app.route('/api/realtime-stock-data')
def get_realtime_stock_data():
    # 获取请求参数中的股票代码列表
    symbols = request.args.get('symbols', '')
    if not symbols:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 构建API请求URL
        api_url = f'https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol={symbols}'
        
        # 设置请求头，模拟浏览器请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://xueqiu.com/'
        }
        
        # 发送请求获取数据
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # 抛出HTTP错误
        
        # 返回获取到的数据并设置缓存头
        result = response.json()
        api_response = make_response(jsonify(result))
        api_response.headers['Cache-Control'] = 'public, max-age=60'  # 缓存1分钟
        return api_response
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'请求失败: {str(e)}'}), 500

@app.route('/filter-by-plate')
def filter_by_plate():
    # 获取请求参数中的题材名称
    plate = request.args.get('plate', '')
    if not plate:
        return jsonify([])
    
    try:
        # 根据题材搜索股票数据
        filtered_stocks = db.search_stocks_by_plate(plate)
        return jsonify(filtered_stocks)
    except Exception as e:
        logging.error(f"筛选股票数据失败: {e}")
        return jsonify([])

@app.route('/api/time-sharing-data')
def get_time_sharing_data():
    # 获取请求参数中的股票代码
    code = request.args.get('code', '').strip()
    if not code:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 根据股票代码生成secid参数
        if code[0] == '6':
            market = '1'  # 沪市
        elif code[0] == '0' or code[0] == '3':
            market = '0'  # 深市
        else:
            return jsonify({'error': f'不支持的股票代码前缀: {code[0]}'}), 400
        
        secid = f"{market}.{code}"
        
        # 构建API请求URL
        api_url = f'https://push2.eastmoney.com/api/qt/stock/trends2/get?fields1=f1,f2,f8,f10&fields2=f51,f53,f56,f58&secid={secid}&ndays=1&iscr=0&iscca=0'
        
        # 设置请求头，模拟浏览器请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        # 发送请求获取数据
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # 抛出HTTP错误
        
        # 返回获取到的数据并设置缓存头
        result = response.json()
        api_response = make_response(jsonify(result))
        api_response.headers['Cache-Control'] = 'public, max-age=60'  # 缓存1分钟
        return api_response
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'请求失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

def scheduled_crawl():
    """定时执行股票数据抓取"""
    logging.info("定时任务开始执行: 抓取股票数据")
    # 强制更新今天的数据
    crawler.crawl_stock_data(crawl_today_only=True, force_update=True)
    logging.info("定时任务执行完成: 股票数据抓取已完成")

# 初始化定时任务调度器
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
# 添加定时任务：每天15:00执行
scheduler.add_job(scheduled_crawl, 'cron', hour=15, minute=0, second=0)

@app.before_first_request
def start_scheduler():
    """应用启动时启动定时任务"""
    if not scheduler.running:
        scheduler.start()
        logging.info("定时任务调度器已启动")

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """应用关闭时关闭定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        logging.info("定时任务调度器已关闭")

if __name__ == '__main__':
    # 确保templates目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    # 初始化数据库
    db.init_db()
    
    # 启动应用
    app.run(debug=True)