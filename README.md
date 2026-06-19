# 包裹违禁物品检测识别系统

基于 YOLOv8 + CBAM 注意力机制的包裹违禁物品智能检测 Web 平台。

## 功能

- **单张图片检测**：上传包裹 X 光/可见光图片，实时返回检测结果
- **批量图片检测**：多文件上传，批量推理
- **视频检测**：上传视频文件，逐帧检测并生成标注结果视频
- **摄像头实时检测**：浏览器摄像头 + WebSocket 实时推流推理
- **用户系统**：注册/登录，检测记录按用户隔离
- **检测历史**：查询、详情回溯

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Django 4.2 + DRF + Celery + Channels |
| 深度学习 | YOLOv8 + CBAM + PyTorch |
| 前端 | Bootstrap 5 + Chart.js + Canvas API |
| 部署 | Nginx + Gunicorn + Systemd |

## 检测类别（10 类违禁品）

打火机 / 压力罐 / 刀具 / 剪刀 / 充电宝 / ZIPPO油 / 手铐 / 弹弓 / 鞭炮 / 指甲油

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 迁移数据库
python manage.py migrate

# 3. 创建管理员
python manage.py createsuperuser

# 4. 启动开发服务器
python manage.py runserver

# 5. 访问 http://127.0.0.1:8000
```

## 部署

生产部署配置文件见 `deploy/` 目录，包含 Nginx、Gunicorn、Systemd 配置模板。

```bash
# 设置环境变量
export DJANGO_SECRET_KEY=你的密钥

# 收集静态文件
python manage.py collectstatic

# 启动 Gunicorn
gunicorn config.wsgi:application -c config/gunicorn.conf.py
```

## 项目结构

```
├── config/              # Django 配置
├── apps/
│   ├── accounts/        # 用户系统
│   └── detection/       # 检测核心
├── templates/           # 前端模板
├── static/              # 静态资源
├── deploy/              # 部署配置
├── models/              # YOLO 模型文件
└── requirements.txt
```
