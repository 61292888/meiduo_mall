
from .models import GoodsCategory

def get_breadcrumb(category_id):
    # 根据category_id获取导航信息
    ret_dict = {}

    category = GoodsCategory.objects.get(pk=category_id)
    # 1级
    if not category.parent:
        ret_dict['cat1'] = category.name
    # 2级
    elif not category.parent.parent:
        ret_dict['cat2'] = category.name
        ret_dict['cat1'] = category.parent.name
    # 3级
    elif not category.parent.parent.parent:
        ret_dict['cat3'] = category.name
        ret_dict['cat2'] = category.parent.name
        ret_dict['cat1'] = category.parent.parent.name

    return ret_dict

