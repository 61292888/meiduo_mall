
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from users.models import User
from .models import User
from django_redis import get_redis_connection
from django.contrib.auth import login,logout,authenticate
import json
import re
# from meiduo_mall.utils.views import login_required
from meiduo_mall.utils.view import login_required
from django.utils.decorators import method_decorator
# Create your views here.

import logging
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


        # 2、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
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
            return JsonResponse({'code':400, 'errmsg': '缺少参数'}, status=400)

        if not re.match(r'^\w{5,20}$', username):
            return JsonResponse({'code':400, 'errmsg': '用户名格式有误'}, status=400)

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({'code':400, 'errmsg': '密码格式有误'}, status=400)

        if password != password2:
            return JsonResponse({'code':400, 'errmsg': '密码输入不一致！'}, status=400)

        if not re.match(r'^\d{6}$', sms_code):
            return JsonResponse({'code': 400, 'errmsg': '验证码格式有误'}, status=400)

        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '请求统一用户协议！'}, status=400)


        # 手机验证码校验
        conn = get_redis_connection('sms_code')
        sms_code_from_redis = conn.get('sms_%s'%mobile)
        if not sms_code_from_redis:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码过期！'}, status=400)
        sms_code_from_redis = sms_code_from_redis.decode()
        if sms_code_from_redis != sms_code:
            return JsonResponse({'code':400, 'errmsg': '短信验证码有误！'}, status=400)

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
        response = JsonResponse({'code': 0, 'errmsg':' ok'})
        response.set_cookie(
            'username',
            username,
            max_age=3600*24*14
        )
        return response


# 登出
class LogoutView(View):

    def delete(self, request):
        # 1、获取用户对象
        # request.user是当前登陆的用户 或 是一个匿名用户
        # user是用户模型类对象 或  AnonymousUser匿名用户对象
        # user = request.user

        # 2、调用logout函数清楚用户session数据
        # 通过request对象提取cookie中是sessionid，经一步删除redis中的用户数据
        logout(request)

        # 3、构建响应
        response = JsonResponse({'code':0, 'errmsg': 'ok'})
        response.delete_cookie('username')

        return response

# 传统登陆(校验用户名和密码)
class LoginView(View):

    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        remembered = data.get('remembered')

        # 2、校验参数
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '参数缺失！'})

        if not re.match(r'^\w{5,20}$', username):
            return JsonResponse({'code':400, 'errmsg': '用户名格式有误'}, status=400)

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({'code':400, 'errmsg': '密码格式有误'}, status=400)


        # 3、数据处理(验证用户名和密码)
        # try:
        #     user = User.objects.get(username=username)
        # except User.DoesNotExist as e:
        #     return JsonResponse({'code': 400, 'errmsg': '用户名错误！'})
        # if not user.check_password(password):
        #     return JsonResponse({'code': 400, 'errmsg': '密码错误！'})

        # authenticate():功能、参数、返回值
        # 功能：传统身份验证——验证用户名和密码
        # 参数：request请求对象，username用户名和password密码
        # 返回值：认证成功返回用户对象，否则返回None
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({"code": 400, 'errmsg': '您提供的身份信息无法验证！'}, status=401)

        # 状态保持
        login(request, user)

        if remembered:
            # 设置session有效期默认2周
            request.session.set_expiry(None)
        else:
            # 设置session有效期为关闭浏览器页面则失效
            request.session.set_expiry(0) # 设置为0表示关闭浏览器清楚sessionid

        # 4、构建响应
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        response.set_cookie(
            'username',
            username,
            max_age=3600 * 24 * 14
        )

        return response



# from django.contrib.auth.mixins import LoginRequiredMixin
# 用户中心页接口
# class UserInfoView(LoginRequiredMixin, View):
class UserInfoView(View):

    @method_decorator(login_required)
    def get(self, request):

        # 1、获取用户对象
        user = request.user

        # 2、构造响应数据返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': user.username,
                'mobile': user.mobile,
                'email': user.email,
                'email_active': user.email_active
            }
        })


from celery_tasks.email.tasks import send_verify_email
# 更新邮箱接口
class EmailView(View):

    @method_decorator(login_required)
    def put(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2、校验参数
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少email'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式有误！'})

        # 3、数据处理(部分更新) ———— 更新邮箱
        user = request.user
        try:
            user.email = email
            user.email_active = False
            user.save()
        except Exception as e:
            print(e)


        # ======发送邮箱验证邮件=======
        verify_url = user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url) # 异步调用！

        # 4、构建响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})



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





from .models import Address
# 新增用户地址
class CreateAddressView(View):

    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place') # 详细地址
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 判断用户地址数量是否超过20个
        user = request.user
        count = Address.objects.filter(user=user).count()
        if count >= 20:
            return JsonResponse({'code': 400, 'errmsg': '数量超限'})


        # 2、校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400, 'errmsg': '缺少参数！'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 3、新建用户地址
        try:
            address = Address.objects.create(
                user=user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver, # 当前地址的标题，默认收货人名称就作为地址标题
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )

            # 如果当前新增地址的时候，用户没有设置默认地址，那么
            # 我们把当前新增的地址设置为用户的默认地址
            if not user.default_address:
                user.default_address = address
                user.save()

        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '新增地址失败！'})

        address_info = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,

            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,

            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 4、返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_info
        })





# 网页地址展示接口
# 本质：把当前用户所有地址信息返回
class AddressView(View):

    def get(self, request):
        # 1、根据用户，过滤出当前用户的所有地址
        user = request.user
        addresses = Address.objects.filter(
            user=user,
            is_deleted=False # 没有逻辑删除的地址
        )

        # 2、把地址转化成字典
        address_list = []
        for address in addresses:
            if address.id != user.default_address_id:
                # address：每一个地址对象
                address_list.append({
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
            else:
                address_list.insert(0, {
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })

        # 3、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'default_address_id': user.default_address_id,
            'addresses': address_list
        })





# 总结：相同的请求路径+不同的请求方法 = 统一类视图中
class UpdateDestroyAddressView(View):

    # 删除地址
    def delete(self, request, address_id):
        # 1、根据路径中的地址主键，获取地址对象
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '地址不存在'}, status=404)

        # 2、通过对象删除(真删除，逻辑删除)
        # 真删除: address.delete()
        # 逻辑删除
        address.is_deleted = True
        address.save()

        # 3、构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })


    # 更新地址接口
    def put(self, request, address_id):

        # 1、获取被更新的地址
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '资源未找到！'})

        # 2、提取参数
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')  # 详细地址
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 3、校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400, 'errmsg': '缺少参数！'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})


        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.tel = tel
        address.email = email
        address.save()

        # data = {"receiver": "韦小宝宝"}
        # update(**data) -->  update(receiver="韦小宝宝")
        # data.pop('province')
        # data.pop('city')
        # data.pop('district')
        # Address.objects.filter(pk=address_id).update(**data)
        # address = Address.objects.get(pk=address_id)

        address_info = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,

            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,

            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_info
        })



# 设置默认地址
class DefaultAddressView(View):

    def put(self, request, address_id):
        # 修改当前登陆用户对象的default_address指向address_id的地址
        user = request.user

        # default_address是ForeignKey类型，是Address对象
        # user.default_address = <Address对象>
        # user.default_address = Address.objects.get(pk=address_id)

        # user.default_address_id = <Address对象的主键>
        user.default_address_id = address_id

        user.save()

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })


# 修改地址标题
class UpdateTitleAddressView(View):

    def put(self, request, address_id):
        # 1、获取更新数据
        data = json.loads(request.body.decode())
        title = data.get('title')

        # 2、获取被修改的地址对象
        address = Address.objects.get(pk=address_id)

        # 3、修改并返回响应
        address.title = title
        address.save()

        return JsonResponse({'code': 0, 'errmsg': 'ok'})



# 修改用户密码
class ChangePasswordView(View):

    def put(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        new_password2 = data.get('new_password2')

        # 2、校验参数
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code':400, 'errmsg': '参数缺失'})

        # 新密码格式校验
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                             'errmsg': '密码最少8位,最长20位'})
        # 两次输入是否一致校验
        if new_password != new_password2:
            return JsonResponse({'code': 400,
                             'errmsg': '两次输入密码不一致'})

        # 旧密码校验
        # User.set_password()
        # User.check_password()
        user = request.user
        if not user.check_password(old_password):
            return JsonResponse({'code': 400, 'errmsg': '旧密码有误！'}, status=400)


        # 3、更新数据
        user.set_password(new_password)
        user.save()
        # 补充逻辑：清楚登陆状态
        logout(request)

        # 4、返回响应
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')
        return response
