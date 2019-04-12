import time
import paramiko
import select
now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
now_day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
# link_server_cmd可行

# -*- coding: utf-8 -*-
import json
import traceback
import paramiko,logging
from kkit import settings
import django
django.setup()
from MaintainWeb import models
from django.db import connection
import sys,time,os
import multiprocessing

def CheckLog(bind_host_id,user_id,cmd,deploy=None):

    bind_host = models.BindHosts.objects.get(id=bind_host_id)

    s = paramiko.SSHClient()
    s.load_system_host_keys()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if bind_host.host_user.auth_method == 'ssh-password':
            s.connect(bind_host.host.ip_addr,
                      int(bind_host.host.port),
                      bind_host.host_user.username,
                      bind_host.host_user.password,
                      timeout=5)
        else:#rsa_key

            key = paramiko.RSAKey.from_private_key_file(settings.RSA_PRIVATE_KEY_FILE)
            s.connect(bind_host.host.ip_addr,
                      int(bind_host.host.port),
                      bind_host.host_user.username,
                      pkey=key,
                      timeout=5)
        # 查看日志
        link_server_client(s,cmd,user_id,bind_host.host.ip_addr)

    except Exception as e:
    #except ValueError as e:
        print('-----------  IP:%s -------------' %(bind_host.host.ip_addr))
        print('\033[31;1mError:%s\033[0m' % e)
        # print(traceback.print_exc())




def link_server_client(client,cmd,userid,ipaddr):
    # 进行连接
    # 开启channel 管道
    transport = client.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    # 执行命令nohup.log.2017-12-30
    # tail = 'tail -f /var/log/messages'
    # tail = 'docker logs -f mysql'
    # tail=cmd
    #将命令传入管道中
    channel.exec_command(cmd)
    while True:
        #判断退出的准备状态
        if channel.exit_status_ready():
            break
        try:
            # 通过socket进行读取日志，个人理解，linux相当于客户端，我本地相当于服务端请求获取数据（此处若有理解错误，望请指出。。谢谢）
            rl, wl, el = select.select([channel], [], [])
            if len(rl) > 0:
                recv = channel.recv(1024)
                # 此处将获取的数据解码成gbk的存入本地日志
                print(recv.decode('utf-8', 'ignore'))
                timename=time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
                upload_dir = '%s/%s' % (settings.FileUploadDir, userid)
                print('upload_dir',upload_dir,'tail(' +ipaddr+'-'+timename + ').log')
                text_save(recv.decode('utf-8', 'ignore'), upload_dir,'tail(' +ipaddr+'-'+timename + ').log')
        #键盘终端异常
        except KeyboardInterrupt:
            print("Caught control-C")
            channel.send("\x03")  # 发送 ctrl+c
            channel.close()
    client.close()

# 文件存储
def text_save(content, upload_dir,filename):
    # Try to save a list variable in txt file.

    file = open('%s/%s' % (upload_dir, filename), 'a')
    for i in content:
        file.write(i)
    file.close()




