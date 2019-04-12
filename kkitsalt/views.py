from django.shortcuts import render,HttpResponseRedirect,HttpResponse,redirect
from django.contrib.auth.decorators import login_required
from MaintainWeb import host_mgr
from django.shortcuts import render
from celery import signature
from celery import chain
import time
from django.urls import reverse
from kkitsalt.salt_mgr import SaltApi
from utils.DeploySaltMinion import SaltMinionShellScript
from MaintainWeb import models
from MaintainWeb import utils
from kkit import settings
from kkitsalt import salt_mgr
from kkitsalt import tasks
from utils.response_code import RET
import json

import logging
@login_required
def SaltConfig(request):
    DiffPath = 'saltconfig'

    # 获取用户组id
    FieldName=['主机ip','主机名','当前状态','接受','拒绝','删除']
    selected_g_id = request.GET.get('selected_group')
    if selected_g_id:
        # 检查selected_g_id的字符串是不是只包含数字
        if selected_g_id.isdigit():
            selected_g_id = int(selected_g_id)
    UserEmail = models.UserProfile.objects.all()
    recent_logins = utils.recent_accssed_hosts(request)
    # 未分组的服务器总数和服务器对象
    UndistributedHostCount, UndistributedHost = utils.undistributed_host(request)
    return render(request, 'MaintainWeb/salt_config.html', {'login_user':request.user,
                                                      'DiffPath':DiffPath,
                                                      'FieldName':FieldName,
                                                      'UserEmail':list(UserEmail),
                                         'selected_g_id': selected_g_id,
                                        'active_node':"/hosts/?selected_group=-1",
                                        'recent_logins':recent_logins,  #去重后用户最近14天登录的主机id集合
                                        'webssh':settings.SHELLINABOX,
                                                            'undistributed_host_count': UndistributedHostCount,
                                                            'UndistributedHost':UndistributedHost})

# 单个，多个key，动作,添加，删除，拒绝接口
@login_required
def SaltAction(request):

    single = request.POST.get('single')
    if single =='True':
        kdate= json.loads(request.POST.get('jdata'))
        saltmethod = kdate.get('saltmethod')
        # BinHostId=kdate['id']
        minion = kdate['hostname']
        salt1 = salt_mgr.SaltApi(settings.salt_api,saltmethod,request)
        # minions_preList,minions_List=salt1.salt_list_key()
        ReturnInfoDic, task_id, task_log_detail_obj_ids = salt1.salt_action_key(minion)

        salt_mgr.CheckKeyActionResult(request=request, task_id=task_id, minion=minion,saltmethod=saltmethod)
        return HttpResponse(task_id)
    else:
        # 全部接收key函数
        dic = {}
        saltmethod = request.POST.get('saltmethod')
        # print('saltmethod',saltmethod)
        salt1 = salt_mgr.SaltApi(settings.salt_api,saltmethod,request)
        minions_preList,minions_List=salt1.salt_list_key()
        if minions_preList != []:
            ReturnInfoDic, task_id, task_log_detail_obj_ids=salt1.salt_action_key(minions_preList)
            salt_mgr.CheckKeyActionResult(request=request,ReturnInfoDic=ReturnInfoDic,task_id=task_id,task_log_detail_obj_ids=task_log_detail_obj_ids,minions_preList=minions_preList)
            return HttpResponse(task_id)
        else:
            dic['msg']='目前没有可以添加的主机！！请检查部署agent是否成功？'
            dic['status']='error'
            return HttpResponse(json.dumps(dic))


# 同步配置信息
@login_required
def SyncMinion(request):
    saltmethod = request.POST.get('jdata')

    salt1=salt_mgr.SaltApi(settings.salt_api, saltmethod)
    jid=salt1.salt_grains()
    if jid=='false':
        return HttpResponse(json.dumps(jid))
    else:
        result = salt1.look_jid(jid)
        return HttpResponse(json.dumps(result))

# 查看多个服务器配置
@login_required
def CheckHostInfo(request):

    FieldName=["minion名","处理器","系统内核","内存(M)","machine_id","cpu数量","系统版本","系统版本","产品名称"]

    return render(request, 'MaintainWeb/salt_hosts_info.html', {'FieldName':FieldName})

# 部署saltstack客户端
@login_required
def DeployAgent(request):
    # print(request.POST)
    task_type='run_cmd'
    cmd = SaltMinionShellScript()
    # 取出id值
    host_ids = [i.get('id') for i in json.loads(request.POST.get("jdata"))]
    # 过期时间
    task_expire_time = '30'
    # 执行主机
    exec_hosts = models.BindHosts.objects.filter(id__in=host_ids)
    random_str = None

    deploy ='SaltAgent'
    M=host_mgr.MultiTask(task_type,request)
    task_id=M.run_cmd(cmd,task_expire_time,exec_hosts,random_str,deploy)
    if task_id:
        return HttpResponse(task_id)
    else:
        return HttpResponse("TaskCreatingError")
#    salt脚本页面
@login_required
def SaltScript(request):
    DiffPath = 'saltscript'

    UserId = request.user.id
    # 最近十条的执行记录
    recent_tasks = models.TaskLog.objects.filter(user_id=UserId).order_by('-id')[:10]
    hobj =models.Hosts._meta.fields
    # 前端展示所需要的字段名
    FieldName = ['主机IP','主机名','idc','系统','端口','备注信息','创建时间']
    return render(request,'MaintainWeb/salt_execute_script.html',{'login_user':request.user,
                                              #'host_groups':valid_hosts,
                                              'FieldName':FieldName,
                                              'recent_tasks': recent_tasks,
                                              'active_node':'/hosts/multi',
                                                          'DiffPath':DiffPath})

# 执行脚本
@login_required
def ExecuteScript(request):

    salt_method = request.POST.get('task_type')
    # print('salt_method',salt_method)
    data= json.loads(request.POST.get('params'))
    salt_client=data['selected_hosts']
    ScriptName=data['local_file_list']
    expire_time = data['expire_time']

    # 查出所有BindHostsObjLis对象
    BindHostsObjLis=[]
    for BinHoustId in salt_client:
        BindHostsObj = models.BindHosts.objects.get(id=BinHoustId)
        BindHostsObjLis.append(BindHostsObj)
    #     初始化日志
    taskid, task_log_detail_obj_ids = salt_mgr.InitScriptLog(request=request, BindHostsObjLisArg=BindHostsObjLis, ScriptName=ScriptName,expire_time=expire_time)
    # print(taskid, task_log_detail_obj_ids)
    # 记循环次数，来找tasktaillog日志行号
    count=0
    for host_name in BindHostsObjLis:
        # 执行脚本
        try:
            tasks.ExecuteScriptTasks.apply_async(args=[request.user.id, host_name.host.hostinfo.minionname, salt_method, ScriptName,taskid,task_log_detail_obj_ids,count])

            # salt_mgr.GetJidPidSalt(host_name.host.hostinfo.minionname, task_log_detail_obj_ids,count)
            count += 1
        except Exception as e:
            logging.info(e)
            count += 1
    return HttpResponse(taskid)

# 查看正在运行中的job
@login_required
def JobAction(request):
    dic={}
    salt_method='saltutil.running'
    BindHostslist=[request.user.bind_hosts.select_related()]
    HostList=[BindHost.host.ip_addr for BindHost in BindHostslist[0]]
    # 带参数 salt -L 的意思
    expr_form='list'
    result=salt_mgr.RunJob(HostList,salt_method,expr_form)
    # 没有运行就不传值回去，要不报错
    for key,value in result.items():
        if value:
            dic[key]=value

        else:
            pass
    if dic:

        return HttpResponse(json.dumps(dic))
    else:
        dic['status'] = RET.THIRDERR
        return HttpResponse(json.dumps(dic))
# 停止job
@login_required
def StopJob(request):
    dic={}
    TmpLis=[]
    salt_method='saltutil.term_job'
    jids=json.loads(request.POST.get('jids'))
    print('jids',jids)
    for item in jids:
        print('item',item)
        jid=item.get('id','')
        salt_client=item.get('salt_client','')
        try:
            lis=salt_mgr.StopJob(salt_client,salt_method,jid)
            print('lislislislis',lis)
            RulInfo=lis.get(salt_client,'')
            print('RulInfo',RulInfo)
            if RulInfo:
                dic['msg']='服务器：' + salt_client + '  停止job反馈信息： ' + RulInfo
                dic['status'] = RET.OK
                TmpLis.append(dic)
            else:
                dic['msg'] = 'job停止失败！可能job已经运行完毕！'
                dic['status'] = RET.THIRDERR
                TmpLis.append(dic)
        except Exception as e:
            logging.error(e)
            dic['msg'] = e
            dic['status'] = RET.THIRDERR
            TmpLis.append(dic)
    print('TmpLis',TmpLis)
    return HttpResponse(json.dumps(TmpLis))

