"""
tasks.py文件名是固定，该文件中定义异步任务函数！！
"""
from celery_tasks.main import app
from celery_tasks.yuntongxun.ccp_sms import CCP

#  定义一个发送短信的任务函数
# name自定义任务函数名称
# 被app.task装饰的函数就是异步任务函数
@app.task(name='ccp_send_sms_code')
def ccp_send_sms_code(mobile, sms_code):
    return CCP().send_template_sms(mobile, [sms_code, 5], 1)