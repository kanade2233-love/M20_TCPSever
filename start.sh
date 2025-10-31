#!/bin/bash
# -*- coding: utf-8 -*-
"""
启动脚本 - TCP Socket服务器
"""

# 设置工作目录
cd /home/wheeltec/controltest

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 设置权限
chmod +x socket_server.py
chmod +x client_test.py

echo "TCP Socket服务器启动脚本"
echo "=========================="
echo "1. 启动服务器"
echo "2. 运行客户端测试"
echo "3. 查看服务器日志"
echo "4. 停止服务器"

read -p "请选择操作 (1-4): " choice

case $choice in
    1)
        echo "启动TCP Socket服务器..."
        echo "服务器将在后台运行，日志文件: server.log"
        echo "按Ctrl+C停止服务器"
        python3 socket_server.py
        ;;
    2)
        echo "运行客户端测试..."
        python3 client_test.py
        ;;
    3)
        echo "查看服务器日志..."
        if [ -f "server.log" ]; then
            tail -f server.log
        else
            echo "日志文件不存在"
        fi
        ;;
    4)
        echo "停止服务器..."
        pkill -f socket_server.py
        echo "服务器已停止"
        ;;
    *)
        echo "无效选择"
        ;;
esac




