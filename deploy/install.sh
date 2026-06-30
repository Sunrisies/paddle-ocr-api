#!/bin/bash
# PaddleOCR API — Linux 一键部署脚本
# 用法: bash deploy/install.sh [--gpu]

set -e

APP_NAME="paddle-ocr-api"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="python3"

echo "============================================"
echo "  PaddleOCR API — Linux 部署"
echo "  目录: $APP_DIR"
echo "============================================"

# 1. 检查 Python
echo ""
echo "[1/4] 检查 Python..."
if ! command -v $PYTHON &>/dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.11~3.12"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "   CentOS/RHEL:   sudo yum install python3 python3-venv python3-pip"
    exit 1
fi

PY_VER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
echo "   Python 版本: $PY_VER"

# 2. 检查 CUDA (GPU 模式)
GPU_MODE=false
if [ "$1" = "--gpu" ]; then
    GPU_MODE=true
    echo ""
    echo "[2/4] 检查 NVIDIA GPU..."
    if ! command -v nvidia-smi &>/dev/null; then
        echo "❌ 未检测到 NVIDIA 驱动 (nvidia-smi 不可用)"
        echo "   请先安装 NVIDIA 驱动: https://www.nvidia.com/Download/index.aspx"
        exit 1
    fi
    echo "   ✅ GPU 可用"
else
    echo ""
    echo "[2/4] CPU 模式（无需 GPU）"
fi

# 3. 创建虚拟环境
echo ""
echo "[3/4] 创建虚拟环境..."
if [ ! -d "$APP_DIR/.venv" ]; then
    $PYTHON -m venv "$APP_DIR/.venv"
    echo "   虚拟环境已创建"
else
    echo "   虚拟环境已存在"
fi

source "$APP_DIR/.venv/bin/activate"

# 4. 安装依赖
echo ""
echo "[4/4] 安装 Python 依赖..."
pip install --upgrade pip -q

if [ "$GPU_MODE" = true ]; then
    echo "   安装 GPU 版 PaddlePaddle..."
    pip install paddlepaddle-gpu==3.3.1 \
        --index https://www.paddlepaddle.org.cn/packages/stable/cu129/
else
    echo "   安装 CPU 版 PaddlePaddle..."
    pip install paddlepaddle
fi

pip install -r "$APP_DIR/requirements.txt"

# 5. 完成
echo ""
echo "============================================"
echo "  ✅ 部署完成！"
echo "============================================"
echo ""
echo "启动服务："
echo "  方式一（前台）：  bash deploy/start.sh"
echo "  方式二（systemd）：sudo cp deploy/paddle-ocr-api.service /etc/systemd/system/"
echo "                      sudo systemctl daemon-reload"
echo "                      sudo systemctl enable --now paddle-ocr-api"
echo ""
echo "服务地址：http://0.0.0.0:8100"
echo "文档地址：http://localhost:8100/static/docs"
