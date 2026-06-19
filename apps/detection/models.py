import uuid
from django.db import models
from django.conf import settings


class DetectionRecord(models.Model):
    """检测记录"""
    SOURCE_TYPES = [
        ("image", "单张图片"),
        ("batch", "批量图片"),
        ("video", "视频"),
        ("camera", "摄像头"),
    ]
    STATUS_CHOICES = [
        ("pending", "等待处理"),
        ("processing", "处理中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="detections", verbose_name="用户"
    )
    source_type = models.CharField(
        max_length=10, choices=SOURCE_TYPES, default="image", verbose_name="来源类型"
    )
    source_file = models.FileField(
        upload_to="uploads/%Y/%m/%d/", null=True, blank=True, verbose_name="原始文件"
    )
    result_image = models.ImageField(
        upload_to="results/%Y/%m/%d/", null=True, blank=True, verbose_name="结果图片"
    )
    result_video = models.FileField(
        upload_to="results/%Y/%m/%d/", null=True, blank=True, verbose_name="结果视频"
    )
    detection_time = models.FloatField(
        null=True, blank=True, verbose_name="推理耗时(秒)"
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="pending", verbose_name="状态"
    )
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    total_objects = models.IntegerField(default=0, verbose_name="检出目标总数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "检测记录"
        verbose_name_plural = "检测记录"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["source_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DetectionBox(models.Model):
    """检测框 — 每个检测到的目标"""
    record = models.ForeignKey(
        DetectionRecord, on_delete=models.CASCADE,
        related_name="boxes", verbose_name="所属记录"
    )
    class_id = models.IntegerField(verbose_name="类别ID")
    class_name = models.CharField(max_length=50, verbose_name="类别名")
    class_name_cn = models.CharField(max_length=50, default="", verbose_name="中文名")
    confidence = models.FloatField(verbose_name="置信度")
    xmin = models.IntegerField(verbose_name="X最小值")
    ymin = models.IntegerField(verbose_name="Y最小值")
    xmax = models.IntegerField(verbose_name="X最大值")
    ymax = models.IntegerField(verbose_name="Y最大值")

    class Meta:
        verbose_name = "检测框"
        verbose_name_plural = "检测框"
        ordering = ["-confidence"]

    def __str__(self):
        return f"{self.class_name_cn} ({self.confidence:.1%})"
