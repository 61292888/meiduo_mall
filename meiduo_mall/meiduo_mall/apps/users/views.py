from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator

from django.views import View
from django.http import JsonResponse
from meiduo_mall.utils.view import LoginRequiredMixin
from users.models import User
from .models import User
from django_redis import get_redis_connection
from django.contrib.auth import login, authenticate
import json
import re
import logging
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.email.tasks import send_verify_email


logger = logging.getLogger('django')

# 验证用户名重复
class UsernameCountView(View):

    def get(self, request, username):

        try:
            # 1、统计用户数量
            count = User.objects.filter(
                username=username
            ).count()

        except Exception as e:
            print(e)
            # 写日志
            logger.error(e)

        finally:
        # 2、构建响应返回
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'count': count,
            })



class MobileCountView(View):

    def get(self, request, mobile):

        try:
            # 1、根据手机号统计数量
            count = User.objects.filter(
                mobile=mobile
            )   .count()
        except Exception as e:
            print(e)
            # 写日志
            logger.error(e)

        # 2、构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })

# 用户注册
class RegisterView(View):

    def post(self, request):
        # 1、提取参数
        # request.body --> b'{"username": "xxxx"}'
        # request.body.decode() --> '{"username": "xxxx"}'
        data = json.loads(request.body.decode())

        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        sms_code = data.get('sms_code')
        allow = data.get('allow')

        # 2、校验参数
        if not all([username, password, password2, mobile, sms_code]):
            return JsonResponse({'code': 400, 'errmsg': '缺少参数'}, status=400)

        if not re.match(r'^\w{5,20}$', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名格式有误'}, status=400)

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': '密码格式有误'}, status=400)

        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '密码输入不一致！'}, status=400)

        if not re.match(r'^\d{6}$', sms_code):
            return JsonResponse({'code': 400, 'errmsg': '验证码格式有误'}, status=400)

        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '请求统一用户协议！'}, status=400)

        # 手机验证码校验
        conn = get_redis_connection('sms_code')
        sms_code_from_redis = conn.get('sms_%s' % mobile)
        if not sms_code_from_redis:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码过期！'}, status=400)
        sms_code_from_redis = sms_code_from_redis.decode()
        if sms_code_from_redis != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码有误！'}, status=400)

        # 3、新建数据,构建用户模型类对象保存数据库
        # User.objects.create() --> 构建的用户模型类对象，密码不会加密
        # User.objects.create_user() --> 构建用户模型类对象，把明文密码加密
        # User.objects.create_superuser() --> 构建用户模型类对象，把明文密码加密以及is_staff=True
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            print(e)

        # 传入request对象和user对象，把用户信息写入session缓存(redis)中，并且把sessionid返回给浏览器
        # 存入cookie
        login(request, user)

        # 4、构建响应
        # return JsonResponse({'code': 0, 'errmsg': ' ok'})
        # 生成响应对象
        response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 返回响应结果
        return response

class LoginView(View):

        def post(self, request):
            '''实现登录接口'''
            # 1.接收参数
            dict = json.loads(request.body.decode())
            username = dict.get('username')
            password = dict.get('password')
            remembered = dict.get('remembered')

            # 2.校验(整体 + 单个)
            if not all([username, password]):
                return JsonResponse({'code': 400,
                                         'errmsg': '缺少必传参数'})

            # 3.验证是否能够登录
            user = authenticate(username=username,
                                password=password)

            # 判断是否为空,如果为空,返回
            # print('user:', user)
            if user is None:
                    return JsonResponse({'code': 400,
                            'errmsg': '用户名或者密码错误'})

            # 4.状态保持
            login(request, user)

            # 5.判断是否记住用户
            if remembered != True:
                # 7.如果没有记住: 关闭立刻失效
                request.session.set_expiry(0)
            else:
                # 6.如果记住:  设置为两周有效
                request.session.set_expiry(None)

            # 生成响应对象
            response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

            # 在响应对象中设置用户名信息.
            # 将用户名写入到 cookie，有效期 14 天
            response.set_cookie('username',
                        user.username,
                        max_age=3600 * 24 * 14)

            # 返回响应结果
            return response

# 登出
class LogoutView(View):
    """定义退出登录的接口"""
    def delete(self, request):

        """实现退出登录逻辑"""
        # 清理 session
        logout(request)
        # 创建 response 对象.
        response = JsonResponse({'code': 0,
                 'errmsg': 'ok'})
    # 调用对象的 delete_cookie 方法, 清除cookie
        response.delete_cookie('username')
        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

# from django.contrib.auth.mixins import LoginRequiredMixin

#
# 用户中心
class UserInfoView(View):
    def get(self,request):
        # 1.获取对象
        user = request.user

        # 2.构造相应数据返回
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'info_data':{
                'username':user.username,
                'mobile':user.mobile,
                'email':user.email,
                'email_active':user.email_active
            }
        })


# 更新email接口
class EmailView(View):
    @method_decorator(login_required)
    def put(self, request):
        # 1.提取参数
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2.校验参数
        if not email:
            return JsonResponse({'code':400,'errmsg':'缺少email'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return  JsonResponse({'code':400,'errmsg':'邮箱格式有误！'})
        # 3.数据更新（部分更新）
        user = request.user
        try:
            user.email = email
            user.email_active = False
            user.save()
        except Exception as e:
            logger.error(e)
            print(e)


        # =====发送邮箱验证邮件=====
        verify_url = user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)  # 异步调用！


        # 4.构建响应
        return JsonResponse({'code':400,'errmsg':'ok'})


# 确认邮箱接口
class VerifyEmailView(View):

    def put(self, request):
        # 1、提取查询字符串中token
        token = request.GET.get('token')
        # 2、校验token
        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({'code': 400, 'errmsg': '验证邮件无效！'})

        # 3、如果token有效，把邮箱的激活状态设置为True
        user.email_active = True
        user.save()

        return JsonResponse({'code': 0, 'errmsg': '邮箱激活成功！'})