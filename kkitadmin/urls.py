from django.conf.urls import url
from kkitadmin import views
# app_name = "kk"
urlpatterns = [
    url(r'^login/$', views.acc_login),
    url(r'^logout/$', views.acc_logout, name="kkitadmin_logout"),
    url(r'^(\w+)/(\w+)/$', views.table_obj_list, name="table_obj_list"),
    url(r'^(\w+)/(\w+)/(\d+)/change/$', views.table_obj_change, name="table_obj_change"),
    url(r'^(\w+)/(\w+)/add/$', views.table_obj_add, name="table_obj_add"),
    url(r'^(\w+)/(\w+)/(\d+)/delete/$', views.table_obj_delete, name="obj_delete"),
    url(r'^$', views.KkitIndex, name="app_index"),

]