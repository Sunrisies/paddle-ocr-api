"""
PyInstaller 构建脚本 — 打包 PaddleOCR API 为单个二进制
"""
import os
import sys
import shutil
from pathlib import Path

# 清理之前的构建
for d in ["build", "dist"]:
    shutil.rmtree(d, ignore_errors=True)
for f in Path(".").glob("*.spec"):
    f.unlink()

# 获取 .venv 的 site-packages
venv = Path(sys.executable).parent.parent
site = list(venv.rglob("site-packages"))[0]

# 模型缓存目录（PaddleX 官方模型）
model_cache = Path.home() / ".paddlex" / "official_models"
if not model_cache.exists():
    print("⚠ 模型缓存未下载，首次运行时会自动下载")
    print(f"   缓存路径: {model_cache}")

cmd = [
    "pyinstaller",
    "--onefile",                     # 单个 exe
    "--name", "paddle-ocr-api",
    
    # 不打开控制台窗口（纯服务，后台运行）
    "--noconsole",
    
    # 隐藏导入 — PaddlePaddle / PaddleOCR
    "--hidden-import", "paddle",
    "--hidden-import", "paddle.base",
    "--hidden-import", "paddle.base.core",
    "--hidden-import", "paddle.base.framework",
    "--hidden-import", "paddle.base.libpaddle",
    "--hidden-import", "paddle.jit",
    "--hidden-import", "paddle.static",
    "--hidden-import", "paddle.nn",
    "--hidden-import", "paddle.tensor",
    "--hidden-import", "paddle.vision",
    "--hidden-import", "paddleocr",
    "--hidden-import", "paddleocr.ppocr",
    "--hidden-import", "paddlex",
    
    # 隐藏导入 — FastAPI / Uvicorn
    "--hidden-import", "uvicorn",
    "--hidden-import", "uvicorn.loggers",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "starlette",
    "--hidden-import", "starlette.routing",
    "--hidden-import", "multipart",
    
    # 递归收集 paddle / paddleocr 的所有数据文件
    "--collect-data", "paddle",
    "--collect-data", "paddleocr",
    "--collect-data", "paddlex",
    "--collect-data", "ppocr",
    
    # 递归收集它们的二进制库
    "--collect-binaries", "paddle",
    "--collect-binaries", "paddleocr",
    
    # 入口
    "main.py",
]

print("开始构建...")
print("=" * 50)
os.system(" ".join(cmd))
print("=" * 50)

# 检查构建结果
dist = Path("dist") / "paddle-ocr-api.exe"
if dist.exists():
    size = dist.stat().st_size / (1024**3)
    print(f"\n✅ 构建成功！")
    print(f"   路径: {dist.absolute()}")
    print(f"   大小: {size:.2f} GB")
else:
    print("\n❌ 构建失败，检查上面的错误信息")
