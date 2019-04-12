
from django.db import models

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,Group,PermissionsMixin
)

import django
# 在管理用户时使用的表单
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )
        # 该方法直接将密码转化成了密文
        user.set_password(password)
        # 保存用户名及密码
        user.save(using=self._db)
        return user
    # 创建超级用户的时候使用的表单
    def create_superuser(self, email, name ,password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(email,
            password=password,
            name=name,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


