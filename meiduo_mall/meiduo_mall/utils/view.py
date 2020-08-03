
from django.http import JsonResponse



# 定义一个装饰器，验证是否已经登陆
def login_required(func):
    # func：是视图函数
    def wrapper(request, *args, **kwargs):
        # 添加功能代码
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        else:
            return JsonResponse({'code': 400, 'errmsg': '您未登陆！'})

    return wrapper