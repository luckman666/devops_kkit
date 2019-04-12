from django.conf.urls import url,include
from kkitsalt import views
from MaintainWeb import ApiUrls
urlpatterns = [
    # 显示配置页面
    url(r'^config/$', views.SaltConfig, name='SaltConfig'),
    # key管理
    url(r'^keyaction/$', views.SaltAction, name='SaltKeyAction'),
    # 同步配置
    url(r'^syncminion/$', views.SyncMinion, name='SyncMinion'),
    # 查看主机配置
    url(r'^checkhostinfo/$', views.CheckHostInfo, name='CheckHostInfo'),
    #部署客户端
    url(r'^deployagent/$', views.DeployAgent, name='DeployAgent'),
    #脚本首页
    url(r'^saltscript/$', views.SaltScript, name='SaltScript'),
    # 执行脚本
    url(r'^executescript/$', views.ExecuteScript, name='ExecuteScript'),
    # job管理
    url(r'jobaction/$',views.JobAction, name='JobAction'),
    # job管理
    url(r'stopiob/$', views.StopJob, name='StopJob'),
]