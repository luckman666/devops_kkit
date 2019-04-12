from django.conf.urls import include, url
from MaintainWeb import views

urlpatterns = [

    url(r'multitask/hostcounts/$', views.HostCounts,name='multitask_HostCounts'),
    # 批量命令执行api
    url(r'multitask/cmd/$', views.multitask_cmd,name='multitask_cmd'),
    # 前端get请求执行任务结果的api
    # url(r'multitask/file_upload/(\w+)/$', views.multitask_file_upload, name='file_upload'),
    url(r'multitask/file_upload/$', views.multitask_file_upload,name='file_upload'),
    url(r'multitask/file_upload/(\w+)/delete/$', views.delete_file,name='delete_file'),
    url(r'multitask/file/$', views.multitask_file,name='multitask_file'),
    # 多任务执行和获取结果
    url(r'multitask/res/$', views.multitask_res),
    url(r'multitask/action/$', views.multitask_task_action,name='multitask_action'),
    url(r'multitask/file_download/(\d+)/$', views.file_download, name='file_download_url'),
    url(r'dashboard_summary/$', views.dashboard_summary, name='dashboard_summary'),
    url(r'audit/user_counts/$', views.user_login_counts, name='user_login_counts'),
    url(r'dashboard_detail/$', views.dashboard_detail, name='dashboard_detail'),
    # 废弃
    # url(r'token/gen/$', views.token_gen, name='token_gen'),
    # 授权接口
    url(r'hosts/accredit/$', views.accredit, name='accredit'),
    # 主机也修改数据传递接口
    url(r'hostschange/$', views.HostsChange, name='hosts_change'),
    # 获取最近10条 任务完成情况的接口
    url(r'request_tasks_id/$', views.RequestTasksId, name='RequestTasksId'),
    # 获取未完成的任务接口
    url(r'request_run_tasks_id/$', views.RequestRuningTasksId, name='RequestRuningTasksId'),
    # 查看日志
    url(r'check_host_software_log/$', views.CheckHostSoftwareLog, name='CheckHostSoftwareLog'),
]