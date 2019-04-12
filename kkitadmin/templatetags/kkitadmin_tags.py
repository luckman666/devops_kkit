from django.template import Library
from django.utils.safestring import mark_safe
import datetime ,time
# 生成一个注册器
register = Library()
# 过滤
@register.simple_tag #注册到语法库,过滤语法 ,就是把数据输入进来,内部执行后再返回去
def build_filter_ele(filter_column,admin_class):
    # filter_column过滤的字段，admin_class用户自定义的过滤类和所对应的模型
    # 取出该模型中涉及过滤的字段的所有值
    column_obj = admin_class.model._meta.get_field(filter_column)
    try:
        # 设置下拉框的选择的name属性用于区分每个过滤框
        filter_ele = "<h4 class='div-inline'> %s: </h4><select class='form-control select2 select2-hidden-accessible div-inline' style='width: 10%%;' name='%s'>" % (filter_column,filter_column)
        # 将对应字段中的choice生成下拉选框,并且生成首选项为-----

        for choice in column_obj.get_choices():
            # print(choice)
            selected = ''
            # 如果涉及到过滤的字段存在于处理返回过来的装有用户过滤选择的filter_condtions字典中，证明其已经被过滤了
            if filter_column in admin_class.filter_condtions:#当前字段被过滤了
                if str(choice[0]) == admin_class.filter_condtions.get(filter_column):#当前值被选中了
                    selected = 'selected'
                    # print('selected......')
            # 将上面的结果设定为选定值
            option = "<option value='%s' %s>%s</option>" % (choice[0],selected,choice[1])
            # 其他的选项继续列出
            filter_ele += option
    except AttributeError as e:
        # print("err",e)
        # print("到这了",filter_column)
        filter_ele = "<h4 class='div-inline'> %s: </h4><select class='form-control select2 select2-hidden-accessible div-inline' style='width: 10%%;' name='%s__gte'>" % (filter_column,filter_column)
        # 如果用户所选的过滤项是时间，因为时间没有choice会出这个错误AttributeError
        # get_internal_type()可以获取字段类型，如果字段是时间类型
        if column_obj.get_internal_type() in ('DateField','DateTimeField'):
            # 生成当前时间的值，2018-11-24格式
            time_obj = datetime.datetime.now()
            time_list = [
                ['','----------'],
                [time_obj,'Today'],
                # 对时间进行运算使用datetime.datetime.now() 当前时间- datetime.timedelta(7)后边数字是几就写几
                [time_obj - datetime.timedelta(7),'七天内'],
                # 直接将天数改成1就是本月初始
                [time_obj.replace(day=1),'本月'],
                [time_obj - datetime.timedelta(90),'三个月内'],
                # 改月份
                [time_obj.replace(month=1,day=1),'YearToDay(YTD)'],
                ['','ALL'],
            ]
            # 如果没有选择，默认值是空'',如果选择了，将option摘取出应有的值
            for i in time_list:
                selected = ''
                time_to_str = ''if not i[0] else "%s-%s-%s"%(i[0].year,i[0].month,i[0].day)
                if  "%s__gte"% filter_column in admin_class.filter_condtions:  # 当前字段被过滤了
                    # print('-------------gte')
                    if time_to_str == admin_class.filter_condtions.get("%s__gte"% filter_column):  # 当前值被选中了
                        selected = 'selected'
                option = "<option value='%s' %s>%s</option>" % \
                         (time_to_str ,selected,i[1])
                filter_ele += option

    filter_ele += "</select>"
    return mark_safe(filter_ele)


# 创建表中的行数据
@register.simple_tag
def  build_table_row(obj,admin_class):
    """生成一条记录的html element"""

    ele = ""
    # 需要显示的列名
    if admin_class.list_display:
        # enumerate可以对象列表生成索引下标和内容
        for index,column_name in enumerate(admin_class.list_display):
            # 取出列名对象
            column_obj = admin_class.model._meta.get_field(column_name)
            if column_obj.choices: #get_xxx_display
                # getattr取出对象属性的值，列对象，列属性
                column_data = getattr(obj,'get_%s_display'% column_name)()
            else:
                column_data = getattr(obj,column_name)
            # 生成列内容
            td_ele = "<td>%s</td>" % column_data
            if index == 0:
                td_ele = "<td><a href='%s/change/'>%s</a></td>" % (obj.id, column_data)
            ele += td_ele
    else:
        td_ele = "<td><a href='%s/change/'>%s</a></td>" % (obj.id,obj)

        ele += td_ele

    return mark_safe(ele)

# 没有特殊设置的显示数据方式
@register.simple_tag
def get_model_name(admin_class):

    return admin_class.model._meta.model_name.upper()

#


# 处理排序列的数字及其正负值
@register.simple_tag
def get_sorted_column(column,sorted_column,forloop):
    # column列名，sorted_column用户点击的列名及其排序情况{'id': '-0'} ，forloop循环次数，从0 开始
    # 如果列在sorted_column说明这一列呗排序了
    if column in sorted_column:#这一列被排序了,
        #你要判断上一次排序是什么顺序,本次取反
        last_sort_index = sorted_column[column]
        # 点一次排序倒叙会有-开头，如果为真
        if last_sort_index.startswith('-'):
            # 就去掉last_sort_index的符号，赋值给this_time_sort_index
            this_time_sort_index = last_sort_index.strip('-')
        else:
            # 否则添加上-
            this_time_sort_index = '-%s' % last_sort_index
        #     生成 href="?_o=8类似这样的标示给每个列
        return this_time_sort_index
    # 就按默认的排序生成顺序id并生成urlid,_o=0或者1
    else:
        return forloop

# 如果用户及排序又过滤，则需要对过滤结果进行保留，所以用这个函数对其href后边的参数进行拼接
@register.simple_tag
def render_filtered_args(admin_class,render_html=True):
    '''拼接筛选的字段'''
    # 如果用户有过滤的条件
    if admin_class.filter_condtions:
        ele = ''
        # 拿到他们的值类似这样&source=1&consultant=1
        for k,v in admin_class.filter_condtions.items():
            ele += '&%s=%s' %(k,v)
        if render_html:
            # 返回页面
            return mark_safe(ele)
        else:
            return ele

    else:
        return ''
# 排序标记箭头用的函数
@register.simple_tag
def render_sorted_arrow(column,sorted_column):
    if column in sorted_column:  # 这一列被排序了,
        last_sort_index = sorted_column[column]
        # last_sort_index排序的索引值，如果为负就是用下箭头，
        if last_sort_index.startswith('-'):
            arrow_direction = 'bottom'
        else:
            # 为正是用上箭头
            arrow_direction = 'top'
        ele = '''<span class="glyphicon glyphicon-triangle-%s" aria-hidden="true"></span>''' % arrow_direction
        return mark_safe(ele)
    return ''
# 前分页
# @register.simple_tag
# def render_paginator(querysets,admin_class,sorted_column):
#     ele = '''
#       <ul class="pagination">
#     '''
#     for i in querysets.paginator.page_range:
#         if abs(querysets.number - i) < 2 :#display btn
#             active = ''
#             if querysets.number == i : #current page
#                 active = 'active'
#             filter_ele = render_filtered_args(admin_class)
#
#             sorted_ele = ''
#             if sorted_column:
#                 sorted_ele = '&_o=%s' % list(sorted_column.values())[0]
#
#             p_ele = '''<li class="%s"><a href="?_page=%s%s%s">%s</a></li>'''  % (active,i,filter_ele,sorted_ele,i)
#
#             ele += p_ele
#
#
#     ele += "</ul>"
#
#     return mark_safe(ele)

@register.simple_tag
def get_current_sorted_column_index(sorted_column):
    # 如果有排序，那么返回排序列id的值，-1或者3之类的
    return list(sorted_column.values())[0] if sorted_column else ''

@register.simple_tag
def get_obj_field_val(form_obj,field):
    '''返回model obj具体字段的值'''

    return getattr(form_obj.instance,field)

# 返回表名别称
@register.simple_tag
def get_model_verbose_name(admin_class):
    return admin_class.model._meta.verbose_name


@register.simple_tag
def get_available_m2m_data(field_name,form_obj,admin_class):
    """返回的是m2m字段关联表的所有数据"""
    # 取出字段对象
    field_obj = admin_class.model._meta.get_field(field_name)
    # 所有该字段的值，总共有的值
    obj_list = set(field_obj.related_model.objects.all())
    # 用户选择了的值，selected_data 右侧框中有的值，被form表单渲染出来的值
    selected_data = set(getattr(form_obj.instance ,field_name).all())
    # 剩下的就是左边还剩下的用户未选择的值。
    return obj_list - selected_data






@register.simple_tag
def get_selected_m2m_data(field_name,form_obj,admin_class):
    """返回已选的m2m数据"""

    selected_data = getattr(form_obj.instance ,field_name).all()
    return selected_data



@register.simple_tag
def display_all_related_objs(obj):
    """
    显示要被删除对象的所有关联对象
    :param obj:
    :return:
    """
    ele = "<ul>"
    # ele += "<li><a href='/kkitadmin/%s/%s/%s/change/'>%s</a></li>" %(obj._meta.app_label,
    #                                                                  obj._meta.model_name,
    #                                                                  obj.id,obj)
    # obj._meta.related_objects能找到该表关联的字段

    for reversed_fk_obj in obj._meta.related_objects:
        # 得到关联字段的名称
        related_table_name =  reversed_fk_obj.name
        # print(related_table_name)
        # 拼接反向查询的字符串
        related_lookup_key = "%s_set" % related_table_name
        related_objs = getattr(obj,related_lookup_key).all() #反向查所有关联的数据
        ele += "<li>%s<ul> "% related_table_name

        if reversed_fk_obj.get_internal_type() == "ManyToManyField":  # 不需要深入查找
            for i in related_objs:
                ele += "<li><a href='/kkitadmin/%s/%s/%s/change/'>%s</a> 记录里与[%s]相关的的数据将被删除</li>" \
                       % (i._meta.app_label,i._meta.model_name,i.id,i,obj)
        else:
            for i in related_objs:
                #ele += "<li>%s--</li>" %i
                ele += "<li><a href='/kkitadmin/%s/%s/%s/change/'>%s</a></li>" %(i._meta.app_label,
                                                                                 i._meta.model_name,
                                                                                 i.id,i)
                ele += display_all_related_objs(i)

        ele += "</ul></li>"

    ele += "</ul>"

    return ele






