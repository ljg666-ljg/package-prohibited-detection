from django.urls import path
from . import views

app_name = "detection"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_image, name="upload"),
    path("batch/", views.batch_upload, name="batch_upload"),
    path("video/", views.video_upload, name="video_upload"),
    path("camera/", views.camera, name="camera"),
    path("history/", views.history, name="history"),
    path("result/<uuid:record_id>/", views.result_detail, name="result_detail"),
    # API
    path("api/detect/image/", views.api_detect_image, name="api_detect_image"),
    path("api/detect/batch/", views.api_detect_batch, name="api_detect_batch"),
    path("api/detect/video/", views.api_detect_video, name="api_detect_video"),
    path("api/record/<uuid:record_id>/delete/", views.api_delete_record, name="api_delete_record"),
]
