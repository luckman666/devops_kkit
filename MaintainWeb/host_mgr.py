import json,subprocess
from MaintainWeb import models
import paramiko,time,os,signal
import multiprocessing
from kkit import settings
from django.db import transaction
from backend.utils import json_date_handler



def valid_host_groups_back(request): #deprecated
    user_groups = models.UserProfile.objects.get(user_id= request.user.id).user_groups.select_related()
    host_groups = []

    for u_group in user_groups:
        host_groups += u_group.host_groups.select_related()
    host_groups = list(set(host_groups))
    host_group_dic = {-1:[]}
    selected_g_id  = None
    active_g_item = None
    for h_group in host_groups:
        hosts = models.BindHosts.objects.filter(host_group_id= h_group.id)

        host_nums = len(set( [i.host.ip_addr for i in hosts ] ))
        hosts = list(hosts) # convert hosts from models object to list,frontpage needs to loop it
        selected_group =request.GET.get('selected_group')
        if selected_group:
            if selected_group.isdigit():
                if h_group.id == int(selected_group):#got selected
                    host_group_dic[h_group.id] = [h_group, host_nums,hosts]
                    selected_g_id = h_group.id
                else:
                    host_group_dic[h_group.id] = [h_group, host_nums]
            elif selected_group == '-1': #recent visited hosts
                selected_g_id = -1
                host_group_dic[h_group.id] = [h_group, host_nums]
        else:
            host_group_dic[h_group.id] = [h_group, host_nums]



    return [ host_group_dic, selected_g_id]


def valid_host_list(request): #deprecated
    user_groups = models.UserProfile.objects.get(user_id= request.user.id).user_groups.select_related()
    host_groups = []

    for u_group in user_groups:
        host_groups += u_group.host_groups.select_related()
    host_groups = list(set(host_groups))
    host_group_dic = {-1:[]}

    for h_group in host_groups:
        hosts = models.BindHosts.objects.filter(host_group_id= h_group.id)
        host_nums = len(set( [i.host.ip_addr for i in hosts ] ))
        hosts = list(hosts) # convert hosts from models object to list,frontpage needs to loop it

        host_group_dic[h_group.id] = [h_group, host_nums,hosts]

    return host_group_dic

# 执行多条命令的方法
class MultiTask(object):
    def __init__(self,task_type,request_ins,parameter=None):
        # 初始化请求实例对象
        self.request = request_ins
        # run_cmd类型
        self.task_type = task_type
        self.parameter = parameter


    # 分析命令
    def run(self):
        return self.parse_args()
    def parse_args(self):
        #print '==>parse_args:', self.request.POST
        task_func = getattr(self,self.task_type)

        return task_func()
    # 停止任务选项
    def terminate_task(self):
        task_id = self.request.POST.get('task_id')
        # 如果不为整数那么就停止该脚本执行
        assert task_id.isdigit()
        task_obj = models.TaskLog.objects.get(id=int(task_id))
        res_msg = ''
        try:
            os.killpg(task_obj.task_pid,signal.SIGTERM)
            res_msg = 'Task %s has terminated!' % task_id
        except OSError as e:
            res_msg = "Error happened when tries to terminate task %s , err_msg[%s]" % (task_id,str(e))
        if (res_msg.split(' ')[0]=='Task'):
            task_log_detail_obj = models.TaskLogDetail.objects.filter(child_of_task_id=task_id).update(event_log=res_msg,result='delete')
        return res_msg

    # 其他组件写入日志函数
    def SaltsFuncWriteLog(self,task_type, exec_hosts , task_expire_time, cmd):

        task_obj,task_log_detail_obj_ids=self.create_task_log(task_type, exec_hosts , task_expire_time, cmd, random_str=None)

        return task_obj.id ,task_log_detail_obj_ids

    def run_cmd(self,cmd=None, task_expire_time=None, exec_hosts=None, random_str=None,deploy=None):
        # 获取cmd命令内容
        # 部署agent用的口deploy=='SaltAgent'
        if deploy:
            cmd=cmd
            task_expire_time=task_expire_time
            exec_hosts=exec_hosts
            random_str=random_str
            # print('cmd!!!!', cmd,deploy, type(cmd))
        else:
            cmd = self.request.POST.get("cmd")
            # 取出id值
            host_ids =[i for i in json.loads(self.request.POST.get("selected_hosts"))]
            # 过期时间
            task_expire_time = self.request.POST.get("expire_time")
            # 执行主机
            exec_hosts = models.BindHosts.objects.filter(id__in=host_ids)

            random_str = self.request.POST.get('local_file_path')
            # print('cmd!!!!',cmd,type(cmd))
        task_obj= self.create_task_log('cmd',exec_hosts,task_expire_time,cmd,random_str)

        #'-task_type', 'cmd', '-task_id', '15', '-expire', '30', '-task', 'ifconfig', '-uid', '1']

        # 执行django以外的脚本，subprocess.Popen是多线程执行命令
        p = subprocess.Popen(['python3',
                             settings.MultiTaskScript,
                             '-task_type','cmd',
                             '-expire',task_expire_time,
                             '-uid',str(self.request.user.id),
                             '-task',cmd,
                             '-task_id', str(task_obj.id),
                              '-deploy',str(deploy)
                             ],
                             preexec_fn=os.setsid)

        task_obj.task_pid = p.pid
        task_obj.save()
        # 返回任务id
        return task_obj.id

    # 记录任务日志
    @transaction.atomic
    def create_task_log(self,task_type,hosts,expire_time,content,random_str=None,note=None):
        task_log_obj = models.TaskLog(
            task_type = task_type,
            user = self.request.user,
            cmd = content,
            files_dir = random_str,
            expire_time = int(expire_time),
            note = note
        )
        task_log_obj.save()

        # print('task_type,hosts,expire_time,content',task_type,hosts,expire_time,content)
        # 添加多对多关系中间表数据
        task_log_obj.hosts.add(*hosts)
        #初始化详细日志记录
        if (task_type == 'Accredit') or (task_type == 'saltstack') :
            task_log_detail_obj_ids=[]
            for h in hosts:

                task_log_detail_obj = models.TaskLogDetail(
                    child_of_task_id = task_log_obj.id,
                    bind_host_id = h.id,
                    event_log = '',
                    result = 'unknown'
                )
                task_log_detail_obj.save()
                task_log_detail_obj_ids.append(task_log_detail_obj.id)

            return task_log_obj, task_log_detail_obj_ids
        else:
            for h in hosts:
                task_log_detail_obj = models.TaskLogDetail(
                    child_of_task_id = task_log_obj.id,
                    bind_host_id = h.id,
                    event_log = '',
                    result = 'unknown'
                )
                task_log_detail_obj.save()
            return task_log_obj

    def file_get(self):
        return self.file_send()

    def file_send(self):
        params = json.loads(self.request.POST.get('params'))
        host_ids =[i for i in params.get("selected_hosts")]
        task_expire_time = params.get("expire_time")
        random_str = params.get('local_file_path')
        exec_hosts = models.BindHosts.objects.filter(id__in=host_ids)
        task_type = self.request.POST.get('task_type')
        local_file_list = params.get('local_file_list')
        if task_type == 'file_send':
            content = "send local files %s to remote path [%s]" %(local_file_list,params.get('remote_file_path'))

        else:
            local_file_list = 'not_required' #set this var just for passing verification
            content = "download remote file [%s]" % params.get('remote_file_path')


        task_obj= self.create_task_log(task_type,exec_hosts,task_expire_time,content,random_str)
        if task_type == 'file_get':
            local_path = "%s/%s/%s" % (
            # settings.BASE_DIR, settings.FileUploadDir, self.request.user.id, task_obj.id)
                 settings.FileUploadDir, self.request.user.id, task_obj.id)

            try:
                os.mkdir(local_path)
            except OSError as e:
                pass

        # preexec_fn=os.setsid 成立一个进程组，所有子进程都挂载这个父进程下面。可以对其进行kill或者创建
        p = subprocess.Popen(['python3',
                             settings.MultiTaskScript,
                             '-task_type',task_type,
                             '-expire',task_expire_time,
                             '-uid',str(self.request.user.id) ,
                             '-local',' '.join(local_file_list) ,
                             '-remote',params.get('remote_file_path') ,
                             '-task_id', str(task_obj.id)
                             ],preexec_fn=os.setsid)

        task_obj.task_pid = p.pid
        task_obj.save()
        return task_obj.id

    # token发放
    def Accredit(self):
        DateDic = self.parameter
        # print('229!!',DateDic)
        task_obj,task_log_detail_obj_ids = self.create_task_log(**DateDic)
        return task_obj.id,task_log_detail_obj_ids

    # 获取多任务结果
    def get_task_result(self,detail=True):
        '''get multi run task result'''
        task_id = self.request.GET.get('task_id')
        log_dic ={
            'detail':{}
        }
        # 任务表查询
        task_obj = models.TaskLog.objects.get(id=int(task_id))
        # 日志详细表查询
        task_detail_obj_list = models.TaskLogDetail.objects.filter(child_of_task_id=task_obj.id)
        # print('task_detail_obj_list',task_detail_obj_list)
        log_dic['summary']={
            'id':task_obj.id ,
            'start_time': task_obj.start_time,
            'end_time': task_obj.end_time,
            'task_type': task_obj.task_type,
            'host_num': task_obj.hosts.select_related().count(),
            'finished_num': task_detail_obj_list.filter(result='success').count(),
            'failed_num': task_detail_obj_list.filter(result='failed').count(),
            'unknown_num': task_detail_obj_list.filter(result='unknown').count(),
            'content': task_obj.cmd,
            'expire_time':task_obj.expire_time
        }

        if detail:
            con =0
            for log in task_detail_obj_list:
                # 将结果加入到log_dic字典中key为detail,值为log.id：一个字典
                log_dic['detail'][log.id] = {
                    'date': log.date ,
                    'bind_host_id':log.bind_host_id,
                    'host_id': log.bind_host.host.id,
                    # 'hostname': log.bind_host.host.hostinfo.hostname,
                    'hostname':'MakeHostname',
                    'ip_addr': log.bind_host.host.ip_addr,
                    'username': log.bind_host.host_user.username,
                    'system' : log.bind_host.host.system_type,
                    'event_log': log.event_log,
                    'result': log.result,
                    'note': log.note
                }
                con+=1
                # print('log####',log_dic)
        return json.dumps(log_dic,default=json_date_handler)


