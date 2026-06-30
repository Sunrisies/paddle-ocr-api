"""生成 OCR 测试图片"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_text(size, texts, filename, bg_color="white"):
    """在纯色背景上绘制文字"""
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # 尝试加载中文字体，fallback 到默认
    try:
        font_cn = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 32)   # 微软雅黑
        font_en = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
    except (IOError, OSError):
        font_cn = font_en = ImageFont.load_default()

    y = 40
    for text, font in texts:
        draw.text((40, y), text, fill="black", font=font)
        bbox = draw.textbbox((40, y), text, font=font)
        y = bbox[3] + 30

    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"  OK {filename}  ({size[0]}x{size[1]})")


def main():
    print("生成测试图片...\n")

    # 1. 中文文本
    draw_text(
        (600, 200),
        [("你好，世界！", None), ("PaddleOCR 识别测试", None)],
        "chinese.png",
    )

    # 2. 英文文本
    draw_text(
        (600, 200),
        [("Hello, World!", None), ("PaddleOCR Test", None)],
        "english.png",
    )

    # 3. 混合中英文 + 数字
    draw_text(
        (700, 300),
        [("订单号：NO.20240630", None), ("金额：¥128.50", None), ("状态：已发货", None)],
        "mixed.png",
    )

    # 4. 多行段落
    draw_text(
        (700, 400),
        [
            ("OCR（光学字符识别）技术", None),
            ("可以将图片中的文字信息", None),
            ("提取为可编辑的文本数据。", None),
            ("广泛应用于文档数字化、", None),
            ("票据识别、车牌识别等领域。", None),
        ],
        "paragraph.png",
    )

    # 5. 大号标题文本（用于清晰识别）
    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 48)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
    draw_text(
        (600, 150),
        [("OCR 测试图片", font_large)],
        "title.png",
    )

    print(f"\n全部生成完毕！共 5 张测试图片，保存在 {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
