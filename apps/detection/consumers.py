"""
Django Channels WebSocket Consumer — 摄像头实时检测
当 Daphne 服务运行时使用，替代 HTTP 轮询
"""
import json
import base64
import numpy as np
import cv2
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class CameraConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'camera_detection'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print('[CameraConsumer] 客户端已连接')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f'[CameraConsumer] 客户端断开: {close_code}')

    async def receive(self, text_data):
        """接收前端发送的 base64 图片帧"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'frame':
                frame_b64 = data.get('frame', '')
                # 解码 base64 为 numpy array
                img_bytes = base64.b64decode(frame_b64.split(',')[1] if ',' in frame_b64 else frame_b64)
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # 同步推理
                result = await sync_to_async(self.detect)(img)

                # 发送结果回客户端
                await self.send(text_data=json.dumps({
                    'type': 'detection',
                    'boxes': result['boxes'],
                    'classes': result['classes'],
                    'class_names_cn': result['class_names_cn'],
                    'confs': result['confs'],
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e),
            }))

    def detect(self, img):
        """同步执行 YOLO 推理"""
        from .yolo_engine import engine
        return engine.detect(img, conf=0.25, iou=0.7)
