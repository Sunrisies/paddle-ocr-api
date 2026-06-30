import time
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import io

app = FastAPI(title="PaddleOCR API", description="OCR识别服务", version="1.0")

# 全局初始化 OCR 模型（新版用 device 参数）
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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
