"""
检测辅助工具函数 — 适配自原项目 detect_tools.py
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile
from .config import font_path, CH_names


class Colors:
    """用于绘制不同颜色的边界框 — 移植自 detect_tools.Colors"""
    def __init__(self):
        hexs = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17',
                '3DDB86', '1A9334', '00D4BB', '2C99A8', '00C2FF', '344593', '6473FF',
                '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
        self.palette = [self.hex2rgb(f'#{c}') for c in hexs]
        self.n = len(self.palette)

    def __call__(self, i, bgr=False):
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))


def draw_rect_box(image, rect, add_text, font_c, color):
    """绘制单个矩形框与中文文本 — 移植自 detect_tools.drawRectBox"""
    cv2.rectangle(image, (int(rect[0]), int(rect[1])),
                  (int(rect[2]), int(rect[3])), color, 2)
    cv2.rectangle(image, (int(rect[0]) - 1, int(rect[1]) - 25),
                  (int(rect[0]) + 80, int(rect[1])), color, -1, cv2.LINE_AA)

    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    draw.text((int(rect[0]) + 2, int(rect[1]) - 27), add_text,
              (255, 255, 255), font=font_c)
    return np.array(img_pil)


def load_chinese_font(size=25):
    """加载中文字体"""
    try:
        return ImageFont.truetype(str(font_path), size, 0)
    except Exception:
        return ImageFont.load_default()


def numpy_to_django_file(img_array, filename, format='JPEG'):
    """将 numpy array 转为 Django ContentFile (用于保存到 FileField)"""
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buffer = BytesIO()
    pil_img.save(buffer, format=format, quality=95)
    return ContentFile(buffer.getvalue(), name=filename)


def cv2_read_chinese_path(path):
    """读取含中文路径的图片 — 移植自 detect_tools.img_cvread"""
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
