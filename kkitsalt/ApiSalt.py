from django.conf.urls import include, url
from MaintainWeb import views

urlpatterns = [

    url(r'script/action/$', views.HostCounts,name='script_action/')

]