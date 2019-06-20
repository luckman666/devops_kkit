简单介绍一下自己之前写的一个全栈项目，框架用的是django2.1版本

主要对paramiko模块，salstack的API二次开发。

核心组件包括：

MQ,mysql,websocket,redis,web控制台采用shellinabox。

为了部署方便我已经把所有组件做成了docker镜像，有时候可能会因为mq启动顺序问题导致不成功。项目具体部署过程如下：

git clone https://github.com/luckman666/devops_kkit.git

cd docker_deploy

docker-compose up -d

# 等待全部启动完毕如果访问出现502错误，那么执行下面语句

docker-compose restart kkit_app

如需试用saltstack功能，需要自行安装并配置相关api，然后修改本目录的settings.py配置即可。

该版核心功能如下：

1、	操作日志留存、审计、分析。

2、	动态分配临时账号，对服务器等资源进行临时授权。

3、	内部邮件系统。

4、	Ssh，saltstack，web界面三种方式的控制操控渠道。

5、	内部通信及沟通机制。

6、	容器管理（没开发完成）。

7、	物理机、虚拟机等底层资源日志分析及审计。

8、	定时任务。

9、	管理员控制面板。

有些内容没写全，因为要改写整个架构。

初始账号123@123.com 密码123

正在全新改写第三版，敬请期待！

也在抓紧录制这个项目的教学视频！

欢迎大家关注我个人的订阅号，会定期分享学习心得，相关案例信息!



![index1](https://github.com/luckman666/devops_kkit/blob/master/gzh.jpg)
管理员控制仪表板：
![index2](https://github.com/luckman666/devops_kkit/blob/master/image/1.jpg) 
系统账号临时登录授权（内部邮件系统发送账号密码和临时token）：
![index3](https://github.com/luckman666/devops_kkit/blob/master/image/2.jpg) 
动态图表监视任务情况：
开始
![index4](https://github.com/luckman666/devops_kkit/blob/master/image/3.jpg) 
结束：
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/4.jpg) 

日志系统可以查看主机系统日志，通过websocket反馈给页面，实现日志动态同步更新。但是我懒得弄了没写完。。。
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/5.jpg) 

批量命令及文件传输下载：
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/6.jpg) 
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/7.jpg) 
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/8.jpg) 
文件下载
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/9.jpg) 
saltstack相信大家不会陌生吧，我对这个实用工具也进行的集成：
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/10.jpg) 
saltstack相信大家不会陌生吧，我对这个实用工具也进行的集成：

批量执行shell脚本

![index5](https://github.com/luckman666/devops_kkit/blob/master/image/11.jpg) 

一个简单的CMD系统：

![index5](https://github.com/luckman666/devops_kkit/blob/master/image/12.jpg) 


简单的工单系统：


![index5](https://github.com/luckman666/devops_kkit/blob/master/image/13.jpg) 
报修工单列表：
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/14.jpg) 


编辑工单
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/15.jpg) 
下面的一些关于审计的模块没有来的及写。
![index5](https://github.com/luckman666/devops_kkit/blob/master/image/16.jpg) 



