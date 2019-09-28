from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, openId, password, **extra_fields):
        if not openId:
            raise ValueError('The given openId must be set')
        user = self.model(openId=openId, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, openId, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(openId, password, **extra_fields)

    def create_superuser(self, openId, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(openId, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    openId = models.CharField(verbose_name='openID', max_length=128, unique=True, db_index=True)
    nickName = models.CharField(verbose_name='微信昵称', max_length=128, default='')
    avatarUrl = models.URLField(verbose_name='头像', max_length=512, default='', blank=True)
    gender = models.IntegerField(verbose_name='性别', default=0)
    province = models.CharField(verbose_name='省份', max_length=24, default='', blank=True)
    city = models.CharField(verbose_name='城市', max_length=24, default='', blank=True)
    wallet = models.FloatField(verbose_name='余额', default=0.00)
    noticeFee = models.FloatField(verbose_name='通知的红包金额', default=0.00)

    unionId = models.CharField(verbose_name='UNIONID', max_length=128, default='', blank=True)
    appId = models.CharField(verbose_name='APPID', max_length=128, default='', blank=True)
    createTime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    USERNAME_FIELD = 'openId'
    objects = UserManager()

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickName


class FormId(models.Model):
    user = models.ForeignKey(User, related_name='formId', on_delete=models.CASCADE)
    formId = models.CharField(verbose_name='fomId', max_length=52)
    status = models.BooleanField(verbose_name='状态', default=True)

    expired = models.DateTimeField(verbose_name='过期时间', null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '用户FormId'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}-{}-{}'.format(self.user, self.formId, self.status)


class NoAuthUser(models.Model):
    openId = models.CharField(verbose_name='openID', max_length=128, db_index=True)
    appId = models.CharField(verbose_name='APPID', max_length=128, default='', blank=True)

    createTime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = 'NoAuth用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}'.format(self.openId)


class NoAuthFormId(models.Model):
    user = models.ForeignKey(NoAuthUser, on_delete=models.CASCADE)
    formId = models.CharField(verbose_name='fomId', max_length=52)
    expired = models.DateTimeField(verbose_name='过期时间', null=True, blank=True)

    class Meta:
        verbose_name = 'NoAuth用户FormId'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}'.format(self.user)


class Media(models.Model):
    appId = models.CharField(verbose_name='APPID', max_length=128)
    mediaType = models.CharField(verbose_name='类型', max_length=20)
    mediaVal = models.CharField(verbose_name='值', max_length=512)

    expired = models.DateTimeField(verbose_name='过期时间', null=True)

    class Meta:
        verbose_name = '媒体素材&TOKEN'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}'.format(self.appId)


class Config(models.Model):
    iapp = models.CharField(verbose_name='APPID', max_length=128)
    ikey = models.CharField(max_length=30)
    ival = models.CharField(max_length=128, default='')
    iremark = models.CharField(verbose_name='备注', max_length=128, default='', blank=True)
    ienable = models.SmallIntegerField(default=1)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}-{}'.format(self.ikey, self.ival)


class AppConfig(models.Model):
    appid = models.CharField(verbose_name='APPID', max_length=128, default='')
    title = models.CharField(verbose_name=u'名称', max_length=50, default='')
    descr = models.CharField(verbose_name=u'描述', max_length=128, default='')
    path = models.CharField(verbose_name=u'启动路径', max_length=100, default='')
    thumb = models.CharField(verbose_name=u'图标路径', max_length=256, default='')
    weight = models.IntegerField(verbose_name=u'权重', default=0, help_text=u'越大越靠前')

    ienable = models.BooleanField(verbose_name=u'是否启用', default=True)

    class Meta:
        verbose_name = u'小程序们'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s - %s' % (self.title, self.appid)


class TimeStampedModel(models.Model):
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
