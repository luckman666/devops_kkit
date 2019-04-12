
from kkitadmin.admin_base import BaseKkitAdmin

class AdminSite(object):
    def __init__(self):
        self.enabled_admins = {}



    def register(self,model_class,admin_class=None):
        """注册admin表"""
        # model_class是模块对象，admin_class是用户自定义的过滤器类名名称
        # print("register",model_class,admin_class)
        # _meta.app_label可以通过是模块对象获取app的名字
        # model_class._meta.model_name通过是模块对象获取获取模块名
        app_name = model_class._meta.app_label
        model_name = model_class._meta.model_name
        # 如果用户没有做特殊设置过滤条件
        if not admin_class: #为了避免多个model共享同一个BaseKingAdmin内存对象
            # 就用一个空的类生成一个空的对象
            admin_class = BaseKkitAdmin()
        else:
            # 如果有特殊设置，那么就使用原有用户自定义好的类（过滤用的）
            admin_class = admin_class()

        admin_class.model = model_class #将用户自定义注册好的模块对象付给admin_class.model

        # 如果新字典里面没有这个app命名的key
        if app_name not in self.enabled_admins:
            # 那么就新建个app的key值为空字典
            self.enabled_admins[app_name] = {}
        #  如果有特殊的设置，则将模块名称为key，相对应的模块对象为velue为值插入到相应的模块中
        # {app名：{表名：表对象}}
        # sites. {'SalesCrm': {'customerinfo': <SalesCrm.kkitadmin.CustomerAdmin object at 0x0000000004297128>}}
        # print('admin_class***',admin_class)
        self.enabled_admins[app_name][model_name] = admin_class

site = AdminSite()