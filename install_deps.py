#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安装脚本
"""

import subprocess
import sys
import os

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package} 安装失败")
        return False

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        print(f"✓ {package} 已安装")
        return True
    except ImportError:
        print(f"✗ {package} 未安装")
        return False

def main():
    """主函数"""
    print("检查并安装依赖包...")
    
    # 需要安装的包
    packages = [
        'pyserial',  # 串口通信
    ]
    
    # 检查并安装
    for package in packages:
        if not check_package('serial'):
            install_package('pyserial')
    
    print("\n依赖检查完成！")
    print("\n使用方法:")
    print("1. 启动服务器: python3 socket_server.py")
    print("2. 运行客户端测试: python3 client_test.py")
    print("3. 查看日志: tail -f server.log")

if __name__ == "__main__":
    main()




