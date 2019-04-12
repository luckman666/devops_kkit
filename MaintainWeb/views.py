import random
import string
from utils import response_code
import os,re
from django.shortcuts import render,HttpResponseRedirect,HttpResponse,redirect
from django.contrib.auth.decorators import  login_required
from django.core.exceptions import ObjectDoesNotExist
from backend.utils import json_date_to_stamp,json_date_handler
from django.views.decorators.csrf import csrf_exempt
from MaintainWeb import models
from kkit import settings
from django.contrib import auth
from MaintainWeb import models,utils
from MaintainWeb import host_mgr
from celery import chain
import django
import json
import datetime
from MaintainWeb import tasks,host_software_log

@login_required
def dashboard(request):
    # 看用户是否为超级用户
    if request.user.is_superuser:
        # 查看该用户的所有日志记录并且按id倒叙排列10条
        recent_tasks = models.TaskLog.objects.all().order_by('-id')[:10]
        # 返回到首页传递一个user,和他的任务日志信息
        return render(request, 'index.html', {
            'login_user': request.user,
            'recent_tasks': recent_tasks
        })
    else:
        # 如果不是管理员直接返回到hosts页面
        return HttpResponseRedirect('/hosts/')
# 临时路径
def adm(request):
    print('daozhelei',request)
    return HttpResponseRedirect('/')

def login(request):

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')
        # 用django自己的认证模块进行验证
        user = auth.authenticate(username=username,password=password)
        # 如果用户名不为空
        if user is not None:
            try:
                # 需要有账号过期开始时间和结束时间，给临时账户提供的方法
                if user.valid_begin_time and user.valid_end_time:
                    # 如果用户的当前时间大于失效的开始日期，并且小于失效的结束日期，说明账号现在是可用状态
                    if django.utils.timezone.now() > user.valid_begin_time and django.utils.timezone.now()  < user.valid_end_time:
                        # 登录用户
                        auth.login(request,user)
                        # session保持30分钟
                        request.session.set_expiry(60*30)
                        # 重定向访问相关路径，获取next指定的路径，如果没有返回首页
                        return HttpResponseRedirect(request.GET.get("next") if request.GET.get("next") else "/")
                    else:
                        # 登录错误返回登录页
                        return render(request,'login.html',{'login_err': '您的账号已过期，请联系系统管理员!'})
                else:
                    # 如果没有设置失效日期也可以登录，
                    auth.login(request, user)
                    request.session.set_expiry(60 * 30)
                    return HttpResponseRedirect(request.GET.get("next") if request.GET.get("next") else "/")
            # 如果未发现账户对象，返回账户没建立
            except ObjectDoesNotExist:
                    return render(request,'login.html',{'login_err': u'Kkit账户还未设定,请先登录后台管理界面创建Kkit账户!'})
        # 如果账户密码验证失败返回
        else:
            return render(request,'login.html',{'login_err': '用户名或密码错误!'})
    #     get请求返回登录页
    else:
        return render(request, 'login.html')


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


@login_required
def hosts(request):
    DiffPath = 'hosts'
    # hobj =models.Hosts._meta.fields
    # print(hobj)
    # 前端展示所需要的字段名
    # FieldName = [f.verbose_name for f in hobj if f.verbose_name not in ['enabled', 'is group','ID','创建时间','IDC机房','操作系统类型']]
    # print(FieldName)
    # 获取用户组id
    FieldName=['主机ip','主机名','端口','系统','创建时间','备注信息']
    selected_g_id = request.GET.get('selected_group')
    if selected_g_id:
        # 检查selected_g_id的字符串是不是只包含数字
        if selected_g_id.isdigit():
            selected_g_id = int(selected_g_id)
    UserEmail = models.UserProfile.objects.all()
    recent_logins = utils.recent_accssed_hosts(request)
    # 未分组的服务器总数和服务器对象
    UndistributedHostCount, UndistributedHost = utils.undistributed_host(request)
    return render(request, 'MaintainWeb/hosts.html', {'login_user':request.user,
                                                      'DiffPath':DiffPath,
                                                      'FieldName':FieldName,
                                                      'UserEmail':list(UserEmail),
                                         'selected_g_id': selected_g_id,
                                        'active_node':"/hosts/?selected_group=-1",
                                        'recent_logins':recent_logins,  #去重后用户最近14天登录的主机id集合
                                        'webssh':settings.SHELLINABOX,
                                        'undistributed_host_count': UndistributedHostCount,
                                                    'UndistributedHost':UndistributedHost})


# 授权模块
@login_required
def accredit(request):
    token = utils.Token(request)
    Taskid,TaskInfoList, task_log_detail_obj_ids = token.generate()
    # print('TaskInfoList',TaskInfoList)
    TaskInfoList=json.dumps(TaskInfoList)
    # 调用异步
    tasks.SendEmail.apply_async(args=[TaskInfoList, Taskid,task_log_detail_obj_ids])
    return HttpResponse(Taskid)


@login_required
def dashboard_summary(request):

    if request.method == 'GET':
        summary_data = utils.dashboard_summary(request)
        return HttpResponse(json.dumps(summary_data,default=json_date_to_stamp))


@login_required
def user_login_counts(request):
    filter_time_stamp = request.GET.get('time_stamp')
    assert  filter_time_stamp.isdigit()
    filter_time_stamp = int(filter_time_stamp) / 1000
    filter_date_begin = datetime.datetime.fromtimestamp(filter_time_stamp)
    filter_date_end = filter_date_begin + datetime.timedelta(days=1)

    user_login_records = models.Session.objects.filter(date__range=[filter_date_begin,filter_date_end]).\
        values('bind_host',
               'bind_host__host_user__username',
               'user',
               'user__name',
               'bind_host__host__hostname',
               'date')

    return  HttpResponse(json.dumps(list(user_login_records),default=json_date_handler))


@login_required
def dashboard_detail(request):
    if request.method == 'GET':
        detail_ins = utils.Dashboard(request)
        res = list(detail_ins.get())
        return HttpResponse(json.dumps(res,default=json_date_handler))

# 临时令牌,废弃
@login_required
def token_gen(request):
    token = utils.Token(request)
    token_key = token.generate()
    return HttpResponse(token_key)

# @permissions.check_permission
@login_required
def hosts_multi(request):
    DiffPath='cmdfile'
    UserId = request.user.id
    # 最近十条的执行记录
    recent_tasks = models.TaskLog.objects.filter(user_id=UserId).order_by('-id')[:10]
    hobj =models.Hosts._meta.fields
    # 前端展示所需要的字段名
    # FieldName = [f.verbose_name for f in hobj if f.verbose_name not in ['enabled', 'is group','ID']]
    #
    FieldName = ['主机IP','主机名','idc','系统','端口','备注信息','创建时间']
    return render(request,'MaintainWeb/hosts_multi.html',{'login_user':request.user,
                                              #'host_groups':valid_hosts,
                                              'FieldName':FieldName,
                                              'recent_tasks': recent_tasks,
                                              'active_node':'/hosts/multi',
                                                          'DiffPath':DiffPath})
@login_required
def file_download(request,task_id):

    file_path = "%s/task_data/%s" %(settings.FileUploadDir,task_id)
    return utils.send_zipfile(request, task_id,file_path)


@login_required
def multitask_task_action(request):
    if request.method == 'POST':
        # print('request.POST!!!!!!!!!!!!',request.POST)
        action = request.POST.get('action')
        m = host_mgr.MultiTask(action,request)
        res = m.run()
        return HttpResponse(json.dumps(res))


# 模态框点击确认后执行的执行命令的函数
@login_required
def multitask_cmd(request):

    task_type=request.POST.get('task_type')
    multi_task = host_mgr.MultiTask(task_type,request)
    task_id = multi_task.run()
    if task_id:
        return HttpResponse(task_id)
    else:
        return HttpResponse("TaskCreatingError")


@login_required
def HostCounts(request):
    HostList=[]
    HostGroup =utils.multitask_HostCounts(request)
    for k,v in HostGroup.items():
        dic = {}
        if k == '未分类主机':
            dic['name']=k
            dic['y'] = v
            # 初始化显示效果
            dic['sliced']='true'
            dic['selected']='true'
        else:
            dic['name']=k
            dic['y'] = v
        HostList.append(dic)
    # print( HostList)

    return HttpResponse(json.dumps(HostList))


# 多任务调用返回数据接口
@login_required
def multitask_res(request):
    multi_task = host_mgr.MultiTask('get_task_result',request)
    task_result = multi_task.run()
    return HttpResponse(task_result)


# 取最近10个任务的id
@login_required
def RequestTasksId(request):
    # TaskNumber = request.POST.get('TaskNumber')
    # TaskIdList=models.TaskLog.objects.filter(user=request.UserProfile,).order_by('-id')[:int(TaskNumber)]

    TaskIdList =[]
    TaskIdObj = models.TaskLog.objects.filter(user_id=request.user.id).order_by('-id')[0:10]
    for taskinfo in TaskIdObj:
        TaskDic = {}
        TaskDic['id'] = taskinfo.id
        TaskDic['task_type']=taskinfo.task_type
        TaskDic['cmd'] = taskinfo.cmd
        TaskIdList.append(TaskDic)

    return HttpResponse(json.dumps(TaskIdList))

# 获取还在运行中的任务id
@login_required
def RequestRuningTasksId(request):

    TaskIdList = []
    TaskIdObj = models.TaskLog.objects.filter(user_id=request.user.id).order_by('-id')[0:10]

    for taskinfo in TaskIdObj:
        task = models.TaskLogDetail.objects.filter(child_of_task_id=taskinfo.id)
        print('task',task)
        for sutask in task:
            if (sutask.result=='unknown'):
                TaskDic = {}
                TaskDic['id'] = taskinfo.id
                TaskDic['task_type'] = taskinfo.task_type
                TaskDic['cmd'] = taskinfo.cmd
                if TaskDic not in TaskIdList:
                    TaskIdList.append(TaskDic)
                else:
                    pass
    return HttpResponse(json.dumps(TaskIdList))


@login_required
def hosts_multi_filetrans(request):
    DiffPath = 'cmdfile'
    # 在26个英文字母中随机生成8个字母
    random_str = ''.join(random.sample(string.ascii_lowercase,8))
    # 取出最近执行的10个任务
    recent_tasks = models.TaskLog.objects.filter(user_id=request.user.id).order_by('-id')[:10]

    hobj =models.Hosts._meta.fields
    # 前端展示所需要的字段名
    # FieldName = [f.verbose_name for f in hobj if f.verbose_name not in ['enabled', 'is group','ID']]
    FieldName = ['主机IP', '主机名', 'idc', '系统', '端口', '备注信息', '创建时间']
    return render(request,'MaintainWeb/hosts_multi_files.html',{'login_user':request.user,
                                              'recent_tasks': recent_tasks,
                                              'random_str': random_str,
                                                'FieldName':FieldName,
                                              'active_node':'/hosts/multi/filetrans',
                                                                'DiffPath':DiffPath})


def get_uploaded_fileinfo(file_dic,upload_dir):
    for filename in os.listdir(upload_dir):
        abs_file = '%s/%s' % (upload_dir, filename)
        file_create_time = datetime.time.strftime("%Y-%m-%d %H:%M:%S",
                                                  datetime.time.gmtime(os.path.getctime(abs_file)))
        file_dic['files'][filename] = {'size': os.path.getsize(abs_file) / 1000,
                                           'ctime': file_create_time}


@login_required
@csrf_exempt
def multitask_file_upload(request):
    filename = request.FILES['filename']
    utils.handle_upload_file(request,filename)
    return HttpResponse(json.dumps({'text':'success'}))


@login_required
def delete_file(request,random_str):
    response = {}
    if request.method == "POST":
        upload_dir = "%s/task_data/tmp/%s" % (settings.FileUploadDir,random_str)
        filename = request.POST.get('filename')
        file_abs = "%s/%s" %(upload_dir,filename.strip())
        if os.path.isfile(file_abs):
            os.remove(file_abs)
            response['msg'] = "file '%s' got deleted " % filename
        else:
            response["error"] = "file '%s' does not exist on server"% filename
    else:
        response['error'] = "only supoort POST method..."
    return HttpResponse(json.dumps(response))


@login_required
def multitask_file(request):
    multi_task = host_mgr.MultiTask(request.POST.get('task_type'),request)
    task_result = multi_task.run()
    return  HttpResponse(task_result)

# 文件下载
@login_required
def file_download(request,task_id):

    file_path = "%s/%s/%s" %(settings.FileUploadDir,request.user.id,task_id)
    print(' file_path ######' ,file_path )
    return utils.send_zipfile(request, task_id,file_path)


# host主机修改处理函数
@login_required
def HostsChange(request):
    print('request.POST',request.POST)
    err_msg={'message':None,'status':None}
    ChangeHostsList=json.loads(request.POST.get('post_list'))

    for BindHostId in ChangeHostsList:
        if 'ip_addr' in BindHostId.get('data'):
            if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",BindHostId.get('data').get('ip_addr')):
                err_msg['message']=BindHostId.get('data').get('ip_addr')+' IP地址格式不正确请重新输入'
                err_msg['status']=response_code.RET.PARAMERR
                break
        elif 'port' in BindHostId.get('data'):
            if not re.match(r"^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$",BindHostId.get('data').get('prot')):
                err_msg['message'] =BindHostId.get('data').get('prot')+ ' 端口地址格式不正确请重新输入'
                err_msg['status'] = response_code.RET.PARAMERR
                break
        else:
            # 找到主机对象，进行更改

            HostObj = models.Hosts.objects.filter(bindhosts=BindHostId.get('id'))
            print('HostObj',HostObj,"BindHostId.get('data')",BindHostId.get('data'))
            HostObj.update(**BindHostId.get('data'))
            err_msg['status'] = response_code.RET.OK

    return HttpResponse(json.dumps(err_msg))

# 日志首页
@login_required
def SyetemLog(request):
    DiffPath='systemlog'
    UserId = request.user.id
    # 最近十条的执行记录
    recent_tasks = models.TaskLog.objects.filter(user_id=UserId).order_by('-id')[:10]
    hobj =models.Hosts._meta.fields
    # 前端展示所需要的字段名
    # FieldName = [f.verbose_name for f in hobj if f.verbose_name not in ['enabled', 'is group','ID']]
    #
    FieldName = ['主机IP','主机名','idc','系统','端口','备注信息','创建时间']
    return render(request,'MaintainWeb/system_log.html',{'login_user':request.user,
                                              #'host_groups':valid_hosts,
                                              'FieldName':FieldName,
                                              'recent_tasks': recent_tasks,
                                              'active_node':'/hosts/multi',
                                                          'DiffPath':DiffPath})

# 查看主机日志
def CheckHostSoftwareLog(request):
    print(request.POST)
    # bind_host_id, user_id, cmd, deploy = None
    selected_hosts=json.loads(request.POST.get('selected_hosts'))
    print('selected_hosts',selected_hosts)
    cmd= 'tail -f /var/log/messages'
    host_software_log.CheckLog(selected_hosts,request.user.id,cmd);
    return HttpResponse('OK')
    # host_software_log.CheckLog(bind_host_id,user_id,cmd,deploy)