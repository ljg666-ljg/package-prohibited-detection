"""
Celery 异步任务 — 用于视频检测和批量处理
需要 Redis 作为 broker: celery -A config worker -l info -P solo
"""
import os
import tempfile
import shutil
import cv2
import numpy as np
from celery import shared_task
from django.conf import settings


@shared_task(bind=True)
def process_video_task(self, record_id):
    """异步处理视频检测"""
    from .models import DetectionRecord, DetectionBox
    from .yolo_engine import engine

    try:
        record = DetectionRecord.objects.get(id=record_id)
        record.status = 'processing'
        record.save()

        # 读取上传的视频文件
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, os.path.basename(record.source_file.name))
        with open(tmp_path, 'wb') as f:
            for chunk in record.source_file.chunks():
                f.write(chunk)

        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out_name = f"video_result_{record.id.hex[:8]}.avi"
        out_path = os.path.join(settings.MEDIA_ROOT, 'results', out_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

        all_boxes = []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            result = engine.detect(frame)
            out.write(result['plot'])

            for i in range(len(result['boxes'])):
                all_boxes.append({
                    'frame': frame_count,
                    'class_id': result['classes'][i],
                    'class_name': result['class_names'][i],
                    'class_name_cn': result['class_names_cn'][i],
                    'confidence': result['confs'][i],
                    'xmin': result['boxes'][i][0],
                    'ymin': result['boxes'][i][1],
                    'xmax': result['boxes'][i][2],
                    'ymax': result['boxes'][i][3],
                })

            # 更新进度 (Celery task state)
            if frame_count % 50 == 0 and total_frames > 0:
                self.update_state(
                    state='PROGRESS',
                    meta={'current': frame_count, 'total': total_frames}
                )

        cap.release()
        out.release()
        shutil.rmtree(tmp_dir, ignore_errors=True)

        record.result_video.name = f'results/{out_name}'
        record.total_objects = len(all_boxes)
        record.detection_time = round(frame_count / fps, 1) if fps else 0
        record.status = 'completed'
        record.save()

        # 保存检测框样本
        boxes_to_create = []
        seen_frames = set()
        for b in all_boxes:
            if b['frame'] not in seen_frames and len(boxes_to_create) < 200:
                seen_frames.add(b['frame'])
                boxes_to_create.append(DetectionBox(
                    record=record,
                    class_id=b['class_id'],
                    class_name=b['class_name'],
                    class_name_cn=b['class_name_cn'],
                    confidence=b['confidence'],
                    xmin=b['xmin'], ymin=b['ymin'],
                    xmax=b['xmax'], ymax=b['ymax'],
                ))
        DetectionBox.objects.bulk_create(boxes_to_create)

        return {
            'status': 'completed',
            'total_frames': frame_count,
            'total_objects': len(all_boxes),
            'result_video': record.result_video.url,
        }

    except Exception as exc:
        try:
            record = DetectionRecord.objects.get(id=record_id)
            record.status = 'failed'
            record.error_message = str(exc)
            record.save()
        except Exception:
            pass
        raise self.retry(exc=exc, max_retries=1)


@shared_task
def process_batch_images_task(record_ids):
    """异步批量处理图片检测"""
    from .models import DetectionRecord, DetectionBox
    from .yolo_engine import engine
    from .utils import numpy_to_django_file
    import cv2, numpy as np

    results = []
    for record_id in record_ids:
        try:
            record = DetectionRecord.objects.get(id=record_id)
            record.status = 'processing'
            record.save()

            file_bytes = record.source_file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            result = engine.detect(img)

            result_img_name = f"result_{record.id.hex[:8]}.jpg"
            django_file = numpy_to_django_file(result['plot'], result_img_name)
            record.result_image.save(result_img_name, django_file)

            boxes_to_create = []
            for i in range(len(result['boxes'])):
                boxes_to_create.append(DetectionBox(
                    record=record,
                    class_id=result['classes'][i],
                    class_name=result['class_names'][i],
                    class_name_cn=result['class_names_cn'][i],
                    confidence=result['confs'][i],
                    xmin=result['boxes'][i][0], ymin=result['boxes'][i][1],
                    xmax=result['boxes'][i][2], ymax=result['boxes'][i][3],
                ))
            DetectionBox.objects.bulk_create(boxes_to_create)

            record.status = 'completed'
            record.detection_time = result['total_time']
            record.total_objects = len(result['boxes'])
            record.save()
            results.append({'record_id': str(record.id), 'success': True})
        except Exception as e:
            record.status = 'failed'
            record.error_message = str(e)
            record.save()
            results.append({'record_id': str(record.id), 'success': False, 'error': str(e)})

    return results
