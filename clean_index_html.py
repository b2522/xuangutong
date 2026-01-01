import shutil

# 读取原始文件
with open('c:\\Users\\Administrator\\Documents\\trae_projects\\xuangutong\\templates\\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 保留前104行（包括第104行的<script src="/static/js/main.js"></script>）
# 保留第694行及之后的内容（从</script>开始）
# 删除第105行到第693行的所有内容

new_lines = lines[:104] + lines[693:]

# 写入新文件
with open('c:\\Users\\Administrator\\Documents\\trae_projects\\xuangutong\\templates\\index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"原始文件行数: {len(lines)}")
print(f"新文件行数: {len(new_lines)}")
print(f"删除了 {len(lines) - len(new_lines)} 行")
