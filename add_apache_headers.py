#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有Python源文件添加Apache 2.0许可证头部
"""

import os

APACHE_HEADER = '''# Copyright 2026 Windows Stock Monitor Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''

def add_header_to_file(filepath):
    """为单个文件添加Apache头部"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 如果已经有旧的头部，先删除
    if '# Copyright 2026 Stock Monitor Contributors' in content:
        # 找到头部结束位置（空行后的第一个非注释行）
        lines = content.split('\n')
        new_lines = []
        skip = False
        for i, line in enumerate(lines):
            if line.startswith('# Copyright 2026 Stock Monitor'):
                skip = True
                continue
            if skip:
                if line.strip() == '' or line.startswith('#'):
                    continue
                else:
                    skip = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines)
        print(f"🔄 更新头部: {filepath}")
    elif 'Apache License' in content:
        print(f"跳过 {filepath} (已有正确的Apache头部)")
        return
    else:
        print(f"✅ 添加头部: {filepath}")
    
    # 添加新头部
    new_content = APACHE_HEADER + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    """主函数"""
    # 需要添加头部的Python文件
    files = [
        'main.py',
        'api_client.py',
        'kline_chart.py',
        'intraday_chart.py'
    ]
    
    print("开始为源文件添加Apache 2.0头部...\n")
    
    for filename in files:
        if os.path.exists(filename):
            add_header_to_file(filename)
        else:
            print(f"⚠️  文件不存在: {filename}")
    
    print("\n✅ 完成！所有源文件已添加Apache 2.0头部")

if __name__ == '__main__':
    main()
