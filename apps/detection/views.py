import os
import time
import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta

from .models import DetectionRecord, DetectionBox
from .yolo_engine import engine
from .utils import numpy_to_django_file

@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # 统计数据
    total_detections = DetectionRecord.objects.filter(user=user).count()
    today_detections = DetectionRecord.objects.filter(user=user, created_at__date=today).count()
    prohibited_count = DetectionBox.objects.filter(record__user=user).count()
    avg_time = DetectionRecord.objects.filter(
        user=user, detection_time__isnull=False
    ).aggregate(avg=Avg('detection_time'))['avg'] or 0

    # 最近7天趋势
    recent_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        cnt = DetectionRecord.objects.filter(user=user, created_at__date=d).count()
        recent_data.append({'date': d.strftime('%m/%d'), 'count': cnt})

    # 类别分布
    class_dist = list(
        DetectionBox.objects.filter(record__user=user)
        .values('class_name_cn')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    # 最近记录
    recent_records = DetectionRecord.objects.filter(user=user).order_by('-created_at')[:10]

    context = {
        'total_detections': total_detections,
        'today_detections': today_detections,
        'prohibited_count': prohibited_count,
        'avg_time': round(avg_time, 3),
        'recent_data': json.dumps(recent_data, ensure_ascii=False),
        'class_dist': json.dumps(list(class_dist), ensure_ascii=False),
        'recent_records': recent_records,
    }
    return render(request, 'detection/dashboard.html', context)

@login_required
def upload_image(request):
    """单张图片检测——传统表单提交方式"""
    result = None
    if request.method == 'POST' and request.FILES.get('image'):
        import cv2, numpy as np, base64
        image_file = request.FILES['image']
        conf = float(request.POST.get('conf', 0.25))
        iou = float(request.POST.get('iou', 0.7))

        # 创建记录
        record = DetectionRecord.objects.create(
            user=request.user, source_type='image', status='processing',
        )
        record.source_file.save(image_file.name, image_file)
        record.save()

        try:
            file_bytes = record.source_file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            res = engine.detect(img, conf=conf, iou=iou)

            # 保存结果图片
            result_img_name = f"result_{record.id.hex[:8]}.jpg"
            django_file = numpy_to_django_file(res['plot'], result_img_name)
            record.result_image.save(result_img_name, django_file)

            # Base64 for inline display
            _, img_encoded = cv2.imencode('.jpg', res['plot'], [cv2.IMWRITE_JPEG_QUALITY, 85])
            img_b64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')

            # 保存检测框
            boxes_to_create = []
            for i in range(len(res['boxes'])):
                boxes_to_create.append(DetectionBox(
                    record=record,
                    class_id=res['classes'][i],
                    class_name=res['class_names'][i],
                    class_name_cn=res['class_names_cn'][i],
                    confidence=res['confs'][i],
                    xmin=res['boxes'][i][0], ymin=res['boxes'][i][1],
                    xmax=res['boxes'][i][2], ymax=res['boxes'][i][3],
                ))
            DetectionBox.objects.bulk_create(boxes_to_create)

            record.status = 'completed'
            record.detection_time = res['total_time']
            record.total_objects = len(res['boxes'])
            record.save()

            result = {
                'record': record,
                'image_base64': f'data:image/jpeg;base64,{img_b64}',
                'boxes': zip(res['boxes'], res['class_names_cn'], res['confs'], res['class_names']),
                'total_time': res['total_time'],
                'device': str(engine.device),
                'total_objects': len(res['boxes']),
            }
        except Exception as e:
            record.status = 'failed'
            record.error_message = str(e)
            record.save()
            messages.error(request, f'检测失败: {e}')

    return render(request, 'detection/upload.html', {'result': result})

@login_required
def batch_upload(request):
    return render(request, "detection/batch.html")

@login_required
def video_upload(request):
    return render(request, "detection/video.html")

@login_required
def camera(request):
    return render(request, "detection/camera.html")

@login_required
def history(request):
    records = DetectionRecord.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "detection/history.html", {"records": records})

@login_required
def result_detail(request, record_id):
    record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)
    boxes = record.boxes.all().order_by("-confidence")
    return render(request, "detection/result.html", {"record": record, "boxes": boxes})

@login_required
@require_POST
def api_detect_image(request):
    """单张图片检测 API"""
    if 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': '请上传图片文件'}, status=400)

    image_file = request.FILES['image']
    conf = float(request.POST.get('conf', 0.25))
    iou = float(request.POST.get('iou', 0.7))

    record = DetectionRecord.objects.create(
        user=request.user, source_type='image', status='processing',
    )
    record.source_file.save(image_file.name, image_file)
    record.save()

    try:
        import cv2, numpy as np, base64
        file_bytes = record.source_file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result = engine.detect(img, conf=conf, iou=iou)

        result_img_name = f"result_{record.id.hex[:8]}.jpg"
        django_file = numpy_to_django_file(result['plot'], result_img_name)
        record.result_image.save(result_img_name, django_file)

        # 同时生成 base64 编码，避免隧道图片加载问题
        _, img_encoded = cv2.imencode('.jpg', result['plot'], [cv2.IMWRITE_JPEG_QUALITY, 90])
        img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')

        boxes_to_create = []
        for i in range(len(result['boxes'])):
            boxes_to_create.append(DetectionBox(
                record=record,
                class_id=result['classes'][i],
                class_name=result['class_names'][i],
                class_name_cn=result['class_names_cn'][i],
                confidence=result['confs'][i],
                xmin=result['boxes'][i][0],
                ymin=result['boxes'][i][1],
                xmax=result['boxes'][i][2],
                ymax=result['boxes'][i][3],
            ))
        DetectionBox.objects.bulk_create(boxes_to_create)

        record.status = 'completed'
        record.detection_time = result['total_time']
        record.total_objects = len(result['boxes'])
        record.save()

        return JsonResponse({
            'success': True,
            'record_id': str(record.id),
            'result_image_url': record.result_image.url,
            'result_image_base64': f'data:image/jpeg;base64,{img_base64}',
            'boxes': result['boxes'],
            'classes': result['classes'],
            'class_names': result['class_names'],
            'class_names_cn': result['class_names_cn'],
            'confs': result['confs'],
            'total_time': result['total_time'],
            'device': str(engine.device),
        })
    except Exception as e:
        record.status = 'failed'
        record.error_message = str(e)
        record.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def api_detect_batch(request):
    """批量图片检测 API"""
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'success': False, 'error': '请上传图片文件'}, status=400)

    conf = float(request.POST.get('conf', 0.25))
    iou = float(request.POST.get('iou', 0.7))

    results = []
    import cv2, numpy as np

    for image_file in files:
        record = DetectionRecord.objects.create(
            user=request.user, source_type='batch', status='processing',
        )
        record.source_file.save(image_file.name, image_file)
        record.save()

        try:
            file_bytes = record.source_file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            result = engine.detect(img, conf=conf, iou=iou)

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
                    xmin=result['boxes'][i][0],
                    ymin=result['boxes'][i][1],
                    xmax=result['boxes'][i][2],
                    ymax=result['boxes'][i][3],
                ))
            DetectionBox.objects.bulk_create(boxes_to_create)

            record.status = 'completed'
            record.detection_time = result['total_time']
            record.total_objects = len(result['boxes'])
            record.save()

            results.append({
                'record_id': str(record.id),
                'filename': image_file.name,
                'result_image_url': record.result_image.url,
                'boxes': result['boxes'],
                'class_names_cn': result['class_names_cn'],
                'confs': result['confs'],
                'total_time': result['total_time'],
                'total_objects': len(result['boxes']),
            })
        except Exception as e:
            record.status = 'failed'
            record.error_message = str(e)
            record.save()
            results.append({
                'filename': image_file.name,
                'error': str(e),
            })

    return JsonResponse({
        'success': True,
        'results': results,
        'device': str(engine.device),
    })

@login_required
@require_POST
def api_detect_video(request):
    """视频检测 API — 同步版本"""
    if 'video' not in request.FILES:
        return JsonResponse({'success': False, 'error': '请上传视频文件'}, status=400)

    video_file = request.FILES['video']
    conf = float(request.POST.get('conf', 0.25))
    iou = float(request.POST.get('iou', 0.7))

    record = DetectionRecord.objects.create(
        user=request.user, source_type='video', status='processing',
    )
    record.source_file.save(video_file.name, video_file)
    record.save()

    try:
        import cv2, numpy as np, tempfile, shutil

        # 保存临时文件
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, video_file.name)
        with open(tmp_path, 'wb') as f:
            for chunk in video_file.chunks():
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
            result = engine.detect(frame, conf=conf, iou=iou)
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

        cap.release()
        out.release()
        shutil.rmtree(tmp_dir, ignore_errors=True)

        # 保存结果视频
        rel_path = f'results/{out_name}'
        record.result_video.name = rel_path
        record.total_objects = len(all_boxes)
        record.detection_time = round(frame_count / fps, 1) if fps else 0
        record.status = 'completed'
        record.save()

        # 只保存每帧第一个框作为样本
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

        return JsonResponse({
            'success': True,
            'record_id': str(record.id),
            'result_video_url': record.result_video.url,
            'total_frames': frame_count,
            'total_objects': len(all_boxes),
            'fps': round(fps, 1),
        })
    except Exception as e:
        record.status = 'failed'
        record.error_message = str(e)
        record.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_delete_record(request, record_id):
    """删除检测记录"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)
    record.delete()
    return JsonResponse({'success': True})
