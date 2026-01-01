"""
移除main.js中的所有console.log调试语句
"""
import re

# 读取文件
with open('static/js/main.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 移除console.log语句（包括单行和多行）
# 匹配 console.log(...) 或 console.log`...` 的模式
pattern = r'console\.log\([^)]*\);?\s*'

# 替换为空字符串
content = re.sub(pattern, '', content)

# 写回文件
with open('static/js/main.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("已移除所有console.log调试语句")
