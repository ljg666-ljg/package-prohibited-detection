"""
YOLOv8 推理引擎 - 单例模式
复用了原项目的 Config.py 和 detect_tools.py 中的配置和辅助函数
"""
import time
import numpy as np
import cv2
import torch
from ultralytics import YOLO
from .config import model_path, names, CH_names


class YOLOEngine:
    """YOLO 推理引擎单例 — 应用启动时加载一次模型"""
    _instance = None
    _model = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self):
        """加载模型（延迟加载，避免导入时阻塞）"""
        if self._model is not None:
            return
        self._device = 0 if torch.cuda.is_available() else 'cpu'
        self._model = YOLO(str(model_path), task='detect')
        # 预热模型
        self._model(np.zeros((48, 48, 3)), device=self._device)
        print(f"[YOLOEngine] 模型加载完成, 设备: {self._device}")

    def detect(self, image, conf=0.25, iou=0.7):
        """
        执行目标检测
        :param image: numpy array (H, W, 3) BGR 或 RGB, 或文件路径字符串
        :param conf: 置信度阈值
        :param iou: IoU 阈值
        :return: dict {
            'boxes': [[x1,y1,x2,y2], ...],
            'classes': [class_id, ...],
            'confs': [confidence, ...],
            'class_names': ['knife', ...],
            'class_names_cn': ['刀具', ...],
            'plot': numpy array (BGR) 画好框的图片,
            'speed': {'preprocess': ..., 'inference': ..., 'postprocess': ...},
            'total_time': float (秒)
        }
        """
        if self._model is None:
            self.load_model()

        t1 = time.time()
        results = self._model(image, conf=conf, iou=iou, device=self._device, verbose=False)[0]
        t2 = time.time()

        boxes_result = results.boxes
        if boxes_result is not None and len(boxes_result) > 0:
            boxes_xyxy = boxes_result.xyxy.tolist()
            boxes_xyxy = [list(map(int, b)) for b in boxes_xyxy]
            classes = [int(c) for c in boxes_result.cls.tolist()]
            confs = [float(c) for c in boxes_result.conf.tolist()]
            class_names = [names.get(c, 'unknown') for c in classes]
            class_names_cn = [CH_names[c] if c < len(CH_names) else '未知' for c in classes]
        else:
            boxes_xyxy = []
            classes = []
            confs = []
            class_names = []
            class_names_cn = []

        # 画框后的图片
        plot_img = results.plot()

        # 推理速度
        speed = results.speed if hasattr(results, 'speed') else {}

        return {
            'boxes': boxes_xyxy,
            'classes': classes,
            'confs': confs,
            'class_names': class_names,
            'class_names_cn': class_names_cn,
            'plot': plot_img,
            'speed': speed,
            'total_time': round(t2 - t1, 3),
        }

    @property
    def device(self):
        return self._device


# 全局单例
engine = YOLOEngine()
