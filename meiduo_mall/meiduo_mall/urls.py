"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 总路由对当前自路由不做匹配，直接指向导子应用的自路由
    re_path(r"",include("users.urls")),

    re_path('', include('verifications.urls')),
    # oauth
    re_path('', include('oauth.urls')),
    # areas:
    path('', include('areas.urls')),
    # 广告
    path('', include('contents.urls')),
    # 商品
    path('', include('goods.urls')),
]
