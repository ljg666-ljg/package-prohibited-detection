from django.contrib import admin
from .models import DetectionRecord, DetectionBox


class DetectionBoxInline(admin.TabularInline):
    model = DetectionBox
    extra = 0
    readonly_fields = ('class_id', 'class_name', 'class_name_cn', 'confidence', 'xmin', 'ymin', 'xmax', 'ymax')
    fields = readonly_fields


@admin.register(DetectionRecord)
class DetectionRecordAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'user', 'source_type', 'total_objects', 'detection_time', 'status', 'created_at')
    list_filter = ('source_type', 'status', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [DetectionBoxInline]
    ordering = ('-created_at',)

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'


@admin.register(DetectionBox)
class DetectionBoxAdmin(admin.ModelAdmin):
    list_display = ('record_short', 'class_name_cn', 'confidence_pct', 'xmin', 'ymin', 'xmax', 'ymax')
    list_filter = ('class_name',)
    search_fields = ('class_name_cn', 'record__user__username')

    def record_short(self, obj):
        return str(obj.record.id)[:8]
    record_short.short_description = '记录ID'

    def confidence_pct(self, obj):
        return f'{obj.confidence*100:.1f}%'
    confidence_pct.short_description = '置信度'
