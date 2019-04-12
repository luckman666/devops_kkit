from django.conf.urls import url,include
from MaintainWeb import views
from MaintainWeb import ApiUrls
urlpatterns = [
    # url(r'^hosts/change/$', views.HostsChange, name='hosts_change'),
    url(r'^hosts/$',views.hosts, name='host_list'),
    url(r'^hosts/multi/$',views.hosts_multi,name="batch_cmd_exec"),
    url(r'^hosts/multi/filetrans$',views.hosts_multi_filetrans,name="batch_file_transfer"),
    url(r'^systemlog/$', views.SyetemLog, name='SyetemLog'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^login/$', views.login, name='login'),
    url(r'^adm/$', views.adm, name='adm'),
    url(r'^$', views.dashboard, name="sales_dashboard"),
]