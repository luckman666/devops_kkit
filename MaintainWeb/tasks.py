# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time,json
from MaintainWeb import utils



# 授权登录模块发送邮件功能
@shared_task(name='sendemail')
def SendEmail(TaskInfoList, Taskid,task_log_detail_obj_ids):
    # print(Taskid,TaskInfoList, task_log_detail_obj_ids)
    result = utils.AccreditMail(TaskInfoList, Taskid, task_log_detail_obj_ids)
    return result
