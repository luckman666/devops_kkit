from django.test import TestCase
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.shortcuts import render,redirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt

from MaintainWeb.models import *
from django.shortcuts import render, redirect, HttpResponse
from django.forms import Form
from django.forms import fields
from django.forms import widgets
import json
import time
import datetime



@csrf_exempt
def lis(request):
    data = [
        {'id': 1, 'title': 'aaa', 'content': 'lalalalalla', 'makedown': '## lalalalla'},
        {'id': 2, 'title': 'bbb', 'content': 'mmmmmmmmmmmmmmmm', 'makedown': '## mmmmmm'},
        {'id': 3, 'title': 'ccc', 'content': 'ggggggggggggg', 'makedown': '## gggggg'},
        {'id': 4, 'title': 'dddd', 'content': 'rrrrrrrrrrrrrr', 'makedown': '## rrrr'},
    ]
    if (request.method == 'GET'):
        print ('aaaaaaaaaaaaaaaaa')
        return HttpResponse(json.dumps(data))
    else:
        dic = json.loads(request.POST.get('data'))
        dic['id'] = len(data)+1
        data.append(dic)
        print ('a',data)
        return  HttpResponse(json.dumps(data))


