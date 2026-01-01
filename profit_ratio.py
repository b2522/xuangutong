import logging
import requests
import json
import pandas as pd
from datetime import datetime
import os
from flask import Flask, render_template, request, jsonify
from typing import Dict, List, Tuple, Optional

# 创建logs目录（如果不存在）
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'web_app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChipDistributionAnalyzer:
    """筹码分布分析器"""
    
    def __init__(self, kdata: pd.DataFrame, accuracy_factor: int = 150, calc_range: Optional[int] = None):
        """
        初始化筹码分布分析器
        
        Args:
            kdata: K线数据，必须包含 [开盘, 收盘, 最高, 最低, 成交量, 换手率] 等字段
            accuracy_factor: 精度因子，决定价格分割的精度
            calc_range: 计算的K线范围，默认使用全部数据
        """
        self._validate_data(kdata)
        self.kdata = kdata
        self.factor = accuracy_factor
        self.range = calc_range

    def _validate_data(self, kdata: pd.DataFrame) -> None:
        """
        验证输入数据的完整性
        
        Args:
            kdata: 待验证的K线数据
            
        Raises:
            ValueError: 当数据不完整或格式不正确时抛出
        """
        required_columns = ['开盘', '收盘', '最高', '最低', '成交量', '换手率']
        missing_columns = [col for col in required_columns if col not in kdata.columns]
        if missing_columns:
            raise ValueError(f"K线数据缺少必要字段: {missing_columns}")

    def calculate_chip_distribution(self, index: int) -> Dict:
        """
        计算指定位置的筹码分布
        
        Args:
            index: K线位置索引
            
        Returns:
            包含筹码分布结果的字典
        """
        # 确定计算范围
        start = max(0, index - self.range + 1) if self.range else 0
        kdata = self.kdata.iloc[start:index + 1]
        
        # 确定价格范围
        max_price = max(kdata['最高'].values)
        min_price = min(kdata['最低'].values)
        
        # 计算精度
        accuracy = max(0.01, (max_price - min_price) / (self.factor - 1))
        
        # 初始化分布数组
        price_range = [round(min_price + accuracy * i, 2) for i in range(self.factor)]
        distribution = [0] * self.factor
        
        # 计算每个K线的贡献
        for _, row in kdata.iterrows():
            distribution = self._calculate_k_line_contribution(
                row, distribution, min_price, accuracy, price_range
            )
        
        result = self._calculate_distribution_metrics(
            distribution, price_range, self.kdata['收盘'].iloc[index]
        )
        # 添加日期信息
        result['date'] = self.kdata['日期'].iloc[index]
        return result

    def _calculate_k_line_contribution(
        self, 
        kline: pd.Series, 
        distribution: List[float],
        min_price: float,
        accuracy: float,
        price_range: List[float]
    ) -> List[float]:
        """
        计算单个K线对筹码分布的贡献
        
        Args:
            kline: 单个K线数据
            distribution: 现有筹码分布
            min_price: 最小价格
            accuracy: 价格精度
            price_range: 价格范围数组
            
        Returns:
            更新后的筹码分布
        """
        open_price = kline['开盘']
        close_price = kline['收盘']
        high_price = kline['最高']
        low_price = kline['最低']
        turnover_rate = min(1, kline['换手率'] / 100)
        
        # 计算平均价格
        avg_price = (open_price + close_price + high_price + low_price) / 4
        
        # 计算价格区间索引
        low_idx = max(0, int((low_price - min_price) / accuracy))
        high_idx = min(self.factor - 1, int((high_price - min_price) / accuracy))
        
        # 衰减现有筹码
        distribution = [d * (1 - turnover_rate) for d in distribution]
        
        # 一字板特殊处理
        if high_price == low_price:
            idx = int((high_price - min_price) / accuracy)
            distribution[idx] += turnover_rate / 2
        else:
            # 计算三角形分布
            for idx in range(low_idx, high_idx + 1):
                price = price_range[idx]
                if price <= avg_price:
                    weight = (price - low_price) / (avg_price - low_price)
                else:
                    weight = (high_price - price) / (high_price - avg_price)
                distribution[idx] += weight * turnover_rate
                
        return distribution

    def _calculate_distribution_metrics(
        self,
        distribution: List[float],
        price_range: List[float],
        current_price: float
    ) -> Dict:
        """
        计算筹码分布的各项指标
        
        Args:
            distribution: 筹码分布数组
            price_range: 价格范围数组
            current_price: 当前价格
            
        Returns:
            包含各项指标的字典
        """
        total_weight = sum(distribution)
        if total_weight == 0:
            return {
                'profit_ratio': 0,
                'avg_cost': 0,
                'cost_90_range': (0, 0),
                'concentration_90': 0,
                'cost_70_range': (0, 0),
                'concentration_70': 0,
                'prices': price_range,
                'distribution': distribution,
                'current_price': current_price
            }

        # 计算平均成本
        avg_cost = sum(p * d for p, d in zip(price_range, distribution)) / total_weight
        
        # 计算获利比例 - 正确的逻辑应该是计算当前价格以下的筹码占比
        # 因为如果当前价格高于买入成本，那么这个筹码就是获利的
        profit_ratio = sum(d for p, d in zip(price_range, distribution) if p <= current_price) / total_weight
        
        # 计算成本区间
        cost_90_range, concentration_90 = self._calculate_cost_range(
            price_range, distribution, total_weight, 0.9
        )
        cost_70_range, concentration_70 = self._calculate_cost_range(
            price_range, distribution, total_weight, 0.7
        )
        
        return {
            'prices': price_range,
            'distribution': distribution,
            'current_price': current_price,
            'profit_ratio': profit_ratio,
            'avg_cost': avg_cost,
            'cost_90_range': cost_90_range,
            'concentration_90': concentration_90,
            'cost_70_range': cost_70_range,
            'concentration_70': concentration_70
        }

    def _calculate_cost_range(
        self,
        price_range: List[float],
        distribution: List[float],
        total_weight: float,
        threshold: float
    ) -> Tuple[Tuple[float, float], float]:
        """
        计算指定比例的成本区间
        
        Args:
            price_range: 价格范围数组
            distribution: 筹码分布数组
            total_weight: 总权重
            threshold: 阈值(如0.9表示90%)
            
        Returns:
            (成本区间元组, 集中度)
        """
        sorted_prices = sorted(
            [(p, d) for p, d in zip(price_range, distribution)],
            key=lambda x: x[1],
            reverse=True
        )
        
        cumsum = 0
        cost_low = float('inf')
        cost_high = float('-inf')
        
        for price, dist in sorted_prices:
            cumsum += dist
            cost_low = min(cost_low, price)
            cost_high = max(cost_high, price)
            if cumsum >= threshold * total_weight:
                break
                
        concentration = (
            (cost_high - cost_low) / (cost_high + cost_low) * 100 
            if cost_high + cost_low > 0 else 0
        )
        
        return (cost_low, cost_high), concentration

def get_stock_data_from_api(stock_code, days=30, end_date=None):
    """
    从东方财富API获取股票K线数据，强制使用真实数据
    
    Args:
        stock_code (str): 股票代码
        days (int): 获取的天数
        end_date (str): 结束日期，格式为YYYYMMDD
    
    Returns:
        pd.DataFrame: 处理后的股票数据
    
    Raises:
        Exception: 当无法从API获取数据时抛出异常
    """
    logger.info(f"正在从东方财富API获取股票 {stock_code} 的真实数据，获取 {days} 天")
    
    # 处理可能带有交易所前缀的股票代码（如SZ.000001或SH.600000）
    if '.' in stock_code:
        # 提取股票代码部分（去除交易所前缀）
        stock_code = stock_code.split('.')[-1]
    
    # 根据股票代码前缀设置正确的secid参数
    if stock_code.startswith('6'):
        secid = f'1.{stock_code}'  # 沪市股票
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        secid = f'0.{stock_code}'  # 深市股票
    else:
        raise ValueError(f"不支持的股票代码格式: {stock_code}")
    
    # 获取今天的日期，格式为YYYYMMDD
    today = datetime.now().strftime('%Y%m%d')
    # 如果提供了end_date，则使用它，否则使用今天的日期
    if end_date:
        # 尝试解析end_date参数，支持多种日期格式（如YYYY-MM-DD、YYYY/MM/DD、YYYYMMDD）
        try:
            # 尝试解析不同格式的日期
            if '-' in end_date or '/' in end_date:
                # 处理带分隔符的日期格式（YYYY-MM-DD或YYYY/MM/DD）
                end_date_obj = datetime.strptime(end_date.replace('/', '-'), '%Y-%m-%d')
                end_date = end_date_obj.strftime('%Y%m%d')
            # 如果已经是YYYYMMDD格式，则直接使用
            logger.info(f"使用转换后的结束日期: {end_date}")
        except ValueError:
            # 如果解析失败，使用今天的日期
            logger.warning(f"无效的结束日期格式: {end_date}，使用今天的日期代替")
            end_date = today
    else:
        end_date = today
    logger.info(f"最终使用的结束日期: {end_date}")
    
    # 使用用户提供的正确API参数格式
    params = {
        'secid': secid,
        'klt': '101',  # 日K线
        'fqt': '1',     # 前复权
        'lmt': days,    # 获取数据的条数
        'end': end_date,   # 结束日期
        'iscca': '1',
        'fields1': 'f1,f2,f3,f4,f5',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f59,f61',
        'ut': 'f057cbcbce2a86e2866ab8877db1d059',
        'forcect': '1'
    }
    
    api_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
    # 设置请求头，模拟浏览器请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Referer': 'https://data.eastmoney.com/',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # 发送请求到东方财富API
        logger.info(f"发送API请求: {api_url}")
        logger.info(f"API请求参数: {params}")
        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        logger.info(f"API响应状态码: {response.status_code}")
        logger.info(f"API响应头: {dict(response.headers)}")
        logger.info(f"API响应内容完整长度: {len(response.text)} 字符")
        logger.info(f"API响应内容: {response.text}")  # 记录完整响应内容
        response.raise_for_status()  # 如果请求失败会抛出异常
        
        # 解析响应数据
        data = response.json()
        logger.info(f"API响应解析后的数据类型: {type(data)}")
        logger.info(f"API响应解析后的数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 检查API返回状态
        if data.get('rc') == 0:
            logger.info("API请求成功")
            if data.get('data'):
                logger.info(f"API返回data字段: {json.dumps(data['data'], ensure_ascii=False)[:2000]}")
                if data['data'].get('klines'):
                    # 提取K线数据
                    klines = data['data'].get('klines', [])
                    
                    if klines:
                        logger.info(f"成功获取股票 {stock_code} 的 {len(klines)} 条K线数据")
                    else:
                        raise Exception(f"未获取到股票 {stock_code} 的K线数据")
                else:
                    raise Exception(f"API响应中没有klines字段")
            else:
                raise Exception(f"API响应中没有data字段")
        else:
            raise Exception(f"API返回错误: rc={data.get('rc')}, msg={data.get('msg', 'Unknown error')}")
        
        # 解析K线数据
        stock_data = []
        for kline in klines:
            # 数据格式: "日期,开盘价,收盘价,最高价,最低价,成交量,成交额,涨跌幅,换手率"
            fields = kline.split(',')
            if len(fields) >= 9:
                stock_data.append({
                    '日期': fields[0],
                    '开盘': float(fields[1]),
                    '收盘': float(fields[2]),
                    '最高': float(fields[3]),
                    '最低': float(fields[4]),
                    '成交量': float(fields[5]),
                    '成交额': float(fields[6]),
                    '涨跌幅': float(fields[7]),
                    '换手率': float(fields[8])
                })
        
        # 创建DataFrame
        df = pd.DataFrame(stock_data)
        
        # 验证数据是否为空
        if df.empty:
            error_msg = f"未获取到股票 {stock_code} 的有效数据"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        return df
        
    except requests.exceptions.RequestException as e:
        error_msg = f"请求东方财富API时出错: {str(e)}"
        logger.error(error_msg)
        # 不再回退到模拟数据，强制要求使用真实数据
        raise Exception(error_msg)
    except (ValueError, KeyError, IndexError) as e:
        error_msg = f"解析API响应数据时出错: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"获取股票 {stock_code} 数据时发生未知错误: {str(e)}"
        logger.error(error_msg)
        # 不使用模拟数据，直接抛出异常
        raise Exception(error_msg)

class SimpleProfitRatioCalculator:
    """
    股票获利比例计算器，使用真实API数据
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_historical_profit_ratio(self, stock_code, days=7, end_date=None):
        """
        计算指定股票在过去几天的历史获利比例
        使用真实的东方财富API数据
        
        Args:
            stock_code (str): 股票代码
            days (int): 计算的天数
            end_date (str): 结束日期，格式为YYYYMMDD
            
        Returns:
            list: 包含日期和获利比例的列表，获利比例以百分比表示，保留两位小数
        
        Raises:
            Exception: 当无法获取数据或计算失败时抛出异常
        """
        self.logger.info(f"开始计算股票 {stock_code} 的历史获利比例数据，请求天数: {days}")
        
        try:
            # 从东方财富API获取真实股票数据
            # 无论用户请求多少天，我们都获取足够的数据来计算筹码分布（至少120天）
            required_days = max(days, 120)
            self.logger.info(f"需要获取的股票数据天数: {required_days}")
            stock_data = get_stock_data_from_api(stock_code, days=required_days, end_date=end_date)
            self.logger.info(f"成功获取股票数据，数据长度: {len(stock_data)} 条")
            
            # 创建ChipDistributionAnalyzer实例，设置calc_range=120与huoli.py保持一致
            self.logger.info("创建筹码分布分析器实例")
            analyzer = ChipDistributionAnalyzer(stock_data, accuracy_factor=150, calc_range=120)
            
            # 计算每一天的获利比例
            self.logger.info("开始计算每一天的获利比例")
            result = []
            for i in range(len(stock_data)):
                self.logger.debug(f"计算第 {i} 天的筹码分布，日期: {stock_data['日期'].iloc[i]}")
                distribution = analyzer.calculate_chip_distribution(i)
                
                # 获取数据
                date = distribution['date']
                profit_ratio = distribution['profit_ratio']
                
                result.append({
                    '日期': date,
                    '获利比例': round(profit_ratio * 100, 2)  # 转换为百分比并保留两位小数
                })
            
            # 只返回用户请求的天数的数据
            returned_data = result[-days:] if days <= len(result) else result
            self.logger.info(f"完成计算股票 {stock_code} 的历史获利比例数据，返回 {len(returned_data)} 条记录")
            return returned_data
            
        except Exception as e:
            error_msg = f"计算股票 {stock_code} 的历史获利比例时出错: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

# Flask应用初始化
# 注意：此文件已作为模块集成到app.py中
# 独立运行功能已被删除，相关代码已迁移到app.py中