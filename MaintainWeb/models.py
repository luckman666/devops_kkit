from django.db import models
# User主要是为了采用django的验证方式
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from MaintainWeb import auth
import datetime
import django

# 机房表
class IDC(models.Model):
    idc_name_choices = (
        ('1', '北京'),
        ('2', '天津'),
    )
    name = models.CharField(choices=idc_name_choices,max_length=64, unique=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'IDC'
        verbose_name_plural = 'IDC'

# 部门表
class Department(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'

# 服务器详细信息表
class HostInfo(models.Model):
    minionname = models.CharField(max_length=64, unique=True, null=True, verbose_name="minion名")
    biosversion = models.CharField(max_length=32, verbose_name="bios版本", null=True)
    cpu_model = models.CharField(max_length=128, verbose_name="cpu型号", null=True)
    cpuarch = models.CharField(max_length=32, verbose_name="系统位码", null=True)
    hostname = models.CharField(max_length=64, verbose_name="主机名", null=True)
    kernelrelease = models.CharField(max_length=64, verbose_name="内核版本", null=True)
    machine_id = models.CharField(max_length=64, verbose_name="machine_id", null=True)
    master = models.CharField(max_length=64, verbose_name="master名称", null=True)
    num_cpus = models.IntegerField(verbose_name="cpu数量", null=True)
    mem_total = models.IntegerField(verbose_name="内存", null=True)
    osfinger = models.CharField(max_length=64, verbose_name="系统版本", null=True)
    osrelease = models.CharField(max_length=64, verbose_name="系统发行版本号", null=True)
    productname = models.CharField(max_length=64, verbose_name="产品名称", null=True)

    def __str__(self):
        return '%s(%s)' % (self.minionname, self.hostname)

# 主机地址表
class Hosts(models.Model):
    # hostname = models.CharField(max_length=64, unique=True, verbose_name="主机名")
    ip_addr = models.GenericIPAddressField(unique=True, verbose_name="主机ip")
    # 是否已经被分到组里
    is_group = models.BooleanField(default=False)
    #在调整
    system_type_choices = (
        ('windows', 'Windows'),
        ('linux', 'Linux/Unix')
    )
    idc = models.ForeignKey('IDC',on_delete=models.CASCADE,verbose_name="IDC")
    system_type = models.CharField(choices=system_type_choices, max_length=32, default='linux',verbose_name="系统")
    port = models.IntegerField(default=22,verbose_name="端口")
    # 是否可以远程访问
    enabled = models.BooleanField(default=True, help_text='主机若不想被用户访问可以去掉此选项')
    # host_users = models.ForeignKey('HostUsers')
    # host_groups = models.ForeignKey('HostGroups')
    # 是否为saltstack的minion
    salt_status_choices = (
        ('Unaccepted', 'Unaccepted'),
        ('Rejected', 'Rejected'),
        ('Accepted', 'Accepted'),
    )
    minionstatus=models.CharField(choices=salt_status_choices,max_length=32,default='Unaccepted',verbose_name="状态")
    # 备注
    memo = models.CharField(max_length=128, blank=True, null=True,verbose_name="备注信息")
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="创建时间")
    hostinfo=models.ForeignKey('HostInfo',on_delete=models.CASCADE,verbose_name="主机详情", null=True)
    def __str__(self):
        return '%s' % (self.ip_addr)

    # class Meta:
    #     verbose_name = '主机'
    #     verbose_name_plural = '主机'
        # verbose_name = ''

# 远程访问主机的用户
class HostUsers(models.Model):
    # 访问的形式
    auth_method_choices = (('ssh-password', "SSH/ Password"), ('ssh-key', "SSH/KEY"))
    #
    auth_method = models.CharField(choices=auth_method_choices, max_length=16,
                                   help_text='如果选择SSH/KEY，请确保你的私钥文件已在settings.py中指定')
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64, blank=True, null=True, help_text='如果auth_method选择的是SSH/KEY,那此处不需要填写..')
    memo = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return '%s(%s)' % (self.username, self.password)

    class Meta:
        verbose_name = '远程用户'
        verbose_name_plural = '远程用户'
        unique_together = ('auth_method', 'password', 'username')

# 远程主机绑定远程用户的第三张表
class BindHosts(models.Model):
    # 关联主机的id
    host = models.ForeignKey('Hosts',on_delete=models.CASCADE,)
    # 关联远程用户的id
    host_user = models.ForeignKey('HostUsers', verbose_name="远程用户",on_delete=models.CASCADE,)
    # 是否激活选项？
    enabled = models.BooleanField(default=True)
    def __str__(self):
        return '%s:%s' % (self.host.ip_addr, self.host_user.username)

    class Meta:
        # 唯一索引
        unique_together = ("host", "host_user")
        verbose_name = '主机与远程用户绑定'
        verbose_name_plural = '主机远程与用户绑定'


# 主机组
class HostGroups(models.Model):
    # 组名
    name = models.CharField(max_length=64, unique=True)
    # 备注
    memo = models.CharField(max_length=128, blank=True, null=True)
    # 组跟绑定好的主机继续关联
    bind_hosts = models.ManyToManyField('BindHosts', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '主机组'
        verbose_name_plural = '主机组'


class UserProfile(auth.AbstractBaseUser, auth.PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    # 是否激活用户
    is_active = models.BooleanField(default=True)
    # 是不是管理员
    is_admin = models.BooleanField(default=False)
    # 有没有最基本的权限
    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    name = models.CharField(max_length=32)

    department = models.ForeignKey('Department', verbose_name='部门', blank=True, null=True,on_delete=models.CASCADE,)
    host_groups = models.ManyToManyField('HostGroups', verbose_name='授权主机组', blank=True)
    bind_hosts = models.ManyToManyField('BindHosts', verbose_name='授权主机', blank=True)

    memo = models.TextField('备注', blank=True, null=True, default=None)
    date_joined = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    # 有效开始时间，默认当前时间
    valid_begin_time = models.DateTimeField(default=django.utils.timezone.now, help_text="yyyy-mm-dd HH:MM:SS")
    # 有限期结束时间
    valid_end_time = models.DateTimeField(blank=True, null=True, help_text="yyyy-mm-dd HH:MM:SS")
    # 用户名字段使用邮件
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['name','token','department','tel','mobile','memo']
    # 必须填写的是邮件
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):  # __str__ on Python 2
        return self.email

    # 自定义权限
    def has_perms(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True
    # 试图权限标签
    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    # 超级用户属性
    @property
    def is_superuser(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = u"用户信息"

    def __str__(self):
        return self.name
    # 自定义的验证表，所以需要重新写这个表以及其验证和管理的表单。还有前端用来显示的表单
    # 对userprofile对进行管理和验证时的form表单
    objects = auth.UserManager()

    class Meta:
        verbose_name = 'kkit账户'
        verbose_name_plural = 'kkit账户'
        # 所设计的权限列表
        permissions = (
            ('web_access_dashboard', '可以访问 审计主页'),
            ('web_batch_cmd_exec', '可以访问 批量命令执行页面'),
            ('web_batch_batch_file_transfer', '可以访问 批量文件分发页面'),
            ('web_config_center', '可以访问 堡垒机配置中心'),
            ('web_config_items', '可以访问 堡垒机各配置列表'),
            ('web_invoke_admin_action', '可以进行admin action执行动作'),
            ('web_table_change_page', '可以访问 堡垒机各配置项修改页'),
            ('web_table_change', '可以修改 堡垒机各配置项'),
        )


class Session(models.Model):
    '''生成用户操作session id '''
    # 关联用户
    user = models.ForeignKey('UserProfile',on_delete=models.CASCADE,)
    # 关联绑定好的主机
    bind_host = models.ForeignKey('BindHosts',on_delete=models.CASCADE,)
    tag = models.CharField(max_length=128, default='n/a')
    closed = models.BooleanField(default=False)
    cmd_count = models.IntegerField(default=0)  # 命令执行数量
    stay_time = models.IntegerField(default=0, help_text="每次刷新自动计算停留时间", verbose_name="停留时长(seconds)")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '<id:%s user:%s bind_host:%s>' % (self.id, self.user.email, self.bind_host.host)

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'


class SessionTrack(models.Model):  # 没用了的表

    date = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)

    def __str__(self):
        return '%s' % self.id


# Deprecated
class AuditLog(models.Model):
    session = models.ForeignKey(SessionTrack,on_delete=models.CASCADE,)
    user = models.ForeignKey('UserProfile',on_delete=models.CASCADE,)
    host = models.ForeignKey('BindHosts',on_delete=models.CASCADE,)
    action_choices = (
        (0, 'CMD'),
        (1, 'Login'),
        (2, 'Logout'),
        (3, 'GetFile'),
        (4, 'SendFile'),
        (5, 'exception'),
        (6,'Accredit'),
    )
    action_type = models.IntegerField(choices=action_choices, default=0)
    cmd = models.TextField(blank=True, null=True)
    memo = models.CharField(max_length=128, blank=True, null=True)
    date = models.DateTimeField()

    def __str__(self):
        return '%s-->%s@%s:%s' % (self.user.email, self.host.host_user.username, self.host.host.ip_addr, self.cmd)

    class Meta:
        verbose_name = '审计日志old'
        verbose_name_plural = '审计日志old'


class TaskLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    task_type_choices = (('cmd', "CMD"), ('file_send', "批量发送文件"), ('file_get', "批量下载文件"),('Accredit',"token授予"),('saltstack',"saltstack操作"))
    task_type = models.CharField(choices=task_type_choices, max_length=50)
    files_dir = models.CharField("文件上传临时目录", blank=True, null=True, max_length=32)
    user = models.ForeignKey('UserProfile',on_delete=models.CASCADE,)
    hosts = models.ManyToManyField('BindHosts')
    cmd = models.TextField()
    expire_time = models.IntegerField(default=30)
    task_pid = models.IntegerField(default=0)
    note = models.CharField(max_length=100, blank=True, null=True)
    jid = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return "taskid:%s cmd:%s" % (self.id, self.cmd)

    class Meta:
        verbose_name = '批量任务'
        verbose_name_plural = '批量任务'


class TaskLogDetail(models.Model):
    child_of_task = models.ForeignKey('TaskLog',on_delete=models.CASCADE,)
    bind_host = models.ForeignKey('BindHosts',on_delete=models.CASCADE,)
    date = models.DateTimeField(auto_now_add=True)  # finished date
    event_log = models.TextField()
    result_choices = (('success', 'Success'), ('failed', 'Failed'), ('unknown', 'Unknown'),('delete', 'Delete'))
    result = models.CharField(choices=result_choices, max_length=30, default='unknown')
    note = models.CharField(max_length=100, blank=True)
    pid = models.CharField(max_length=100, blank=True, null=True)
    jid = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return "child of:%s result:%s" % (self.child_of_task.id, self.result)

    class Meta:
        verbose_name = '批量任务日志'
        verbose_name_plural = '批量任务日志'

class Token(models.Model):
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE,)
    host = models.ForeignKey(BindHosts,on_delete=models.CASCADE,)
    token = models.CharField(max_length=64)
    date = models.DateTimeField(default=django.utils.timezone.now)
    expire = models.IntegerField(default=600)

    def __str__(self):
        return '%s : %s' % (self.host.host.ip_addr, self.token)

# 保障单的表
class Trouble(models.Model):
    title = models.CharField(max_length=32)
    detail = models.TextField()
    user = models.ForeignKey(UserProfile,related_name='u',on_delete=models.CASCADE,)
    # ctime = models.CharField(max_length=32) # 1491527007.452494
    ctime = models.DateTimeField()
    status_choices = (
        (1,'未处理'),
        (2,'处理中'),
        (3,'已处理'),
    )
    status = models.IntegerField(choices=status_choices,default=1)
    # 处理者
    processer = models.ForeignKey(UserProfile,related_name='p',null=True,blank=True,on_delete=models.CASCADE,)
    # 解决方案
    solution = models.TextField(null=True)
    ptime = models.DateTimeField(null=True)
    pj_choices = (
        (1, '不满意'),
        (2, '一般'),
        (3, '活很好'),
    )
    # 评分
    pj = models.IntegerField(choices=pj_choices,null=True,default=2)



