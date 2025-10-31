#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本
"""

import subprocess
import time
import sys
import os

def test_server():
    """测试服务器功能"""
    print("开始测试TCP Socket服务器...")
    
    # 检查文件是否存在
    files = ['socket_server.py', 'client_test.py', 'config.py']
    for file in files:
        if not os.path.exists(file):
            print(f"错误: 文件 {file} 不存在")
            return False
    
    print("✓ 所有必需文件存在")
    
    # 检查Python语法
    try:
        subprocess.run([sys.executable, '-m', 'py_compile', 'socket_server.py'], 
                      check=True, capture_output=True)
        subprocess.run([sys.executable, '-m', 'py_compile', 'client_test.py'], 
                      check=True, capture_output=True)
        subprocess.run([sys.executable, '-m', 'py_compile', 'config.py'], 
                      check=True, capture_output=True)
        print("✓ Python语法检查通过")
    except subprocess.CalledProcessError as e:
        print(f"✗ Python语法错误: {e}")
        return False
    
    print("\n测试完成！")
    print("\n使用方法:")
    print("1. 启动服务器: python3 socket_server.py")
    print("2. 运行客户端测试: python3 client_test.py")
    print("3. 查看日志: tail -f server.log")
    
    return True

if __name__ == "__main__":
    test_server()




