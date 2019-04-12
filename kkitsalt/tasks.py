# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time,json
from kkitsalt import salt_mgr



# salt执行脚本
@shared_task(name='saltscript')
def ExecuteScriptTasks(userid, salt_client, salt_method, ScriptName,taskid,task_log_detail_obj_ids,count):
    salt_mgr.ExecuteSaltScript(userid, salt_client=salt_client, salt_method=salt_method, ScriptName=ScriptName,taskid=taskid,task_log_detail_obj_ids=task_log_detail_obj_ids,count=count)
    # return result

@shared_task(name='GetJidPid')
def GetJidPidTasks(salt_client,task_log_detail_obj_ids,count):
    # time.sleep(2)
    salt_mgr.GetJidPidSalt(salt_client,task_log_detail_obj_ids,count)
