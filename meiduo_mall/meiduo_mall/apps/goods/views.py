from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
# Paginator:分页器
from django.core.paginator import Paginator,EmptyPage
from .models import SKU,GoodsCategory
from .utils import get_breadcrumb
# Create your views here.


# sku商品列表数据返回（分页）
class ListView(View):

    def get(self, request, category_id):

        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering') # -create_time

        # 1、获取sku商品数据 —— 排序
        skus = SKU.objects.filter(
            category_id=category_id,
            is_launched=True # 商品是上架状态
        ).order_by(ordering) # order_by('-create_time')


        # 2、分页 —— 根据page和page_size分页
        # 使用django的接口对一个模型类查询集分页
        # 实例化一个分页器对象，传入skus被分页对目标数据(查询集)，传入page_size来指定按照每页几个划分
        paginator = Paginator(skus, page_size)
        print("数据总量：", paginator.count)
        print("总页数：", paginator.num_pages)

        try:
            # 分页器对象.page函数调用传入page标示获取第几页
            # 返回值是一个查询集，表示当前页数据查询集
            cur_page = paginator.page(page)
        except EmptyPage as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '空页！'})

        ret_list = []
        for sku in cur_page:
            ret_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url.url,
                'name': sku.name,
                'price': sku.price
            })

        breadcrumb = get_breadcrumb(category_id)

        # 3、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': ret_list,
            'count': paginator.num_pages # 总页数
        })


# 热销商品
class HotGoodsView(View):

    def get(self, request, category_id):
        # 1、获取热销商品(取销量最高的2个)
        skus = SKU.objects.filter(
            category_id=category_id,
            is_launched=True
        ).order_by('-sales')[:2] # 根据销量降序排列

        # 2、构建响应返回
        ret_list = []
        for sku in skus:
            ret_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'hot_skus': ret_list
        })



# 使用Haystack提供的搜索视图，实现搜索
# SearchView搜索视图基类，它提供的视图对应的接口就是：
# 请求方式：GET
# 请求路径：search/
# 请求参数：?q=华为&page=1&page_size=3
# 响应数据：默认返回的是完整的html页面；不符合我们的接口需求，所以调整它的返回值
from haystack.views import SearchView
class MySearchView(SearchView):
    # 当前搜索是"短语精确搜索" —— 不会把用户的搜索词进行分词处理；

    # 构建一个响应
    def create_response(self):
        # 默认SearchView搜索视图逻辑：先搜索出结果，再调用create_response函数构建响应

        # 1、获取全文检索的结果
        context = self.get_context()

        # context['query'] 检索词
        # context['paginator'] 分页器对象
        # context['paginator'].count 数据量
        # context['paginator'].num_pages 当前页
        # context['page'].object_list 列表(SearchResult对象)
        # SearchResult.object 被搜索到的SKU模型类对象

        sku_list = []
        # 2、从查询的结果context中提取查询到的sku商品数据
        for search_result in context['page'].object_list:
            # search_result: SearchResult对象
            # search_result.object: SKU模型类对象
            sku = search_result.object
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url,
                'searchkey': context['query'],
                'page_size': context['paginator'].per_page,
                'count': context['paginator'].count
            })


        # sku_list = [
        #     {
        #         'id': 1,
        #         'name': '苹果100',
        #         'price': 10,
        #         'default_image_url': 'http://image.meiduo.site:8888/group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429',
        #         'searchkey': '华为',
        #         'page_size': 5,
        #         'count': 12
        #     }
        # ]

        return JsonResponse(sku_list, safe=False)

