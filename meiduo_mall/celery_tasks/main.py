"""
该文件作为异步应用程序初始化的模块
"""

# 在异步任务程序中加载django的环境
import os
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'meiduo_mall.settings.dev'
)


from celery import Celery

# 初始化一个应用程序对象
app = Celery("meiduo")

# 加载配置文件——参数是配置文件(模块)的导包路径
# 我们将来是在celery_tasks包所在的目录为工作目录运行异步程序；
app.config_from_object('celery_tasks.config')

# 告知app监听的任务有哪些
# 该函数的参数是一个列表，列表里写的是任务包的导包路径
app.autodiscover_tasks([
    'celery_tasks.sms',
    'celery_tasks.email'
])