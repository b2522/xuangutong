import datetime

# 模拟前端的日期验证逻辑
def is_weekend(date_str):
    """检查日期是否为周末"""
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    
    date = datetime.datetime(year, month, day)
    # 0是周一，6是周日
    return date.weekday() >= 5

def is_valid_date_format(date_str):
    """检查日期格式是否正确"""
    # 检查是否为8位数字
    if not date_str.isdigit() or len(date_str) != 8:
        return False
    
    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        # 检查日期是否有效
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

def validate_date_selection(date_str, available_dates):
    """模拟前端完整的日期验证逻辑"""
    # 检查日期格式
    if not is_valid_date_format(date_str):
        return {
            'valid': False,
            'message': '日期格式不正确，请输入8位数字，格式为YYYYMMDD'
        }
    
    # 检查是否为周末
    if is_weekend(date_str):
        return {
            'valid': False,
            'message': '周末没有股票数据，请选择工作日'
        }
    
    # 检查日期是否在可用列表中
    if date_str not in available_dates:
        return {
            'valid': False,
            'message': '该日期没有数据，请选择其他日期'
        }
    
    # 验证通过
    return {
        'valid': True,
        'message': '日期验证通过'
    }

# 模拟从后端获取的可用日期列表
def get_available_dates_from_backend():
    # 这些是数据库中实际存在的日期
    return [
        '20251223', '20251222', '20251219', '20251218', '20251217', 
        '20251216', '20251215', '20251212', '20251211', '20251210', 
        '20251209', '20251208', '20251205', '20251204', '20251203', 
        '20251202', '20251201'
    ]

# 测试可能的问题点
def test_date_validation():
    print('=== 日期验证逻辑测试 ===')
    
    # 获取可用日期列表
    available_dates = get_available_dates_from_backend()
    test_date = '20251223'
    
    print(f'测试日期: {test_date}')
    print(f'可用日期列表: {available_dates}')
    print(f'{test_date} 是否在可用日期列表中: {test_date in available_dates}')
    
    # 检查日期格式
    print(f'日期格式是否正确: {is_valid_date_format(test_date)}')
    
    # 检查是否为周末
    print(f'是否为周末: {is_weekend(test_date)}')
    
    # 执行完整验证
    result = validate_date_selection(test_date, available_dates)
    print(f'验证结果: {result}')
    
    # 检查字符串比较问题
    print('\n=== 字符串比较问题检查 ===')
    
    # 检查列表中的第一个元素
    first_date = available_dates[0]  # 应该是'20251223'
    print(f'列表中第一个日期: "{first_date}"')
    print(f'类型比较: type(test_date) == type(first_date) ? {type(test_date) == type(first_date)}')
    print(f'值比较: test_date == first_date ? {test_date == first_date}')
    print(f'身份比较: test_date is first_date ? {test_date is first_date}')
    
    # 检查可能的空格或特殊字符
    print(f'测试日期长度: {len(test_date)}')
    print(f'去除空格后比较: {test_date.strip() == first_date.strip()}')
    
    # 检查字符编码
    print(f'字符编码 (测试日期): {[ord(c) for c in test_date]}')
    print(f'字符编码 (列表中日期): {[ord(c) for c in first_date]}')
    
    # 检查可能的缓存问题
    print('\n=== 可能的缓存或异步加载问题 ===')
    print('1. 前端可能在初始加载时缓存了可用日期列表')
    print('2. 当新数据(20251223)添加到数据库后，前端没有更新缓存')
    print('3. 前端可能在加载可用日期列表时出错或中断')
    
    # 检查后端数据获取逻辑
    print('\n=== 后端数据获取逻辑检查 ===')
    print('模拟前端从后端API获取数据:')
    print('- 可能的URL: /get-available-dates')
    print('- 可能的问题: API返回的数据与数据库实际数据不一致')
    
    # 常见前端错误模式
    print('\n=== 常见前端错误模式 ===')
    print('1. 日期格式转换错误: 字符串 vs 数字 vs Date对象')
    print('2. 异步加载顺序问题: 先验证后获取可用日期')
    print('3. 缓存过期: 没有刷新缓存机制')
    print('4. 字符串比较中的空格或特殊字符')
    print('5. 数据类型不一致: 如"20251223" vs 20251223')
    
    # 检查日期转换问题
    print('\n=== 日期转换问题 ===')
    # 尝试将字符串转换为其他类型
    print(f'字符串转整数: {int(test_date)}')
    print(f'整数转字符串: {str(int(test_date))}')
    print(f'字符串转整数后再转字符串: {str(int(test_date)) == test_date}')
    
    return result

# 运行测试
if __name__ == '__main__':
    test_result = test_date_validation()
    print('\n=== 测试总结 ===')
    print(f'测试日期 {test_result["valid"] and "通过" or "失败"} 验证: {test_result["message"]}')
    
    # 提出修复建议
    print('\n=== 修复建议 ===')
    print('1. 确保前端在每次验证前从后端获取最新的可用日期列表')
    print('2. 在前端实现刷新缓存的机制，特别是在数据更新后')
    print('3. 加强日期字符串比较的健壮性，确保类型一致')
    print('4. 添加详细的日志记录，方便调试验证过程')
    print('5. 考虑修改前端验证逻辑，允许在本地缓存无效时直接向后端请求数据')
