// 日期选择器验证逻辑测试脚本

/**
 * 检查日期是否为周末
 * @param {string} dateStr - 日期字符串，格式为YYYYMMDD
 * @returns {boolean} - 如果是周末返回true，否则返回false
 */
function isWeekend(dateStr) {
    const year = parseInt(dateStr.substr(0, 4));
    const month = parseInt(dateStr.substr(4, 2)) - 1; // JavaScript月份从0开始
    const day = parseInt(dateStr.substr(6, 2));
    
    const date = new Date(year, month, day);
    const dayOfWeek = date.getDay(); // 0是周日，6是周六
    
    return dayOfWeek === 0 || dayOfWeek === 6;
}

/**
 * 检查日期格式是否正确
 * @param {string} dateStr - 日期字符串，格式为YYYYMMDD
 * @returns {boolean} - 如果格式正确返回true，否则返回false
 */
function isValidDateFormat(dateStr) {
    // 检查格式是否为8位数字
    const regex = /^\d{8}$/;
    if (!regex.test(dateStr)) {
        return false;
    }
    
    // 检查日期是否合法
    const year = parseInt(dateStr.substr(0, 4));
    const month = parseInt(dateStr.substr(4, 2)) - 1;
    const day = parseInt(dateStr.substr(6, 2));
    
    const date = new Date(year, month, day);
    return date.getFullYear() === year && 
           date.getMonth() === month && 
           date.getDate() === day;
}

/**
 * 模拟前端的日期验证逻辑
 * @param {string} dateStr - 日期字符串，格式为YYYYMMDD
 * @param {Array} availableDates - 可用日期列表
 * @returns {Object} - 包含验证结果和消息
 */
function validateDateSelection(dateStr, availableDates) {
    // 检查日期格式
    if (!isValidDateFormat(dateStr)) {
        return {
            valid: false,
            message: '日期格式不正确，请输入8位数字，格式为YYYYMMDD'
        };
    }
    
    // 检查是否为周末
    if (isWeekend(dateStr)) {
        return {
            valid: false,
            message: '周末没有股票数据，请选择工作日'
        };
    }
    
    // 检查日期是否在可用列表中
    if (!availableDates.includes(dateStr)) {
        return {
            valid: false,
            message: '该日期没有数据，请选择其他日期'
        };
    }
    
    // 验证通过
    return {
        valid: true,
        message: '日期验证通过'
    };
}

/**
 * 模拟可用日期列表，从后端获取的逻辑
 * 在前端代码中，这个列表可能是通过API获取的
 */
function getAvailableDatesFromBackend() {
    // 模拟从后端获取的可用日期列表
    // 根据之前的数据库检查，20251223确实在可用日期列表中
    return [
        '20251223', '20251222', '20251219', '20251218', '20251217', 
        '20251216', '20251215', '20251212', '20251211', '20251210', 
        '20251209', '20251208', '20251205', '20251204', '20251203', 
        '20251202', '20251201'
    ];
}

/**
 * 测试函数，检查20251223日期是否能够通过验证
 */
function testDateValidation() {
    console.log('=== 日期验证逻辑测试 ===');
    
    // 获取可用日期列表
    const availableDates = getAvailableDatesFromBackend();
    console.log('可用日期列表:', availableDates);
    console.log('20251223是否在可用日期列表中:', availableDates.includes('20251223'));
    
    // 检查20251223是否为周末
    console.log('20251223是否为周末:', isWeekend('20251223'));
    
    // 检查20251223的日期格式
    console.log('20251223日期格式是否正确:', isValidDateFormat('20251223'));
    
    // 执行完整验证
    const result = validateDateSelection('20251223', availableDates);
    console.log('20251223验证结果:', result);
    
    // 检查可能的日期格式问题
    console.log('\n=== 检查可能的日期格式问题 ===');
    
    // 检查日期字符串类型转换
    const dateStr = '20251223';
    console.log('字符串"20251223"的类型:', typeof dateStr);
    
    // 检查字符串比较
    const dateInList = availableDates[0]; // 应该是'20251223'
    console.log('列表中第一个日期:', dateInList, '类型:', typeof dateInList);
    console.log('"20251223" === "20251223" ?', dateStr === dateInList);
    
    // 检查字符串长度
    console.log('"20251223"的长度:', dateStr.length);
    
    // 检查可能的空格或特殊字符
    console.log('去除首尾空格后比较:', dateStr.trim() === dateInList.trim());
    console.log('字符编码检查:', Array.from(dateStr).map(c => c.charCodeAt(0)));
    
    // 检查日期解析
    console.log('\n=== 日期解析检查 ===');
    const year = parseInt(dateStr.substr(0, 4));
    const month = parseInt(dateStr.substr(4, 2));
    const day = parseInt(dateStr.substr(6, 2));
    console.log(`解析后的年月日: ${year}-${month}-${day}`);
    
    // 检查日期实例
    const dateObj = new Date(year, month - 1, day);
    console.log('日期对象:', dateObj.toISOString());
    
    return result;
}

// 运行测试
const testResult = testDateValidation();
console.log('\n=== 测试总结 ===');
console.log(`20251223日期验证${testResult.valid ? '通过' : '失败'}: ${testResult.message}`);

// 如果测试失败，尝试找出可能的解决方案
if (!testResult.valid) {
    console.log('\n=== 可能的解决方案 ===');
    console.log('1. 检查availableDates列表是否与后端实际返回的一致');
    console.log('2. 确保日期字符串比较时没有格式或类型问题');
    console.log('3. 检查前端代码中是否有缓存旧数据的情况');
    console.log('4. 验证后端API返回的日期格式是否正确');
}
