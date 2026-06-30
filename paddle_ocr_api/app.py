import time
from typing import List
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


from paddleocr import PaddleOCR
import paddle
import numpy as np
from PIL import Image, ImageDraw
import io

app = FastAPI(title="PaddleOCR API", description="OCR识别服务", version="1.0")

# 静态文件目录
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    return FileResponse(static_dir / "index.html")

# 自动检测设备
_device = "gpu" if paddle.is_compiled_with_cuda() else "cpu"
print(f"[PaddleOCR] 设备: {_device}")

# 全局初始化 OCR 模型
ocr = PaddleOCR(
    device=_device,
    text_detection_model_name="PP-OCRv6_medium_det",
    text_recognition_model_name="PP-OCRv6_medium_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
)


class OCRResultItem(BaseModel):
    bbox: List[List[float]]   # 四点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text: str
    confidence: float


class OCRResponse(BaseModel):
    success: bool
    message: str = ""
    total_time_ms: float
    results: List[OCRResultItem]
    raw_text: str


@app.post("/ocr", response_model=OCRResponse)
async def ocr_recognize(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(img)

        start = time.time()
        result = ocr.predict(img_np)   # result 是 List[Dict]
        elapsed_ms = (time.time() - start) * 1000

        ocr_items = []
        text_parts = []

        # 正确解析新版 PaddleOCR 返回的字典结构
        for res_dict in result:
            bboxes = res_dict.get('dt_polys', [])
            texts = res_dict.get('rec_texts', [])
            scores = res_dict.get('rec_scores', [])

            for bbox, text, conf in zip(bboxes, texts, scores):
                if hasattr(bbox, 'tolist'):
                    bbox = bbox.tolist()
                ocr_items.append(OCRResultItem(bbox=bbox, text=text, confidence=conf))
                text_parts.append(text)

        return OCRResponse(
            success=True,
            message=f"识别到 {len(ocr_items)} 个文本区域",
            total_time_ms=elapsed_ms,
            results=ocr_items,
            raw_text="".join(text_parts)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/ocr/visual")
async def ocr_visual(file: UploadFile = File(...)):
    """OCR 识别并返回带标注框的图片"""
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(img)

        result = ocr.predict(img_np)
        draw = ImageDraw.Draw(img, "RGBA")

        for res_dict in result:
            bboxes = res_dict.get('dt_polys', [])
            texts = res_dict.get('rec_texts', [])
            scores = res_dict.get('rec_scores', [])

            for bbox, text, conf in zip(bboxes, texts, scores):
                if conf is None:
                    continue
                # bbox 是 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                pts = [(int(p[0]), int(p[1])) for p in bbox]

                # 根据置信度选颜色
                if conf >= 0.9:
                    color = (34, 197, 94, 180)      # 绿
                elif conf >= 0.7:
                    color = (59, 130, 246, 180)     # 蓝
                elif conf >= 0.5:
                    color = (245, 158, 11, 200)     # 橙
                else:
                    color = (239, 68, 68, 200)      # 红

                draw.polygon(pts, fill=color[:3] + (30,), outline=color)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")
