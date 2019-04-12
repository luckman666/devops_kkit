from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.urls import reverse
from kkitadmin import form_handle
from django.db.models import Q
# 登录验证装饰器
from django.contrib.auth.decorators import login_required
from .utils.pagination import Pagination
from django.shortcuts import HttpResponse
from MaintainWeb.models import *
from kkitadmin import app_setup
from kkitadmin import permissions

import json
app_setup.kkitadmin_auto_discover()

from kkitadmin.sites import site
# print("sites.",site.enabled_admins)


def KkitIndex(request):
    # print(site)
    return render(request, 'kkitadmin/kkitadmin_index.html',{'site':site})


# 过滤
def get_filter_result(request,querysets):
    #
    filter_conditions = {}
    # 当选择过滤的时候产生一个GET请求，通过for循环取出里面的字典值
    # 请求格式如下source=0&consultant=&status=&date__gte=
    # 接收格式<QueryDict: {'source': ['0'], 'consultant': [''], 'status': [''], 'date__gte': ['']}>
    for key,val in request.GET.items():
        if key in ('p', '_o', '_q'): continue
        if val:
            filter_conditions[key] = val

    # querysets是模型对象，直接返回条件查询结果，filter_conditions是查询的条件
    return querysets.filter(**filter_conditions),filter_conditions

def get_orderby_result(request,querysets,admin_class):
    """排序"""

    current_ordered_column = {}
    orderby_index = request.GET.get('_o')
    if orderby_index:
        # 点一下是正再点一下变负值，这里去list_display列表中的下标只能获取正值并且是数字类型
        # 得到用户所选的是哪列的名字
        orderby_key =  admin_class.list_display[ abs(int(orderby_index)) ]
        #生成新的字典{'name': '1'}，排序的列名，排序的列索引下标，以及是正是负，倒叙还是正序
        current_ordered_column[orderby_key] = orderby_index #为了让前端知道当前排序的列
        # print(current_ordered_column)
        # 如果获取的索引是-开头那么这次就需要去掉负号
        if orderby_index.startswith('-'):
            orderby_key =  '-'+ orderby_key
        # 如果不是，就直接返回排序数据和当前的排序状态，类似这样的{'name': '1'}
        return querysets.order_by(orderby_key),current_ordered_column
    else:
        # 没排序直接返回去源数据
        return querysets,current_ordered_column




def get_serached_result(request,querysets,admin_class):
    # 搜索
    search_key = request.GET.get('_q')
    if search_key:
        # 生成Q实例
        q = Q()
        # 将Q条件之间改成或的关系，默认是and
        q.connector = 'OR'
        for search_field in admin_class.search_fields:
            # 字段名__包含=某值   条件与条件之间是or的关系
            q.children.append(("%s__contains" % search_field, search_key))
            # 返回数据库查询结果
            return querysets.filter(q)
    # 如果没有直接返回源数据
    return querysets


@permissions.check_permission
@login_required
def table_obj_list(request,app_name,model_name,*args,**kwargs):
    """取出指定model里的数据返回给前端"""
    # site.enabled_admins全局字典里面存储着所有用户注册了的app和相对应的模块
    # 接收前端menu传递过来的值SalesCrm/customerinfo/类似这样，匹配出相应的app和模块
    # 得到用户在kkitadmin中自定义的，有过滤的类模型对象
    admin_class = site.enabled_admins[app_name][model_name]
    # 使用admin activate是post请求
    if request.method == "POST":
        # print(request.POST)
        #action是动作文本内容信息 前端go input显示的
        selected_action = request.POST.get('action')
        # selected_ids 勾选框的id
        selected_ids = json.loads(request.POST.get('selected_ids'))
        # print('selected_action',selected_action, selected_ids)
        if not selected_action:  # 如果有action参数,代表这是一个正常的action,如果没有,代表可能是一个删除动作
            if selected_ids:  # 这些选中的数据都要被删除
                admin_class.model.objects.filter(id__in=selected_ids).delete()
        else:  # 走action流程
            # 找到相关模板的数据
            selected_objs = admin_class.model.objects.filter(id__in=selected_ids)
            # 获取模块属性函数，并赋值给一个变量admin_action_func，这个函数是在admin_class对象中配置好的
            admin_action_func = getattr(admin_class, selected_action)
            # 执行该函数
            response = admin_action_func(request, selected_objs)
            # 返回结果
            if response:
                return response

    # 取出该模型的所有数据
    querysets = admin_class.model.objects.all().order_by('-id')
    # print('**',admin_class,'##',querysets)
    # 得到querysets过滤后查询的结果，filter_condtions用户查询的条件
    querysets,filter_condtions  = get_filter_result(request,querysets)
    # 为自定义的admin类添加filter_condtions 属性保存过滤选项值以便页面刷新后保留选项
    admin_class.filter_condtions = filter_condtions
    # print(request.GET.get)

    # searched queryset result
    querysets = get_serached_result(request, querysets, admin_class)
    admin_class.search_key = request.GET.get('_q', '')
    # 排序
    querysets, sorted_column = get_orderby_result(request, querysets, admin_class)

    # 分页
    # 获得模型的所有条目数
    data_count = querysets.count()
    # 生成需要分页的url
    base_url = '/kkitadmin/' + app_name+'/'+ model_name + '/'
    # 生成页面对象，p是前端返回的页面点击请求
    page = Pagination(request.GET.get('p', 1), data_count)
    page_str = page.page_str(base_url)
    # 对需要展示的数据进行分页。
    querysets = querysets[page.start:page.end]

    # searched






    return render(request,'kkitadmin/kkitadmin_right_context.html', locals())

def acc_login(request):
    error_msg = ''
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        # print(username,password)
        user = authenticate(username=username,password=password)
        # print(user)
        if user:
            # print("passed authencation",user)
            login(request,user)
            return redirect(request.GET.get('next','app_index'))
        else:
            error_msg = "Wrong username or password!"
    return render(request, 'kkitadmin/kkitadmin_login.html', {'error_msg':error_msg})


def acc_logout(request):
    logout(request)
    return redirect("/kkitadmin/login/")


@permissions.check_permission
@login_required
def table_obj_change(request,app_name,model_name,obj_id):

    """kingadmin 数据修改页"""

    # {'SalesCrm': {'customerinfo': < SalesCrm.kkitadmin.CustomerAdmin object at 0x0000000004297128 >}}
    # 获得表对象
    admin_class = site.enabled_admins[app_name][model_name]
    # 返回一个form对象，经过处理和样式处理之后的
    model_form = form_handle.create_dynamic_model_form(admin_class)
    # 获得行对象
    obj = admin_class.model.objects.get(id=obj_id)
    # 如果是get请求，那么就用这个form表单去渲染着行数据
    if request.method == "GET":
        form_obj = model_form(instance=obj)
    # 如果是post请求那么就用这个表单验证并且渲染这条数据
    elif request.method == "POST":
        form_obj = model_form(instance=obj,data=request.POST)
        if form_obj.is_valid():
            # 保存修改信息
            form_obj.save()
            return redirect("/kkitadmin/%s/%s/" % (app_name,model_name))

    # locals()返回字典类型的局部变量
    return render(request,'kkitadmin/table_obj_change.html',locals())

@permissions.check_permission
@login_required
def table_obj_delete(request,app_name,model_name,obj_id):
    # 取出要删除的表对象
    admin_class = site.enabled_admins[app_name][model_name]
    # 找到字段对象
    obj = admin_class.model.objects.get(id=obj_id)

    selected_objs = admin_class.model.objects.filter(id=obj_id)
    # 获取模块属性函数，并赋值给一个变量admin_action_func，这个函数是在admin_class对象中配置好的
    admin_action_func = getattr(admin_class, 'delete_selected_objs')
    response=admin_action_func(request, selected_objs)

    if request.method == "POST":
        # 删除字段对象
        obj.delete()
        return redirect("/kkitadmin/{app_name}/{model_name}/".format(app_name=app_name,model_name=model_name))
    if response:
        return response

    # return render(request,'kkitadmin/table_obj_delete.html',locals())

@permissions.check_permission
@login_required
def table_obj_add(request,app_name,model_name):
    admin_class = site.enabled_admins[app_name][model_name]
    model_form = form_handle.create_dynamic_model_form(admin_class,form_add=True)
    if request.method == "GET":
        form_obj = model_form()
    elif request.method == "POST":
        form_obj = model_form(data=request.POST)
        if form_obj.is_valid():
            form_obj.save()
            return redirect("/kingadmin/%s/%s/" % (app_name, model_name))

    return render(request,'kkitadmin/table_obj_add.html',locals())