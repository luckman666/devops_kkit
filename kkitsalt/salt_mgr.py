import json
import operator
from MaintainWeb import models
import urllib3
import ssl
import redis
import operator
import requests
import logging
from MaintainWeb import host_mgr
from kkit import settings
import time
try:
    import cookielib
except:
    import http.cookiejar as cookielib

# 使用urllib2请求https出错，做的设置
context = ssl._create_unverified_context()

# 使用requests请求https出现警告，做的设置
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


class SaltApi:
    """
    定义salt api接口的类
    初始化获得token
    """
    def __init__(self,url,saltmethod,request=None):
        self.url = url
        self.username = "saltapi"
        self.password = "saltapi"
        self.request=request
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
            "Content-type": "application/json"
        }
        self.params = {'client': 'local', 'fun': '', 'tgt': ''}

        self.login_url = settings.salt_api + "login"
        self.login_params = {'username': self.username, 'password': self.password, 'eauth': 'pam'}
        self.token = self.get_data(self.login_url, self.login_params)['token']
        self.headers['X-Auth-Token'] = self.token
        self.saltmethod=saltmethod

    # 执行获取数据
    def get_data(self, url, params):
        send_data = json.dumps(params)
        request = requests.post(url, data=send_data, headers=self.headers, verify=False)
        response = request.json()
        result = dict(response)

        return result['return'][0]

    # 同步命令
    def salt_command(self, tgt, method, arg=None):
        """远程执行命令，相当于salt 'client1' cmd.run 'free -m'"""
        if arg:
            params = {'client': 'local', 'fun': method, 'tgt': tgt, 'arg': arg}
        else:
            params = {'client': 'local', 'fun': method, 'tgt': tgt}

        result = self.get_data(self.url, params)

        return result
    # 异步命令
    def salt_async_command(self, tgt, method, arg=None):  # 异步执行salt命令，根据jid查看执行结果
        """远程异步执行命令"""
        if arg:
            params = {'client': 'local_async', 'fun': method, 'tgt': tgt, 'arg': arg}
        else:
            params = {'client': 'local_async', 'fun': method, 'tgt': tgt}
        jid = self.get_data(self.url, params)['jid']
        return jid

    # 本地查看秘钥
    def salt_master_command(self,method):  # 异步执行salt命令，根据jid查看执行结果

        params = {'client': 'wheel', 'fun': method}
        jid = self.get_data(self.url, params)['jid']
        # print('jid',jid)
        return jid

    # 查看job运行情况函数
    def runner_command(self, tgt, method,expr_form=None,arg=None):
        """远程执行命令，相当于salt 'client1' cmd.run 'free -m'"""
        #  'expr_form':expr_form 相当于-L
        if expr_form:
            params = {'client': 'local', 'fun': method, 'tgt': tgt, 'expr_form':expr_form}
        else:
            params = {'client': 'local', 'fun': method, 'tgt': tgt}
        # print ('命令参数: ', params)
        result = self.get_data(self.url, params)
        # print('get_jobdata',result)
        return result

    # job stop
    def stop_command(self, tgt, method, arg=None):
        """查看job"""
        # print('method',method,'tgt',tgt)
        if arg:
            params = {'client': 'local', 'fun': method, 'tgt': tgt,'arg':arg}
        else:
            params = {'client': 'local', 'fun': method, 'tgt': tgt}

        result = self.get_data(self.url, params)

        return result

    # key操作
    def salt_action_key(self, minion):  # 异步执行salt命令，根据jid查看执行结果

        params = {'client': 'wheel', 'fun': self.saltmethod,'match':minion}
        content = self.get_data(self.url, params)

        ReturnInfoDic = content['data']['return']
        if self.saltmethod=='key.delete':
            minions_preList, minions_List = self.salt_list_key()
            task_id,task_log_detail_obj_ids=SaltsfuncLog(self.request,ReturnInfoDic,self.saltmethod,minion,minions_List)
        else:
            task_id, task_log_detail_obj_ids = SaltsfuncLog(self.request, ReturnInfoDic, self.saltmethod)
        return ReturnInfoDic,task_id,task_log_detail_obj_ids

    # 查看都有哪些key
    def salt_list_key(self):  # 异步执行salt命令，根据jid查看执行结果

        params = {'client': 'wheel', 'fun': 'key.list_all'}
        content = self.get_data(self.url, params)

        minions_preList = content['data']['return']['minions_pre']

        # minions_rejectedList = content['data']['return']['minions_rejected']
        # minions_deniedList = content['data']['return']['minions_denied']
        minions_List = content['data']['return']['minions']
        # print('minions_List!!!!!!!!',minions_List)
        return minions_preList,minions_List

    def look_jid(self, jid):  # 根据异步执行命令返回的jid查看事件结果
        params = {'client': 'runner', 'fun': 'jobs.lookup_jid', 'jid': jid}
        result = self.get_data(self.url, params)
        # 同步主机配置设置
        if self.saltmethod =='grains.items':
            result=GrainsItemsInsertData(result)

        return result

    # 查看minion配置
    def salt_grains(self):  # 异步执行salt命令，根据jid查看执行结果
        params = {'client': 'local_async','tgt':'*','fun': self.saltmethod }
        try:
            content = self.get_data(self.url, params)
            return content['jid']
        except Exception as e:
            return 'false'

# 初始化写入日志
def SaltsfuncLog(request,exec_hosts,saltmethod,minion=None,minions_List=None):
    BindHostsObjLis = []
    if saltmethod=='key.accept':

        for hostname in exec_hosts['minions']:
            HostInfoObj=models.HostInfo.objects.get(hostname=hostname)
            Hosts = models.Hosts.objects.filter(hostinfo=HostInfoObj.id)
            BindHostsObj=models.BindHosts.objects.filter(host=Hosts[0].id)
            BindHostsObjLis.append(BindHostsObj[0])
        M = host_mgr.MultiTask('SaltsFuncWriteLog',request)
        content='服务器已经开始加入集群动作'
        task_expire_time='20'
        taskid ,task_log_detail_obj_ids= M.SaltsFuncWriteLog('saltstack',BindHostsObjLis,task_expire_time,content )
        return taskid,task_log_detail_obj_ids
    elif saltmethod=='key.delete':
        # print('minions_List',minions_List,'minion',minion)
        if minion not in minions_List:
            HostInfoObj=models.HostInfo.objects.get(hostname=minion)
            Hosts = models.Hosts.objects.filter(hostinfo=HostInfoObj.id)
            BindHostsObj=models.BindHosts.objects.filter(host=Hosts[0].id)
            BindHostsObjLis.append(BindHostsObj[0])
            # print('BindHostsObjLis', BindHostsObjLis, type(BindHostsObjLis),'Hosts ',Hosts,'HostInfoObj',HostInfoObj )
        M = host_mgr.MultiTask('SaltsFuncWriteLog',request)
        content= '主机名为： '+ minion + '服务器已经开始进行剥离集群动作'
        task_expire_time='20'
        # print('BindHostsObjLis',BindHostsObjLis,type(BindHostsObjLis))
        taskid ,task_log_detail_obj_ids= M.SaltsFuncWriteLog('saltstack',BindHostsObjLis,task_expire_time,content )
        return taskid,task_log_detail_obj_ids



# 同步配置插入数据库！
def GrainsItemsInsertData(result):
    # print('result',result)
    ResultList=[]
    for key, value in result.items():
        msg = {'status': None}
        dic = {}
        try:
            HostInfoObj =models.HostInfo.objects.get(minionname=key)
            dic['minionname'] = key
            dic['biosversion'] = value.get('biosversion')
            dic['cpu_model'] = value.get('cpu_model')
            dic['cpuarch'] = value.get('cpuarch')
            # dic['hostname'] = value.get('host')
            dic['hostname'] = key
            dic['kernelrelease'] = value.get('kernelrelease')
            dic['machine_id'] = value.get('machine_id')
            dic['master'] = value.get('master')
            dic['num_cpus'] = value.get('num_cpus')
            dic['osfinger'] = value.get('osfinger')
            dic['osrelease'] = value.get('osrelease')
            dic['productname'] = value.get('productname')
            dic['mem_total']= value.get("mem_total")
            print(value)
            try:
                models.HostInfo.objects.filter(id=HostInfoObj.id).update(**dic)
                msg['status'] = 'HostInfo.update成功'
                msg['minionname'] = key
                ResultList.append(msg)
            except Exception as e:
                logging.info(e)
                msg['status'] = 'HostInfo.update失败'
                msg['minionname'] = key
                ResultList.append(msg)
        except Exception as e:
            logging.info(e)
            hostobj = models.Hosts.objects.filter(hostname=key)
            dic['minionname'] = key
            dic['biosversion']=value.get('biosversion')
            dic['cpu_model']=value.get('cpu_model')
            dic['cpuarch']=value.get('cpuarch')
            # dic['hostname']=value.get('host')
            dic['hostname']=key
            dic['kernelrelease']=value.get('kernelrelease')
            dic['machine_id']=value.get('machine_id')
            dic['master']=value.get('master')
            dic['num_cpus']=value.get('num_cpus')
            dic['osfinger']=value.get('osfinger')
            dic['osrelease']=value.get('osrelease')
            dic['productname']=value.get('productname')
            dic['mem_total'] = value.get("mem_total")
            print(value)
            try:
                HostInfoObj=models.HostInfo.objects.create(**dic)
                hostobj.update(hostinfo=HostInfoObj)
                msg['status'] = 'HostInfo.add成功'
                msg['minionname'] = key
                ResultList.append(msg)
            except Exception as e:
                logging.info(e)
                msg['status'] = 'HostInfo.add失败'
                msg['minionname'] = key
                ResultList.append(msg)

    return ResultList


# 检查key完成情况
def CheckKeyActionResult(request,task_id,ReturnInfoDic=None,task_log_detail_obj_ids=None,minion=None,saltmethod=None,minions_preList=None):
    # print('ReturnInfoDic',ReturnInfoDic,'ReturnInfoDic,minions_preList',ReturnInfoDic,minions_preList)
    if ReturnInfoDic != None and ReturnInfoDic.get('minions') !=[] and operator.eq(ReturnInfoDic.get('minions'),minions_preList):
        count=0
        for houstname in ReturnInfoDic.get('minions'):
            print('bbbb')
            try:
                HostInfoobj=models.HostInfo.objects.filter(hostname=houstname)
                HostsObj=models.Hosts.objects.filter(hostinfo=HostInfoobj[0].id)
                HostsObj.update(minionstatus='Accepted')
                BindHostsObj = models.BindHosts.objects.filter(host=HostsObj)
                msg='主机名为 ： ' + houstname + ' 成功成为ip master ' + settings.salt_master_ip_addr + ' 的从属服务器，可以对其进行批量操作了！'
                res_status = 'success'
                TakeResultWrite(request, task_id, BindHostsObj,msg,res_status,count,task_log_detail_obj_ids)
            except Exception as e:
                print('cccc')
                msg = logging.error(e)
                HostInfoobj = models.HostInfo.objects.filter(hostname=houstname)
                HostsObj=models.Hosts.objects.filter(hostinfo=HostInfoobj[0].id)
                # HostsObj.update(minionstatus='Accepted')
                BindHostsObj = models.BindHosts.objects.filter(host=HostsObj)
                res_status = 'failed'
                TakeResultWrite(request, task_id, BindHostsObj, msg, res_status,count,task_log_detail_obj_ids)
            count += 1
    else:

        if saltmethod=='key.delete':
            try:
                HostInfoobj = models.HostInfo.objects.get(hostname=minion)
                HostsObj = models.Hosts.objects.get(hostinfo=HostInfoobj.id)
                HostsObj.minionstatus='Unaccepted'
                HostsObj.save()
                BindHostsObj = models.BindHosts.objects.get(host=HostsObj)
                msg = '主机名为 ： ' + minion + ' 成功剥离ip master ' + settings.salt_master_ip_addr + ' 无法通过saltstack模块对其进行操作！'
                res_status = 'success'

                TakeResultWrite(request=request, task_id=task_id, BindHostsObj=BindHostsObj, msg=str(msg), res_status=res_status)
            except Exception as e:

                msg = logging.error(e)
                HostInfoobj = models.HostInfo.objects.get(hostname=minion)
                HostsObj = models.Hosts.objects.get(hostinfo=HostInfoobj.id)

                BindHostsObj = models.BindHosts.objects.get(host=HostsObj)
                res_status = 'failed'
                TakeResultWrite(request, task_id, BindHostsObj, msg, res_status)

# 完成任务后状态插入数据库函数
def TakeResultWrite(task_id,BindHostsObj,msg,res_status,count=None,task_log_detail_obj_ids=None):

    # 全部许可的插入语句
    if count != None and task_log_detail_obj_ids != None:
        task_log_detail_obj_id=task_log_detail_obj_ids[count]
        log_obj = models.TaskLogDetail.objects.get(id=task_log_detail_obj_id)
        log_obj.event_log = msg
        log_obj.result= res_status
        log_obj.save()
        # return log_obj.id
    else:
        # key单独操作的语句
        log_obj = models.TaskLogDetail.objects.get(child_of_task_id=int(task_id), bind_host_id=BindHostsObj.id)
        log_obj.event_log = msg
        log_obj.result= res_status
        log_obj.save()
        # return log_obj.id
# 执行脚本函数
def ExecuteSaltScript(userid,salt_client,salt_method,ScriptName,taskid,task_log_detail_obj_ids,count):

    salt_params ='salt://base/'+str(userid)+'/'+ScriptName[0]
    salt1 = SaltApi(settings.salt_api, salt_method)
    RelDic = salt1.salt_command(salt_client, salt_method, salt_params)

    for key,values in RelDic.items():
        stderr=values.get('stderr','')
        stdout=values.get('stdout','')
        if stderr:
            res_status = 'failed'
        else:
            res_status = 'success'
        msg='主机名： '+ key +' 脚本执行反馈如下：' + stderr+stdout

        TakeResultWrite( task_id=taskid, BindHostsObj=salt_client, msg=str(msg),res_status=res_status,count=count,task_log_detail_obj_ids=task_log_detail_obj_ids)


# 执行脚本返回值检查函数
def InitScriptLog(request, BindHostsObjLisArg, ScriptName,expire_time):

    M = host_mgr.MultiTask('SaltsFuncWriteLog', request)
    content = '脚本名为： '+ ScriptName[0] + '开始执行'
    task_expire_time = expire_time
    taskid, task_log_detail_obj_ids = M.SaltsFuncWriteLog('saltstack', BindHostsObjLisArg, task_expire_time, content)
    return taskid ,task_log_detail_obj_ids

# 查看正在运行的job
def RunJob(salt_client,salt_method,expr_form):

    salt1 = SaltApi(settings.salt_api, salt_method)
    result = salt1.runner_command(salt_client,salt_method,expr_form)

    return result

# 停止job
def StopJob(salt_client,salt_method,jid):
    salt1 = SaltApi(settings.salt_api, salt_method)
    # lis=[]
    # for jid in jids:
    result = salt1.stop_command(salt_client,salt_method,jid)
    # lis.append(result)
        # TakeResultWrite( task_id=taskid, BindHostsObj=salt_client, msg=str(msg),res_status=res_status,count=count,task_log_detail_obj_ids=task_log_detail_obj_ids)

    return result


# 跟执行脚本嵌套使用的获取jid和pid(废弃)
def GetJidPidSalt(salt_client,task_log_detail_obj_ids,count):
    # time.sleep(2)
    # # 收集jid和pid等信息
    method = 'saltutil.running'
    expr_form = 'list'
    salt1 = SaltApi(settings.salt_api, method)
    result = salt1.runner_command(salt_client, method,expr_form)
    # 存到相应的表中
    for key, values in result.items():
        jid = values[0].get('jid')
        pid = values[0].get('pid')
        log_obj = models.TaskLogDetail.objects.get(id=task_log_detail_obj_ids[count])
        log_obj.jid = jid
        log_obj.pid = pid
        log_obj.save()

