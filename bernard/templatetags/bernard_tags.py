#_*_coding:utf-8_*_

import datetime
import re,os,time,json
from django import template

from django.utils.safestring import mark_safe#,mark_for_escaping
from  django.urls import reverse as url_reverse
from kkit import settings
from bernard import models
register = template.Library()


@register.simple_tag
def get_plan_last_runlog(plan_obj):

    return plan_obj.schedulelog_set.last()


@register.simple_tag
def get_plan_crontab(plan_obj):

    #lowlowlow
    try:
        task_obj = models.PeriodicTask.objects.get(args=json.dumps([plan_obj.id]))

        return task_obj
    except Exception as e:
        return None


@register.simple_tag
def  get_plan_stages_in_order(plan_obj):
    return  plan_obj.stage_set.order_by('order')


@register.simple_tag
def get_stages_jobs_in_order(stage):
    return stage.job_set.order_by('order')