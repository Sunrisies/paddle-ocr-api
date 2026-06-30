# PaddleOCR API

基于 **PaddleOCR** 的高性能 OCR（光学字符识别）Web API 服务，支持通过 HTTP 上传图片并返回识别到的文字及其位置信息。

## 技术栈

| 组件 | 说明 |
| **框架** | FastAPI + Uvicorn |
| **OCR 引擎** | PaddleOCR v3.7.0 |
| **深度学习框架** | PaddlePaddle-GPU 3.3.1（CUDA 12.9） |
| **模型** | PP-OCRv6_medium_det（文字检测） + PP-OCRv6_medium_rec（文字识别） |
| **Python** | ≥ 3.11, < 3.13 |
| **Python 版本管理** | uv（.python-version） |

## 快速开始


### 1. 环境要求

- Python 3.11 ~ 3.12
- GPU 加速可选（NVIDIA GPU + CUDA 12.9）

### 2. 安装依赖

**CPU 机器（Linux / Mac / Windows 无 GPU）：**
```bash
pip install -r requirements.txt
```
> `paddleocr` 会自动安装 CPU 版 `paddlepaddle`，开箱即用。

**GPU 机器（Windows / Linux 有 NVIDIA GPU）：**
```bash
pip install -r requirements-gpu.txt
```

> 代码会自动检测设备，无需额外配置。

### 3. 启动服务

```bash
python main.py
```

服务默认监听 `http://0.0.0.0:8100`

## Linux 部署（纯 CPU）

```bash
# 一键安装
bash deploy/install.sh

# 前台启动
bash deploy/start.sh

# systemd 服务（生产环境）
sudo cp deploy/paddle-ocr-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paddle-ocr-api
```

项目目录建议放在 `/opt/paddle-ocr-api`，systemd 服务文件中已预设此路径。

## API 文档

### 健康检查

```http
GET /health
```

**响应示例：**

```json
{
  "status": "ok"
}
```

### OCR 识别

```http
POST /ocr
```

**请求：** `multipart/form-data`，字段名 `file`，上传图片文件。

**响应格式：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否成功 |
| `message` | string | 提示信息 |
| `total_time_ms` | float | 识别耗时（毫秒） |
| `results` | array | 识别结果列表 |
| `results[].bbox` | [[float,float],...] | 文本包围盒四点坐标 `[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]` |
| `results[].text` | string | 识别出的文字 |
| `results[].confidence` | float | 置信度（0~1） |
| `raw_text` | string | 所有识别文字的拼接结果 |

**调用示例（curl）：**

```bash
curl -X POST http://localhost:8100/ocr \
  -F "file=@test.png"
```

**响应示例：**

```json
{
  "success": true,
  "message": "识别到 3 个文本区域",
  "total_time_ms": 152.34,
  "results": [
    {
      "bbox": [[10, 10], [100, 10], [100, 30], [10, 30]],
      "text": "Hello",
      "confidence": 0.98
    },
    {
      "bbox": [[10, 40], [80, 40], [80, 60], [10, 60]],
      "text": "World",
      "confidence": 0.95
    }
  ],
  "raw_text": "HelloWorld"
}
```

## 项目结构

```
paddle-ocr-api/
├── main.py                      # 入口脚本
├── paddle_ocr_api/              # 应用包
│   ├── __init__.py
│   └── app.py                   # FastAPI 应用（模型、路由）
├── requirements.txt             # Python 依赖
├── pyproject.toml               # 项目元信息与构建配置
├── .python-version      # Python 版本（uv）
├── .gitignore           # Git 忽略规则
├── tests/               # 测试
│   ├── generate_test_images.py   # 测试图片生成脚本
│   └── images/          # 生成的测试图片（中文、英文、混合等）
└── README.md            # 文档
```

## 模型说明

本服务使用 PaddleOCR 的 **PP-OCRv6_medium** 系列模型：

- **文字检测模型** (`PP-OCRv6_medium_det`)：定位图片中的文本区域
- **文字识别模型** (`PP-OCRv6_medium_rec`)：从检测区域中识别具体文字
- **文字行方向分类** (`use_textline_orientation=True`)：自动判断文字方向

首次启动时会自动下载模型文件。
