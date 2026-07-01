import time
import base64
from typing import List
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image, ImageDraw
import pypdfium2 as pdfium
import io

app = FastAPI(title="PaddleOCR API", description="OCR识别服务", version="1.0")

# 静态文件目录
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/assets/{path:path}")
async def assets(path: str):
    return FileResponse(static_dir / "assets" / path)


@app.get("/")
async def index():
    return FileResponse(static_dir / "index.html")

# GPU 版 OCR 模型
ocr = PaddleOCR(
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


class PDFPageResult(BaseModel):
    page: int
    total_pages: int
    results: List[OCRResultItem]
    raw_text: str
    total_time_ms: float
    image_base64: str  # 带标注框的页面图片 base64


class PDFResponse(BaseModel):
    success: bool
    message: str = ""
    total_pages: int
    total_time_ms: float
    pages: List[PDFPageResult]
    full_text: str


@app.post("/ocr/pdf", response_model=PDFResponse)
async def ocr_pdf(file: UploadFile = File(...)):
    """PDF 批量 OCR — 逐页识别"""
    try:
        contents = await file.read()
        pdf = pdfium.PdfDocument(contents)
        total_pages = len(pdf)
        if total_pages == 0:
            raise HTTPException(status_code=400, detail="PDF 无页面")

        overall_start = time.time()
        page_results = []
        all_text = []

        for page_idx in range(total_pages):
            page = pdf[page_idx]
            # 渲染页面为图片（200 DPI）
            bitmap = page.render(scale=200 / 72)
            img_pil = bitmap.to_pil()

            # OCR 识别
            img_np = np.array(img_pil.convert("RGB"))
            page_start = time.time()
            result = ocr.predict(img_np)
            elapsed = (time.time() - page_start) * 1000

            # 解析结果
            ocr_items = []
            texts = []
            draw = ImageDraw.Draw(img_pil, "RGBA")

            for res_dict in result:
                bboxes = res_dict.get('dt_polys', [])
                rec_texts = res_dict.get('rec_texts', [])
                rec_scores = res_dict.get('rec_scores', [])

                for bbox, text, conf in zip(bboxes, rec_texts, rec_scores):
                    if hasattr(bbox, 'tolist'):
                        bbox = bbox.tolist()
                    ocr_items.append(OCRResultItem(bbox=bbox, text=text, confidence=conf))
                    texts.append(text)

                    # 画框
                    pts = [(int(p[0]), int(p[1])) for p in bbox]
                    if conf >= 0.9:
                        color = (34, 197, 94, 180)
                    elif conf >= 0.7:
                        color = (59, 130, 246, 180)
                    elif conf >= 0.5:
                        color = (245, 158, 11, 200)
                    else:
                        color = (239, 68, 68, 200)
                    draw.polygon(pts, fill=color[:3] + (30,), outline=color)

            # 图片转 base64
            buf = io.BytesIO()
            img_pil.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

            page_text = "".join(texts)
            page_results.append(PDFPageResult(
                page=page_idx + 1,
                total_pages=total_pages,
                results=ocr_items,
                raw_text=page_text,
                total_time_ms=elapsed,
                image_base64=b64,
            ))
            all_text.append(page_text)

        overall_elapsed = (time.time() - overall_start) * 1000
        return PDFResponse(
            success=True,
            message=f"识别完成，共 {total_pages} 页",
            total_pages=total_pages,
            total_time_ms=overall_elapsed,
            pages=page_results,
            full_text="\n".join(all_text),
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF处理失败: {str(e)}")


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
