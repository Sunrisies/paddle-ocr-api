#!/bin/bash
# PaddleOCR API — 前台启动脚本
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 进入项目目录
cd "$APP_DIR"

# 激活虚拟环境（如已安装）
if [ -d ".venv/bin" ]; then
    source .venv/bin/activate
fi

echo "============================================"
echo "  PaddleOCR API"
echo "  地址: http://0.0.0.0:8100"
echo "============================================"

# 启动
exec uvicorn paddle_ocr_api.app:app \
    --host 0.0.0.0 \
    --port 8100 \
    --log-level info
