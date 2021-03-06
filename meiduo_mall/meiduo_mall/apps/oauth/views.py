from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from .models import OAuthQQUser
from users.models import User
from django.contrib.auth import login
from itsdangerous import TimedJSONWebSignatureSerializer
import json,re
from django_redis import get_redis_connection


def generate_access_token(openid):
    # 功能：加密openid
    # 参数：openid用户的qq标示
    # 返回token值
    serializer = TimedJSONWebSignatureSerializer(
        secret_key=settings.SECRET_KEY,
        expires_in=3600 # 定义当前生成的token的有效期为3600秒
    )

    # 加密的数据是一个字典
    data = {"openid": openid}

    access_token = serializer.dumps(data)

    return access_token.decode()


def check_access_token(token):
    # 功能：解密出openid
    # 参数：token值
    # 返回值，返回openid
    serializer = TimedJSONWebSignatureSerializer(
        secret_key=settings.SECRET_KEY
    )

    data = serializer.loads(token)

    openid = data.get('openid')

    return openid

class QQUserView(View):

    def get(self, request):

        # 1、提取查询字符串参数code
        code = request.GET.get('code')
        # 2、验证code获取token
        try:
            oauth_qq = OAuthQQ(
                client_id=settings.QQ_CLIENT_ID,
                client_secret=settings.QQ_CLIENT_SECRET,
                redirect_uri=settings.QQ_REDIRECT_URI
            )
            token = oauth_qq.get_access_token(code)
            # 3、根据token获取openid
            openid = oauth_qq.get_open_id(access_token=token)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': 'qq登陆失败！'})


        try:
            oauth_qq = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist as e:
            # 4、用户没有绑定过qq：我们需要返回加密的openid
            access_token = generate_access_token(openid)
            return JsonResponse({
                'access_token': access_token
            })


        # 5、用户已经绑定过qq——登陆成功！！
        user = oauth_qq.user
        login(request, user) # 状态保持
        response = JsonResponse({'code':0, 'errmsg': 'ok'})
        response.set_cookie('username', user.username, max_age=3600*24*14)
        return response


    def post(self, request):
        # 根据用户传递来的手机号，判断用户是否注册美多商城账号
        user_info = json.loads(request.body.decode())
        mobile = user_info.get('mobile')
        password = user_info.get('password')
        sms_code = user_info.get('sms_code')
        access_token = user_info.get("access_token")

        if not all([mobile, password, sms_code, access_token]):
            return JsonResponse({'code': 400, 'errmsg': '缺少参数'})

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})

        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})


        conn = get_redis_connection('sms_code')
        sms_code_fron_redis = conn.get('sms_%s'%mobile)
        if not sms_code_fron_redis:
            return JsonResponse({'code': 400, 'errmsg': '验证码过期'})
        if sms_code_fron_redis.decode() != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '您输入的短信验证码有误！'})


        # 把openid从access_token参数中解密出来
        openid = check_access_token(access_token)

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist as e:
            print(e)
            # 1、没有注册，新建再绑定
            user = User.objects.create_user(
                username=mobile,
                mobile=mobile,
                password=password
            )
            # 绑定openid
            OAuthQQUser.objects.create(
                openid=openid,
                user=user
            )

            login(request, user)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', user.username, max_age=3600*24*14)
            return response


        # 2、已经注册，直接绑定
        # 绑定openid
        OAuthQQUser.objects.create(
            openid=openid,
            user=user
        )
        login(request, user)
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response

class QQFirstView(View):
    """提供QQ登录页面网址"""

    def get(self, request):
        # next 表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取 QQ 登录页面网址
        # 创建 OAuthQQ 类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 调用对象的获取 qq 地址方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'login_url':login_url})

