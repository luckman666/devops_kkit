from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.shortcuts import render,redirect,HttpResponse
from MaintainWeb.models import *
from django.shortcuts import render, redirect, HttpResponse
from django.forms import Form
from django.forms import fields
from django.forms import widgets
import json
import time
import datetime






@login_required
def trouble_list(request):
    # 先获取用户信息
    # user_info = request.session.get('user_info') # {id:'',}

    current_user_id = request.user.id
    result = Trouble.objects.filter(user_id=current_user_id).order_by('status').only('title','status','ctime','processer')
    # print(result)
    return render(request,'MaintainWeb/trouble_list.html',{'result': result})

# 创建表单的验证类

class TroubleMaker(Form):
    title = fields.CharField(
        max_length=32,
        widget=widgets.TextInput(attrs={'class': 'form-control'})
    )
    detail = fields.CharField(
        widget=widgets.Textarea(attrs={'id':'detail','class':'kind-content'})
    )
@login_required
def trouble_create(request):
    # 如果是get请求就发送form表单中的数据给前端
    if request.method == 'GET':
        form = TroubleMaker()
        print('formget', form)
    else:
        #接收前端post的数据
        form = TroubleMaker(request.POST)
        print('form',form)
        if form.is_valid():
            # title,content
            # form.cleaned_data
            # 通过后加入字典中
            dic = {}
            dic['user_id'] = request.user.id # session中获取
            dic['ctime'] = datetime.datetime.now()
            dic['status'] = request.user.is_admin
            print("lalala",dic)
            # 将前端post传过来的form表单验证的数据，添加到字典中
            dic.update(form.cleaned_data)
            # print("hahaha",dic)
            # {'user_id': 1, 'ctime': datetime.datetime(2018, 11, 12, 20, 39, 25, 75325), 'status': 1, 'title': '你好啊','detail': '没事啦啦啦'}
            # 将字典中的数据保存到数据库中
            Trouble.objects.create(**dic)
            # 反解析到处理首页
            return redirect('/trouble/trouble-list')
    # 返回form表单数据
    return render(request, 'MaintainWeb/trouble_create.html', {'form':form})
# 编辑保障单
@login_required
def trouble_edit(request,nid):
    # 直接调用接口查看
    if request.method == "GET":
        # 查找单据id和status=1未处理的单子，并且只取三列
        obj = Trouble.objects.filter(id=nid, status=request.user.is_admin).only('id', 'title', 'detail').first()
        # 如果没有
        if not obj:
            return HttpResponse('已处理中的保单章无法修改..')
        # initial 仅初始化，什么也不填是验证
        # form = TroubleMaker(initial={'title': obj.title,'detail': obj.detail} )
        # data会验证，这样前端页面会显示报错信息error.0可以抓到
        form = TroubleMaker(data={'title': obj.title, 'detail': obj.detail})
        # 将从form中取出的数据返回前端页面
        return render(request,'MaintainWeb/trouble_edit_order.html',{'form':form,'nid':nid})
    else:
        # 如果是post来的数据
        form = TroubleMaker(data=request.POST)
        if form.is_valid():
            # V是返回的受响应的行数，id=nid,确定哪个文章 status=1确定其未处理的状态
            v = Trouble.objects.filter(id=nid, status=1).update(**form.cleaned_data)
            if not v:
                return HttpResponse('已经被处理')
            else:
                return redirect('/trouble/trouble-list')
        return render(request, 'MaintainWeb/trouble_edit_order.html', {'form': form, 'nid': nid})
# 删除保障单
@login_required
def trouble_delete(request,nid):
    if request.method == "GET":
        v=Trouble.objects.filter(id=nid).delete()
        # print(v)
        if not v:
            return HttpResponse('删除有误..')
        else:
            return redirect('/trouble/trouble-list/')
# 处理订单
@login_required
def trouble_kill_list(request):
    from django.db.models import Q
    # 首选带入用户id，需要该写成session取
    current_user_id = request.user.id
    # Q是多条件或关系，首选是有处理权限的人，还有订单是未处理的单据，按状态排序
    result = Trouble.objects.filter(Q(processer_id=current_user_id)|Q(status=request.user.is_admin)).order_by('status')
    # 页面跳转到编辑，返回相关结果给改页面
    return render(request, 'MaintainWeb/trouble_kill_list.html', {'result':result})

# 抢单编辑form表单验证
class TroubleKill(Form):
    solution = fields.CharField(
        widget=widgets.Textarea(attrs={'id':'solution','class':'kind-content'})
    )
    # current_user_id = fields.IntegerField()

# 处理订单的页面
@login_required
def trouble_kill(request,nid):
    current_user_id = request.user.id
    if request.method == 'GET':

        # 查找当前有处理权限的用户所能看到的单据
        ret = Trouble.objects.filter(id=nid, processer=current_user_id).count()
        # 如果这个单据不为空，说明抢单成功
        if not ret:
            # 以单据id和状态为未处理的单据为条件，直接更新为处理人为谁，并且把单据状态更新为处理中
            v = Trouble.objects.filter(id=nid,status=1).update(processer=current_user_id,status=2)
            # 如果更新不成功，显示没抢到
            if not v:
                return HttpResponse('手速太慢...')

        # 获取已经抢到单据的信息
        obj = Trouble.objects.filter(id=nid).first()
        # 将取出的信息存储在form对象中

        form = TroubleKill(initial={'title': obj.title,'solution': obj.solution })
        # data = TplType.objects.all().values('mtype', 'tplnew1__titleInfo', 'tplnew1__contentId__content')
        # data.query.group_by=['mtype']
        # print(data)
        # tyList=[]
        # for i in list(data):
        #     mty=i.get('mtype')
        #     tyList.append(mty)
        # print(set(tyList))
        # 反馈给前端
        return render(request,'MaintainWeb/trouble_kill.html',{'obj':obj,'form': form,'nid':nid})
    else:

        # 接收post数据前先去数据库查询一下。post来的单据是否正确
        # 编写单据并提交，首选获取单据信息，判断单据id，处理者id，状态为处理中，count()返回结果行数
        ret = Trouble.objects.filter(id=nid, processer=current_user_id,status=2).count()
        unHandle = request.POST.get('unHandle')
        unHandle= int(unHandle)
        # print(unHandle)
        #防止盗取单据信息非法提交，私自post该端口数据，所有post请求与上述条件不符合的都将被拒绝返回非法提交
        if not ret:
            return HttpResponse('非法提交')
        if unHandle:
            Trouble.objects.filter(id=nid, status=2).update(processer=None, status=1)
            return redirect('/trouble/trouble-kill-list.html')
        #将提交数据进行form验证
        form = TroubleKill(request.POST)
        if form.is_valid():
            dic = {}
            dic['status'] = 3
            dic['solution'] = form.cleaned_data['solution']
            dic['ptime'] = datetime.datetime.now()
            # 更新数据库数据
            Trouble.objects.filter(id=nid, processer=current_user_id,status=2).update(**dic)
            # 专项到列表页面
            return redirect('/trouble/trouble-kill-list.html')
        # 查询处理
        obj = Trouble.objects.filter(id=nid).first()
        # 返回页面并提交相关数据
        return render(request, 'MaintainWeb/trouble_kill.html', {'obj': obj, 'form': form, 'nid': nid })

# class CreateModel(Form):
#     mtype = fields.CharField(
#         max_length=32,
#         widget=widgets.TextInput(attrs={'class': 'form-control'})
#     )
#     titleInfo = fields.CharField(
#         max_length=32,
#         widget=widgets.TextInput(attrs={'class': 'form-control'})
#     )
#     content = fields.CharField(
#         widget=widgets.Textarea(attrs={'id':'content','class':'kind-content'})
#     )







def backend_trouble_create_model(request,nid):

    if request.method == 'GET':
        form = CreateModel()
        return render(request,'bky/trouble_create_model.html',{ 'form': form ,'nnid':nid })

    else:
        form=CreateModel(request.POST)
        if form.is_valid():
            mobj={}
            mobj['processer']=32
            mobj['titleInfo'] = form.cleaned_data.get('titleInfo')
            content = form.cleaned_data.get('content')
            mtype = form.cleaned_data.get('mtype')
            tynid=TplType.objects.filter(mtype=mtype).values('nid')
            # print(list(tynid)[0].get('nid'))
            if tynid:
                mobj['typeid_id'] = list(tynid)[0].get('nid')
            else:
                tyid = TplType.objects.create(mtype=mtype).nid
                mobj['typeid_id'] = tyid
            ttid=TplNewContent1.objects.create(content=content).nid
            mobj['contentId_id']=ttid
            TplNew1.objects.create(**mobj)

            return redirect('trouble-kill-' + nid + '.html' )

    return render(request, 'bky/trouble_create_model.html', {'form': form, 'nnid': nid })


def trouble_report(request):

    return render(request,'bky/backend_trouble_report.html')


from django.db import connection, connections
def trouble_json_report(request):

    # from datetime import datetime
    # 数据库中获取数据
    user_list = UserInfo.objects.filter()
    response = []
    for user in user_list:
        # 执行原生sql
        cursor = connection.cursor()
        # 时间格式化date_format转换成字符串，unix_timestamp将字符串转换成时间戳
        cursor.execute("""select unix_timestamp(date_format(ctime,"%%Y-%%m-01"))*1000,count(id) from repository_trouble where processer_id = %s group by unix_timestamp(date_format(ctime,"%%Y-%%m-01"))*1000 """, [user.nid,])
        # 获取所有结果
        result = cursor.fetchall()

        # print(user.username,result)
        temp = {
            'name': user.username,
            'data':result
        }
        response.append(temp)
    import json
    return HttpResponse(json.dumps(response))

# 测试图形
def trouble_prosses(request):

    return render(request,'bky/backend_trouble_prosses.html')

def trouble_json_prosses(request):


    # 数据库中获取数据
    user_list = UserInfo.objects.filter()
    response = []
    for user in user_list:
        # 执行原生sql
        cursor = connection.cursor()
        # 时间格式化date_format转换成字符串，unix_timestamp将字符串转换成时间戳
        cursor.execute("""select %s,count(id) from repository_trouble where processer_id = %s group by date_format(ctime,"%%Y-%%m") """, [user.username,user.nid,])
        # 获取所有结果
        result = cursor.fetchall()

        print(user.username,result)
        temp = {
            'name': user.username,
            'data':result
        }
        response.append(temp)
    import json
    return HttpResponse(json.dumps(response))
