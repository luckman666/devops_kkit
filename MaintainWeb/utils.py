from MaintainWeb import models
from django.db.models import Count,Sum
import django,time,random,json
from django.contrib.sessions.models import Session
import os, tempfile, zipfile,time
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from kkit import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from MaintainWeb import host_mgr

# 获取所有登录的用户
def get_all_logged_in_users():
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    sessions = Session.objects.filter(expire_date__gte=django.utils.timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return models.UserProfile.objects.filter(id__in=uid_list)


# 算出未分组主机
def undistributed_host(request):
    # 空列表
    DistributedHostList=[]
    # 查出所有组对象
    GroupList = models.HostGroups.objects.all()
    for group in GroupList:
        # 遍历出所有组对象对应的服务器主机
        group_host_list = group.bind_hosts.all()
        # 组成新的列表
        for h in list(group_host_list):
            DistributedHostList.append(h.id)
    # 这里是已经分完组的了，拿出新列表长度也就是数目
    distributed_host_count = len(DistributedHostList)
    # 查出所有主机的数目
    TopHost = models.Hosts.objects.all()
    HostCount = TopHost.count()
    # print('TopHost',list(TopHost))
    # 减去，剩下的就是了
    undistributed_host_count = HostCount - distributed_host_count
    # 遍历所有主机，和已经有组的主机列表对比，得出的值就是没有组的
    UndistributedHost = set(i for i in list(TopHost) if i.id not in DistributedHostList)

    return undistributed_host_count,UndistributedHost

    # cursor = connection.cursor()
    # # 时间格式化date_format转换成字符串，再分组排序
    # cursor.execute( """SELECT DATE_FORMAT(create_time,"%%Y-%%m") as ctime,count(nid) as num  from repository_article WHERE blog_id= %s group by DATE_FORMAT(create_time,"%%Y-%%m") """,[blog.nid,])
    # # 获取所有结果
    # date_list = cursor.fetchall()


def recent_accssed_hosts(request):
    # 得到14天前的时间
    days_before_14 = django.utils.timezone.now() +django.utils.timezone.timedelta(days=-14)
    # 查看日志表最近两周的操作，按时间排序（待优化）
    recent_logins = models.AuditLog.objects.filter(date__gt = days_before_14,user_id=request.user.id,action_type=1).order_by('date')
    # 如果去对远程主机的重复操作。得到其唯一的远程主机id集合
    unique_bindhost_ids = set([i[0] for i in recent_logins.values_list('host_id')])
    recent_login_hosts = []
    # 建立新列表，将去重过的主机id插入到新的集合中，然后再去重返回给前端
    for h_id in unique_bindhost_ids:
        recent_login_hosts.append(recent_logins.filter(host_id=h_id).latest('date'))

    return  set(recent_login_hosts)


def dashboard_summary(request):
    data_dic = {
        'user_login_statistics' :[],
        'recent_active_users':[],
        'recent_active_users_cmd_count':[],
        'summary':{}
    }
    days_before_30 = django.utils.timezone.now() +django.utils.timezone.timedelta(days=-30)
    #data_dic['user_login_statistics'] = list(models.AuditLog.objects.filter(action_type=1).extra({"login_date":"date(date)"}).values_list('login_date').annotate(count=Count('pk')))
    data_dic['user_login_statistics'] = list(models.Session.objects.filter(date__gt=days_before_30).extra({'login_date':'date(date)'}).values_list('login_date').annotate(count=Count('pk')))
    days_before_7 = django.utils.timezone.now() +django.utils.timezone.timedelta(days=-7)
    #recent_active_users= models.Session.objects.all()[0:10].values('user','user__name','cmd_count').annotate(Count('user'))
    recent_active_users= models.Session.objects.all()[0:10].values("user",'user__name').annotate(Sum('cmd_count'),Count('id'))
    recent_active_users_cmd_count= models.AuditLog.objects.filter(date__gt = days_before_7,action_type=0).values('user','user__name').annotate(Count('cmd'))
    data_dic['recent_active_users'] = list(recent_active_users)
    data_dic['recent_active_users_cmd_count'] = list(recent_active_users_cmd_count)
    data_dic['summary']['total_servers'] = models.Hosts.objects.count()
    data_dic['summary']['total_users'] = models.UserProfile.objects.count()
    data_dic['summary']['current_logging_users'] = get_all_logged_in_users().count()

    #current_connection servers
    current_connected_hosts = models.Session.objects.filter(closed=0).count()

    #current_connected_hosts = login_times - logout_times
    data_dic['summary']['current_connected_hosts'] = current_connected_hosts


    return  data_dic


# 生成临时令牌
class Token(object):
    def __init__(self,request):
        self.request = request
        self.token_type = request.POST.get('token_type')
        self.token = {'token':None}
    def generate(self):
        # 获取token类型
        func = getattr(self,self.token_type)
        return func()
    def host_token(self):

        TaskInfoList = []
        BindhostObjlist = []
        TaskDic = {}
        # 获取服务器主机id
        host_ids = [i for i in json.loads(self.request.POST.get("selected_hosts"))]
        UserIdList = [i for i in json.loads(self.request.POST.get("UserIdList"))]
        TokenExpireTime = self.request.POST.get('TokenExpireTime')
        # 找到主机对象
        for userid in UserIdList:
            for hostid in host_ids:
                objList = []
                host_obj = models.BindHosts.objects.get(id=int(hostid))
                UserObj = models.UserProfile.objects.get(id=int(userid))
            # 根据主机id和用户id找到最新的token对象
                latest_token_obj = models.Token.objects.filter(host_id = int(hostid),user_id=int(userid)).last()
                # print('!!!!!!!!!!!!host_obj ',host_obj ,'hostid',hostid)
                token_gen_flag = False
            # 如果有,需要检查是否过期
                if latest_token_obj:
                    # time.struct_time(tm_year=2018, tm_mon=12, tm_mday=6, tm_hour=10, tm_min=28, tm_sec=2, tm_wday=3, tm_yday=340, tm_isdst=0)
                    # timetuple()会被时间分成9个数值的元组对象
                    # mktime变成秒数表示的时间1544063282.0
                    token_gen_time_stamp = time.mktime(latest_token_obj.date.timetuple())
                    # 当前时间秒数
                    current_time = time.mktime(django.utils.timezone.now().timetuple() )
                    # 如果当前时间减去token的存活时间，大于token的300秒
                    if current_time - token_gen_time_stamp >latest_token_obj.expire:#token expired
                        token_gen_flag = True

                else:
                    token_gen_flag = True
                # 如果超时就新算个给他
                if token_gen_flag:
                    # 生成六位随机数
                    token = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba1234567890',6))
                    # 将相关信息存进数据库中
                    models.Token.objects.create(
                        user = UserObj,
                        host = host_obj,
                        token = token,
                        expire= (int(TokenExpireTime) * 60),
                    )
                else:
                    # 如果时间没超过，则返回最后那个token值给前端
                    token = latest_token_obj.token

                #task_log写入任务启动阶段

                # BindhostObjlist.append(host_obj)
                objList.append(UserObj.email)
                objList.append(UserObj.name)
                objList.append(token)
                # objList.append(host_obj.host.hostinfo.hostname)
                objList.append('TempMakeHostname')
                objList.append(host_obj.host.ip_addr)
                if (objList in TaskInfoList):
                    pass
                else:
                    BindhostObjlist.append(host_obj)
                    TaskInfoList.append(objList)
        taskmeg= ' 执行授权登录生成临时令牌以及发送邮件！！'
        TaskDic['task_type']='Accredit'
        TaskDic['hosts'] = BindhostObjlist
        TaskDic['expire_time'] = TokenExpireTime
        TaskDic['content']=str(taskmeg)
        # print('TaskDic',TaskDic)
        m = host_mgr.MultiTask('Accredit', self.request,parameter=TaskDic)
        TaskId,task_log_detail_obj_ids = m.run()
        # task_log_detail_obj_ids 详细日志行号数组
        # 写入完毕

        return TaskId,TaskInfoList,task_log_detail_obj_ids


#    授权之后发送邮件
def AccreditMail(TaskInfoList,Taskid,task_log_detail_obj_ids ):

    TaskInfoList=json.loads(TaskInfoList)

    result=['TaskInfoList',TaskInfoList]
    count = 0
    for host in TaskInfoList:
        TempDic={}
        usermail = host[0]
        username = host[1]
        token = host[2]
        hostname = host[3]
        ip_addr = host[4]



        subject, form_email, to = 'kkit服务器登录授权通知邮件!', settings.EMAIL_HOST_USER, usermail
        text_content ='<p> 您好！ '+ str( username )+' : </p> 系统管理员已经授权了您对主机名：'+ str( hostname) +' &nbsp&nbsp IP地址： '+ str(ip_addr )+ '  的登录请求. <p>点击下面地址并输入账号密码及临时令牌即可进行相应的操作：</p>' \
                                       '<p>用户名：'+ str( settings.SHELLINABOX.get('username') )+'  &nbsp&nbsp密码： '+ str( settings.SHELLINABOX.get('password'))+'&nbsp&nbsp 临时令牌：' + str( token ) + '</p>'
        html_content = "<p>" + str(text_content) + "</p>"+ '<b>登录连接：</b> <a href=\"https://'  + str(settings.SHELLINABOX.get('host')) + ':' + str(settings.SHELLINABOX.get('port')) + '\"  rel=\"external nofollow\">点击登录 </a>'
        msg = EmailMultiAlternatives(subject, str(text_content), form_email, [to])
        msg.attach_alternative(str(html_content), 'text/html')
        msg.send()
        log_obj = models.TaskLogDetail.objects.get(id=task_log_detail_obj_ids[count])
        log_obj.event_log = str(html_content)
        log_obj.result= 'success'
        log_obj.save()
        TempDic['hostinfo'] =host
        TempDic['Taskid'] = Taskid
        TempDic['text_content']=text_content
        result.append(TempDic)
        count += 1
    return result


# 已经分组的主机对象
def multitask_GroupHostCounts(request):
    GroupHostdic={}
    # 找到所有组对象
    GroupsObj = models.HostGroups.objects.all()
    # 按字典分出组名：数字
    for group in GroupsObj:
        GroupHost=group.bind_hosts.all()
        GroupHostdic[group.name] =GroupHost.count()
    return GroupHostdic


# 给多条命令饼状图返回分组数据的
def multitask_HostCounts(request):

    HostCounts = {}
    # 未分组的
    ungrouped_count,ungrouped_obj = undistributed_host(request)
    # 得到以分组的主机字典对象 {'测试1': 1, '测试2': 2}
    grouped_dic = multitask_GroupHostCounts(request)
    HostCounts['未分类主机']=ungrouped_count
    HostCounts.update(grouped_dic)
    # print('HostMerged',HostCounts)
    return HostCounts

def handle_upload_file(request,file_obj):
    # upload_dir = '%s/%s/%s' %(settings.BASE_DIR,settings.FileUploadDir,request.user.id)
    upload_dir = '%s/%s' % (settings.FileUploadDir, request.user.id)
    if not os.path.isdir(upload_dir):
        os.mkdir(upload_dir)
    with open('%s/%s' %(upload_dir,file_obj.name),'wb') as destination :
        for chunk in file_obj.chunks():
            destination.write(chunk)

def send_zipfile(request,task_id,file_path):
    """
    Create a ZIP file on disk and transmit it in chunks of 8KB,
    without loading the whole file into memory. A similar approach can
    be used for large dynamic PDF files.
    """

    zip_file_name = 'task_id_%s_files' % task_id
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    file_list = os.listdir(file_path)
    for filename in file_list:
        archive.write('%s/%s' %(file_path,filename))
    archive.close()
    data = temp.tell()
    temp.seek(0)
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % zip_file_name
    response['Content-Length'] = data

    return response




