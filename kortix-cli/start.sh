#!/bin/bash
# Kortix CLI Linux/Mac 启动脚本

set -e

echo "========================================"
echo "  Kortix AI Agent CLI"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安装"
    echo "请安装 Python 3.8+"
    exit 1
fi

# 检查依赖
echo "[INFO] 检查依赖..."
if ! python3 -c "import dashscope" &> /dev/null; then
    echo "[INFO] 依赖未安装，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "[WARNING] .env 文件不存在"
    echo "[INFO] 正在创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "========================================"
    echo "  重要提示"
    echo "========================================"
    echo "请编辑 .env 文件，填入你的阿里云百炼 API Key"
    echo "API Key 获取地址: https://dashscope.console.aliyun.com/"
    echo ""
    echo "按 Enter 键继续..."
    read
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[WARNING] Docker 未安装"
    echo "代码执行功能将不可用"
    echo ""
fi

# 启动程序
echo "[INFO] 启动 Kortix AI Agent..."
echo ""
python3 run.py "$@"
