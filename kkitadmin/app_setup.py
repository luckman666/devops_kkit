from django import conf
# 将所有注册在django下的app下面的kkitadmin导入。使其用户在该业务模块下配置的kkitadmin文件得以运行生效
def kkitadmin_auto_discover():
    for app_name in conf.settings.INSTALLED_APPS:
        try:
            mod = __import__('%s.kkitadmin' % app_name)
            #print(mod.kingadmin)
        except ImportError :
            pass