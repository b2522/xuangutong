// K线图相关变量
var kLineChart = null;
var volumeChart = null;
var currentHoveredStock = null;

// 生成secid参数
function generateSecid(stockCode) {
    if (!stockCode || typeof stockCode !== 'string') return null;
    // 根据股票代码开头判断市场
    if (stockCode.startsWith('6')) {
        return '1.' + stockCode; // 沪市
    } else if (stockCode.startsWith('3') || stockCode.startsWith('0')) {
        return '0.' + stockCode; // 深市
    }
    return null;
}

// 解析和绘制K线图的主函数
function parseAndDrawKLineChart(klineDataObj, stockCode) {
    // 获取容器
    var kLineContainer = document.getElementById('kLineChart');
    var volumeContainer = document.getElementById('volumeChart');
    if (!kLineContainer || !volumeContainer) {
        console.error('图表容器不存在');
        return;
    }
    
    // 解析K线数据
    var parsedData = parseKLineData(klineDataObj);
    if (!parsedData) {
        console.error('解析K线数据失败');
        return;
    }
    
    // 计算涨跌颜色
    var upDownColors = calculateUpDownColors(parsedData.klineData);
    
    // 绘制K线图 - 调整参数调用
    drawKLineChart(parsedData.dates, parsedData.klineData, parsedData.changePercentData);
    
    // 绘制成交量图 - 调整参数调用
    drawVolumeChart(parsedData.dates, parsedData.volumeData, parsedData.turnoverData, upDownColors);
    
    // 设置图表联动
    setupChartLinkage();
}

// 修改fetchKLineData函数，确保调用链正确
function fetchKLineData(stockCode, stockName) {
    var secid = generateSecid(stockCode);
    if (!secid) {
        console.error('无法生成有效的股票代码标识');
        return Promise.reject(new Error('无法生成有效的股票代码标识'));
    }
    
    // 获取今天的日期，格式化为YYYYMMDD
    var today = new Date();
    var endDate = today.getFullYear().toString() + 
                 (today.getMonth() + 1).toString().padStart(2, '0') + 
                 today.getDate().toString().padStart(2, '0');
    
    // 优化API请求参数，使用后端代理API
    var proxyUrl = `/api/proxy-eastmoney-kline-data?secid=${secid}&klt=101&fqt=1&lmt=250&end=${endDate}`;
    
    // 发送API请求获取数据
    return fetch(proxyUrl)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.json();
        })
        .then(function(data) {
            if (data && data.data) {
                // 更新弹窗标题
                document.getElementById('popupStockName').textContent = `${stockName}(${stockCode})`;
                // 解析和绘制图表，传递stockCode参数
                parseAndDrawKLineChart(data.data, stockCode);
            } else {
                throw new Error('API返回的数据格式不正确');
            }
        })
        .catch(function(error) {
            console.error('获取K线图数据失败:', error);
            document.getElementById('popupStockName').textContent = `获取数据失败`;
        });
}

// 绘制成交量图表
function drawVolumeChart(dates, volumeData, turnoverData, upDownColors) {
    // 初始化成交量图实例
    var volumeChartDom = document.getElementById('volumeChart');
    if (!volumeChartDom) return;
    
    if (!volumeChart) {
        volumeChart = echarts.init(volumeChartDom);
    } else {
        volumeChart.clear();
    }
    
    // 准备成交量数据，每个数据点包括日期、成交量和对应的颜色
    var volumeItems = [];
    for (var i = 0; i < volumeData.length; i++) {
        volumeItems.push({
            value: [dates[i], volumeData[i]],
            itemStyle: {
                color: upDownColors[i]
            }
        });
    }
    
    // 设置成交量图配置
    var option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                var date = params[0].axisValue;
                var index = dates.indexOf(date);
                var turnover = turnoverData[index];
                // 只显示日期和成交额
                return `日期: ${date}<br/>成交额: ${(turnover / 100000000).toFixed(2)}亿`;
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '0%',
            bottom: '30%' // 增加底部空间，使与时间调节器之间有更多距离
        },
        xAxis: {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: {onZero: false},
            splitLine: {show: false},
            axisTick: {show: false},
            axisLabel: {show: false}
        },
        yAxis: {
            scale: true,
            splitArea: {show: true},
            axisLine: {show: false},
            axisTick: {show: false},
            axisLabel: {
                show: false
            }
        },
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0],
                start: 50,
                end: 100
            },
            {
                show: true, // 打开成交量图的时间调节器
                xAxisIndex: [0],
                type: 'slider',
                bottom: '0%',
                start: 50,
                end: 100,
                height: 50, // 增加时间调节器高度，以便显示日期
                textStyle: {
                    fontSize: 12
                },
                borderColor: '#ddd',
                fillerColor: 'rgba(64, 158, 255, 0.2)',
                handleStyle: {
                    color: '#409EFF'
                }
            }
        ],
        series: [{
            name: '成交量',
            type: 'bar',
            data: volumeItems,
            // 设置柱状图样式
            itemStyle: {
                // 颜色由数据点指定，确保与K线图颜色一致
                borderRadius: [1, 1, 0, 0]
            }
        }]
    };
    
    // 应用配置
    volumeChart.setOption(option);
}

// 通用的涨跌颜色计算函数
function calculateUpDownColors(klineData) {
    var upDownColors = [];
    for (var i = 0; i < klineData.length; i++) {
        // 修改逻辑：收盘 >= 开盘 = 红色（上涨）
        // 收盘 < 开盘 = 绿色（下跌）
        if (klineData[i][1] >= klineData[i][0]) {
            upDownColors.push('#e33232');
        } else {
            upDownColors.push('#00a854');
        }
    }
    return upDownColors;
}

// 计算移动平均线(MA)指标
function calculateMA(dates, data, period) {
    var result = [];
    for (var i = 0; i < data.length; i++) {
        if (i < period - 1) {
            // 数据点不足，无法计算均线，使用null值占位
            result.push([dates[i], null]);
        } else {
            // 计算最近period个收盘价的平均值
            var sum = 0;
            for (var j = 0; j < period; j++) {
                sum += data[i - j][1]; // 第2个元素是收盘价
            }
            result.push([dates[i], sum / period]);
        }
    }
    return result;
}

// 绘制K线图
function drawKLineChart(dates, klineData, changePercentData) {
    // 初始化K线图实例
    var kLineChartDom = document.getElementById('kLineChart');
    if (!kLineChartDom) return;
    
    if (!kLineChart) {
        kLineChart = echarts.init(kLineChartDom);
    } else {
        kLineChart.clear();
    }
    
    // 计算MA均线数据 - 添加MA5, MA10, MA20三条均线
    var ma5Data = calculateMA(dates, klineData, 5);
    var ma10Data = calculateMA(dates, klineData, 10);
    var ma20Data = calculateMA(dates, klineData, 20);
    
    // 设置K线图配置
    var option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function(params) {
                var date = params[0].axisValue;
                var kline = params[0].data;
                var tooltipStr = `日期: ${date}<br/>开盘: ${kline[0].toFixed(2)}<br/>收盘: ${kline[1].toFixed(2)}<br/>最高: ${kline[2].toFixed(2)}<br/>最低: ${kline[3].toFixed(2)}`;
                
                var dataIndex = params[0].dataIndex;
                var changePercent = changePercentData[dataIndex].toFixed(2);
                var color = changePercent >= 0 ? 'red' : 'green';
                tooltipStr += `<br/>涨幅: <span style="color: ${color}">${changePercent}%</span>`;
                
                params.forEach(function(param) {
                    if (param.seriesName !== 'K线' && param.value[1] !== null) {
                        tooltipStr += `<br/>${param.seriesName}: ${param.value[1].toFixed(2)}`;
                    }
                });
                
                return tooltipStr;
            }
        },
        legend: {
            data: ['K线', 'MA5', 'MA10', 'MA20'],
            top: '0%' // 将图例移动到上方
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '10%',
            bottom: '10%' // 减小底部空间，使与成交量图更紧凑
        },
        xAxis: {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: {onZero: false},
            splitLine: {show: false},
            axisTick: {show: false},
            axisLabel: {
                show: true,
                formatter: function(value) {
                    // 只显示部分日期标签，避免重叠
                    var index = dates.indexOf(value);
                    return index % 10 === 0 ? value : '';
                }
            }
        },
        yAxis: {
            scale: true,
            splitArea: {show: true},
            axisLine: {show: false},
            axisTick: {show: false}
        },
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0],
                start: 50,
                end: 100
            },
            {
                show: false, // 隐藏K线图的时间调节器
                xAxisIndex: [0],
                type: 'slider',
                bottom: '0%',
                start: 50,
                end: 100,
                height: 30
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: klineData,
                // 设置K线图样式：阳线空心红色，阴线实心绿色
                itemStyle: {
                    color: '#e33232',     // 阳线填充颜色设为红色，实现实心效果
                    color0: '#00a854',    // 阴线填充颜色 - 绿色
                    borderColor: '#e33232', // 阳线边框颜色 - 红色
                    borderColor0: '#00a854' // 阴线边框颜色 - 绿色
                },
                emphasis: {
                    itemStyle: {
                        color: '#e33232',     // 保持阳线实心效果
                        color0: '#00a854',    // 阴线填充颜色
                        borderColor: '#e33232', // 阳线边框颜色
                        borderColor0: '#00a854' // 阴线边框颜色
                    }
                }
            },
            {
                name: 'MA5',
                type: 'line',
                data: ma5Data,
                smooth: true,
                lineStyle: {
                    width: 1,
                    color: '#808080' // 灰色
                },
                symbol: 'none'
            },
            {
                name: 'MA10',
                type: 'line',
                data: ma10Data,
                smooth: true,
                lineStyle: {
                    width: 1,
                    color: '#FFA500' // 橙色
                },
                symbol: 'none'
            },
            {
                name: 'MA20',
                type: 'line',
                data: ma20Data,
                smooth: true,
                lineStyle: {
                    width: 1,
                    color: '#FF00FF' // 洋红色
                },
                symbol: 'none'
            }
        ]
    };
    
    // 应用配置
    kLineChart.setOption(option);
}

// 设置图表联动逻辑，实现单一时间调节器同时控制两个图表
function setupChartLinkage() {
    if (kLineChart && volumeChart) {
        // 监听成交量图的数据缩放事件，同步到K线图
        volumeChart.on('dataZoom', function(params) {
            kLineChart.dispatchAction({
                type: 'dataZoom',
                start: params.start,
                end: params.end
            });
        });
        
        // 确保图表初始化时有相同的缩放状态
        kLineChart.dispatchAction({
            type: 'dataZoom',
            start: 50,
            end: 100
        });
        
        // 鼠标悬停联动 - K线图到成交量图
        kLineChart.on('mouseover', function(params) {
            if (params.componentType === 'series' && params.dataIndex !== undefined) {
                volumeChart.dispatchAction({
                    type: 'highlight',
                    seriesIndex: 0,
                    dataIndex: params.dataIndex
                });
            }
        });
        
        kLineChart.on('mouseout', function(params) {
            if (params.componentType === 'series' && params.dataIndex !== undefined) {
                volumeChart.dispatchAction({
                    type: 'downplay',
                    seriesIndex: 0,
                    dataIndex: params.dataIndex
                });
            }
        });
        
        // 鼠标悬停联动 - 成交量图到K线图
        volumeChart.on('mouseover', function(params) {
            if (params.componentType === 'series' && params.dataIndex !== undefined) {
                kLineChart.dispatchAction({
                    type: 'highlight',
                    seriesIndex: 0,
                    dataIndex: params.dataIndex
                });
            }
        });
        
        volumeChart.on('mouseout', function(params) {
            if (params.componentType === 'series' && params.dataIndex !== undefined) {
                kLineChart.dispatchAction({
                    type: 'downplay',
                    seriesIndex: 0,
                    dataIndex: params.dataIndex
                });
            }
        });
    }
}

// 显示K线图弹窗
function showKLinePopup(event, stockCode, stockName) {
    if (currentHoveredStock === stockCode) return; // 避免重复请求
    
    currentHoveredStock = stockCode;
    
    // 保存初始鼠标位置（相对于视口）
    var initialMouseX = event.clientX;
    var initialMouseY = event.clientY;
    
    // 设置弹窗位置
    var popup = document.getElementById('kLinePopup');
    if (!popup) return;
    
    // 先显示弹窗以获取其尺寸
    popup.style.display = 'block';
    popup.style.left = '-9999px';
    popup.style.top = '-9999px';
    
    // 获取弹窗尺寸
    var popupWidth = popup.offsetWidth;
    var popupHeight = popup.offsetHeight;
    
    // 计算弹窗位置（相对于视口）
    var x = initialMouseX + 15;
    var y = initialMouseY + 15;
    
    // 确保弹窗不会超出视口右侧
    if (x + popupWidth > window.innerWidth) {
        x = initialMouseX - popupWidth - 15;
    }
    // 确保弹窗不会超出视口底部
    if (y + popupHeight > window.innerHeight) {
        y = initialMouseY - popupHeight - 15;
    }
    // 确保弹窗不会超出视口左侧
    if (x < 0) {
        x = 10;
    }
    // 确保弹窗不会超出视口顶部
    if (y < 0) {
        y = 10;
    }
    
    // 转换为相对于文档的坐标
    popup.style.left = (x + window.scrollX) + 'px';
    popup.style.top = (y + window.scrollY) + 'px';
    
    // 延迟获取K线图数据，确保弹窗DOM完全渲染
    setTimeout(function() {
        fetchKLineData(stockCode, stockName);
        
        // 在数据加载完成后重新调整弹窗位置
        setTimeout(function() {
            adjustPopupPosition(initialMouseX, initialMouseY);
        }, 500);
    }, 100);
}

// 调整弹窗位置
function adjustPopupPosition(mouseX, mouseY) {
    var popup = document.getElementById('kLinePopup');
    if (!popup) return;
    
    // 获取弹窗实际尺寸
    var popupWidth = popup.offsetWidth;
    var popupHeight = popup.offsetHeight;
    
    // 计算弹窗位置（相对于视口）
    var x = mouseX + 15;
    var y = mouseY + 15;
    
    // 确保弹窗不会超出视口右侧
    if (x + popupWidth > window.innerWidth) {
        x = mouseX - popupWidth - 15;
    }
    // 确保弹窗不会超出视口底部
    if (y + popupHeight > window.innerHeight) {
        y = mouseY - popupHeight - 15;
    }
    // 确保弹窗不会超出视口左侧
    if (x < 0) {
        x = 10;
    }
    // 确保弹窗不会超出视口顶部
    if (y < 0) {
        y = 10;
    }
    
    // 转换为相对于文档的坐标
    popup.style.left = (x + window.scrollX) + 'px';
    popup.style.top = (y + window.scrollY) + 'px';
}

// 关闭K线图弹窗
function closeKLinePopup() {
    var popup = document.getElementById('kLinePopup');
    if (popup) {
        popup.style.display = 'none';
    }
    currentHoveredStock = null;
}

// 为股票名称链接添加鼠标事件
function initStockNameEvents() {
    // 等待DOM加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            attachStockNameEventListeners();
        });
    } else {
        attachStockNameEventListeners();
    }
}

// 绑定股票名称的鼠标事件监听器
function attachStockNameEventListeners() {
    var stockLinks = document.querySelectorAll('.stock-name-link');
    Array.prototype.forEach.call(stockLinks, function(link) {
        link.addEventListener('mouseenter', function(event) {
            // 获取股票代码（从父行的第五列获取）
            var row = link.closest('tr');
            var codeElement = row.querySelector('td:nth-child(5)');
            if (codeElement) {
                var stockCode = codeElement.textContent.trim();
                var stockName = link.textContent.trim();
                showKLinePopup(event, stockCode, stockName);
            }
        });
        
        link.addEventListener('mouseleave', function() {
            // 延迟关闭，避免鼠标快速移动时频繁开关
            setTimeout(function() {
                // 检查鼠标是否还在弹窗上
                var popup = document.getElementById('kLinePopup');
                var isOverPopup = popup && popup.matches(':hover');
                if (!isOverPopup) {
                    closeKLinePopup();
                }
            }, 100);
        });
    });
    
    // 为弹窗添加鼠标悬停事件，避免快速关闭
    var popup = document.getElementById('kLinePopup');
    if (popup) {
        popup.addEventListener('mouseenter', function() {
            // 鼠标进入弹窗，保持显示
        });
        
        popup.addEventListener('mouseleave', function() {
            closeKLinePopup();
        });
    }
}

// 窗口大小变化时调整图表大小
window.addEventListener('resize', function() {
    if (kLineChart) {
        kLineChart.resize();
    }
    if (volumeChart) {
        volumeChart.resize();
    }
    if (profitRatioChart) {
        profitRatioChart.resize();
    }
});

// 页面加载完成后初始化
window.addEventListener('load', function() {
    initStockNameEvents();
});

// 添加解析K线数据的工具函数
function parseKLineData(data) {
    var dates = data.klines.map(function(kline) {
        var parts = kline.split(',');
        return parts[0]; // f51: 日期
    });
    
    var klineData = data.klines.map(function(kline) {
        var parts = kline.split(',');
        // 数据顺序为 [开盘, 收盘, 最高, 最低] 符合ECharts的K线图要求
        return [
            parseFloat(parts[1]), // f52: 开盘
            parseFloat(parts[2]), // f53: 收盘
            parseFloat(parts[3]), // f54: 最高
            parseFloat(parts[4])  // f55: 最低
        ];
    });
    
    // 解析成交量数据
    var volumeData = data.klines.map(function(kline) {
        var parts = kline.split(',');
        return parseFloat(parts[5]); // f56: 成交量
    });
    
    // 解析成交额数据
    var turnoverData = data.klines.map(function(kline) {
        var parts = kline.split(',');
        return parseFloat(parts[6]); // f57: 成交额
    });
    
    // 解析涨跌幅数据
    var changePercentData = data.klines.map(function(kline) {
        var parts = kline.split(',');
        return parseFloat(parts[8]); // f59: 涨跌额
    });
    
    return {
        dates: dates,
        klineData: klineData,
        volumeData: volumeData,
        turnoverData: turnoverData,
        changePercentData: changePercentData
    };
}

// 获取获利比例数据
function fetchProfitRatioData(stockCode, days) {
    var apiUrl = '/api/profit-ratio-data?stock_code=' + stockCode + '&days=' + days;
    
    return fetch(apiUrl)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.json();
        })
        .then(function(data) {
            if (data && data.status === 'success' && data.data) {
                return data.data;
            } else {
                throw new Error('API返回的数据格式不正确');
            }
        })
        .catch(function(error) {
            console.error('获取获利比例数据失败:', error);
            return null;
        });
}

// 绘制获利比例图
function drawProfitRatioChart(dates, profitRatioData) {
    var profitRatioChartDom = document.getElementById('profitRatioChart');
    if (!profitRatioChartDom) {
        console.error('获利比例图容器不存在');
        return;
    }
    
    if (!profitRatioChart) {
        profitRatioChart = echarts.init(profitRatioChartDom);
    } else {
        profitRatioChart.clear();
    }
    
    // 准备数据
    var data = [];
    for (var i = 0; i < dates.length && i < profitRatioData.length; i++) {
        var profitRatio = profitRatioData[i];
        var numericProfitRatio = parseFloat(profitRatio);
        if (!isNaN(numericProfitRatio)) {
            data.push([dates[i], numericProfitRatio]);
        }
    }
    
    if (data.length === 0) {
        console.warn('没有有效的获利比例数据');
        return;
    }
    
    // 设置获利比例图配置
    var option = {
        animation: false,
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function(params) {
                var date = params[0].axisValue;
                var profitRatio = params[0].data[1];
                return `日期: ${date}<br/>获利比例: ${Math.round(profitRatio)}%`;
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '10%',
            bottom: '30%'
        },
        xAxis: {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: {onZero: false},
            splitLine: {show: false},
            axisTick: {show: false},
            axisLabel: {
                show: false
            }
        },
        yAxis: {
            scale: true,
            splitArea: {show: true},
            axisLine: {show: false},
            axisTick: {show: false},
            axisLabel: {
                formatter: function(value) {
                    return Math.round(value) + '%';
                }
            },
            min: 0,
            max: 100
        },
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0],
                start: 50,
                end: 100
            },
            {
                show: false,
                xAxisIndex: [0],
                type: 'slider',
                bottom: '0%',
                start: 50,
                end: 100,
                height: 30
            }
        ],
        series: [{
            name: '获利比例',
            type: 'line',
            data: data,
            smooth: true,
            lineStyle: {
                width: 2,
                color: '#FF6B6B'
            },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0, color: 'rgba(255, 107, 107, 0.3)'
                    }, {
                        offset: 1, color: 'rgba(255, 107, 107, 0.05)'
                    }]
                }
            },
            itemStyle: {
                color: function(params) {
                    return params.data[1] < 6 ? '#00a854' : '#FF6B6B';
                }
            },
            symbol: 'circle',
            symbolSize: 4,
            markLine: {
                symbol: ['none', 'none'],
                data: [{
                    yAxis: 6,
                    lineStyle: {
                        type: 'dashed',
                        color: '#999'
                    },
                    label: {
                        formatter: '6%',
                        position: 'start'
                    }
                }]
            }
        }]
    };
    
    // 应用配置
    console.log('应用获利比例图配置');
    profitRatioChart.setOption(option);
}