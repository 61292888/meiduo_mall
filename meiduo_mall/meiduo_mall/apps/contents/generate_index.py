"""
该模块中实现首页静态化
"""
# loader：读取/加载模版文件
from django.template import loader
from django.conf import settings
import os
from goods.models import GoodsChannel,GoodsCategory
from contents.models import ContentCategory,Content

# 这个函数功能：渲染出完整的index.html首页静态文件
def generate_static_index_html():

    # 模版参数categories是首页分类频道
    categories = {}

    # 获取首页所有的分类频道数据
    channels = GoodsChannel.objects.order_by(
        'group_id',
        'sequence'
    )
    # 遍历所有是分类频道，构建以组号作为key的键值对
    for channel in channels:
        # channel: GoodsChannel对象
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                'channels': [], # 当前分组中的分类频道(一级分类)
                'sub_cats': [] # 二级分类
            }
        # (1)、填充当前组中的一级分类
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # (2)、填充当前组中的二级分类
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        for cat2 in cat2s:
            # cat2：二级分类对象

            cat3_list = [] # 每一次遍历到一个二级分类对象的时候，初始化一个空列表，用来构建三级分类
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            # (3)、填充当前组中的三级分类
            for cat3 in cat3s:
                # cat3；三级分类对象
                cat3_list.append({
                    'id': cat3.id,
                    'name': cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3_list # 三级分类
            })


    # 模版参数contents是页面广告数据
    contents = {}
    # 广告分类(位置)
    content_cats = ContentCategory.objects.all()
    for content_cat in content_cats:
        # content_cat：是每一个广告的分类，如"轮播图"
        contents[content_cat.key] = Content.objects.filter(
            category=content_cat,
            status=True
        ).order_by('sequence')

    # 模版参数
    context = {
        'categories': categories,
        'contents': contents
    }

    # ==========广告首页渲染=========
    # 1、获取模版对象
    template = loader.get_template('index.html')
    # 2、传入模版参数，渲染页面
    html_text = template.render(context)
    # 3、写入font_end_pc文件夹下的index.html静态文件中
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')

    with open(file_path, 'w') as f:
        f.write(html_text)


