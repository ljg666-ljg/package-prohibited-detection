# Gunicorn 配置文件
# 用法: gunicorn config.wsgi:application -c config/gunicorn.conf.py

import multiprocessing

# 监听地址和端口
bind = "127.0.0.1:8000"

# 工作进程数（CPU 核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 每个 worker 的线程数
threads = 2

# 超时时间（视频处理可能较长）
timeout = 300

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程名称
proc_name = "ppd_detection"

# 重启（worker 处理一定请求后重启，防止内存泄漏）
max_requests = 1000
max_requests_jitter = 100

# 优雅重启
graceful_timeout = 30
