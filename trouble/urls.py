from django.conf.urls import url,include
from trouble import views
from trouble import tests


urlpatterns = [
    # 一般用户： 提交报障单,查看，修改（未处理），评分（处理完成，未评分）
    url(r'^lis/$', tests.lis),
    # url(r'^addstu/$', tests.addstu),



    url(r'^trouble-list/$',views.trouble_list, name='TroubleList'),
    url(r'^trouble-create/$', views.trouble_create, name='TroubleCreate'),
    url(r'^trouble-edit-(\d+).html$', views.trouble_edit, name='TroubleEdit'),
    url(r'^trouble-delete-(\d+).html$', views.trouble_delete, name='TroubleDelete'),

    # 处理者的处理情况
    url(r'^trouble-kill-list.html$', views.trouble_kill_list, name='TroubleKillList'),
    url(r'^trouble-kill-(\d+).html$', views.trouble_kill, name='TroubleKill'),
    # 模板的管理
    url(r'^trouble-create-model-(?P<nid>\d+).html$', views.backend_trouble_create_model, name='TroubleCreateModel'),
]