# 导入
from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer,BadSignature
from django.conf import settings

# 我们重写用户模型类, 继承自 AbstractUser
class User(AbstractUser):
    """自定义用户模型类"""

    # 额外增加 mobile 字段
    mobile = models.CharField(max_length=11,
                              unique=True,
                              verbose_name='手机号')

    # 新增 email_active 字段
    # 用于记录邮箱是否激活, 默认为 False: 未激活
    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')

    # 对当前表进行相关设置:
    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    # 在 str 魔法方法中, 返回用户名称
    def __str__(self):
        return self.username



    def generate_verify_email_url(self):
        """
        生成邮箱验证链接
        :param user: 当前登录用户
        :return: verify_url
        """
        # 调用 itsdangerous 中的类,生成对象
        # 有效期: 1天
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=60 * 60 * 24)
        # 拼接参数
        data = {'user_id': self.id, 'email': self.email}
        # 加密生成 token 值, 这个值是 bytes 类型, 所以解码为 str:
        token = serializer.dumps(data).decode()
        # 拼接 url
        verify_url = settings.EMAIL_VERIFY_URL + token
        # 返回
        return verify_url

    # 校验token值，返回用户对象
    @staticmethod
    def check_verify_email_token(token):
        """
        校验token值
        :param token:token值
        :return: 用户对象 或None
        """

        seriaalizer = TimedJSONWebSignatureSerializer(secret_key=settings.SECRET_KEY)

        try:
            user_info = seriaalizer.loads(token)
        except BadSignature as e:
            print(e)
            return None

        user_id = user_info.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as e:
            print(e)
            return  None
        return user