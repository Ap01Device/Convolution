import os
import binascii

from django.db import models
from qlive.payutils import generate_out_trade_no


class UserToken(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(verbose_name='Key', max_length=40, primary_key=True)
    user_id = models.IntegerField(verbose_name='用户ID', default=0, unique=True, blank=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = False
        verbose_name = "UserToken"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(UserToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class User(models.Model):
    '''
    用户基本信息
    '''
    user_id = models.IntegerField(verbose_name='本地ID', default=0, unique=True, blank=True)

    open_id = models.CharField(verbose_name='OpenID', max_length=128, db_index=True, blank=True)
    app_id = models.CharField(verbose_name='APPID', max_length=128, default='', blank=True)
    session_key = models.CharField(verbose_name='sessionKey', max_length=64, default='', blank=True)
    user_sig = models.CharField(verbose_name='IM_User_sign', max_length=512, default='', blank=True)
    user_sig_expired = models.DateTimeField(verbose_name='UserSig过期时间', null=True, blank=True)

    nickname = models.CharField(verbose_name='昵称', max_length=50, default='', blank=True)
    gender = models.SmallIntegerField(verbose_name='性别', default=1, blank=True, help_text="1:男,2:女")
    age = models.IntegerField(verbose_name='年龄', default=25, blank=True)
    face_url = models.URLField(verbose_name='头像', max_length=512, default='', blank=True)
    area = models.CharField(verbose_name='地区', max_length=8, default='', blank=True)
    declaration = models.CharField(verbose_name='相亲宣言', max_length=50, default='真心相亲', blank=True)

    gold = models.IntegerField(verbose_name='账户金币', default=0, blank=True)
    height = models.IntegerField(verbose_name='身高', default=180, blank=True)
    is_matchmaker = models.BooleanField(verbose_name='是否是红娘', default=False, blank=True)
    income = models.IntegerField(verbose_name='收益', default=0, blank=True)

    banned = models.SmallIntegerField(verbose_name="封号状态", default=0, blank=True, help_text="0:未封号，1：封号")
    last_login_time = models.DateTimeField(verbose_name='上次登录时间', null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        verbose_name = '用户基本信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}-{}".format(self.user_id, self.nickname)


class LiveBroadcastRoom(models.Model):
    '''
    直播间信息
    '''
    image = models.URLField(verbose_name='封面', max_length=512, default='', blank=True)
    group_id = models.CharField(verbose_name='IM群ID', max_length=16, default='', blank=True)
    is_live = models.BooleanField(verbose_name='是否在直播', default=False, blank=True, help_text='False:不在直播，True:直播中')
    start_time = models.DateTimeField(verbose_name='开播时间', null=True, blank=True)
    continuous_time = models.IntegerField(verbose_name='连续直播时间(秒)', default=0, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    play_url_owner = models.URLField(verbose_name='大主播播放地址', max_length=512, default='', blank=True)
    play_url_male = models.URLField(verbose_name='男嘉宾播放地址', max_length=512, default='', blank=True)
    play_url_female = models.URLField(verbose_name='女嘉宾播放地址', max_length=512, default='', blank=True)

    class Meta:
        verbose_name = '直播间信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.group_id


class User2Live(models.Model):
    '''
    用户与直播间关系
    '''
    user_id = models.IntegerField(verbose_name='用户ID', default=0, blank=True, db_index=True)
    live_id = models.IntegerField(verbose_name='直播间ID', default=0, blank=True, db_index=True)
    is_host = models.BooleanField(verbose_name='是否是主播', default=False, blank=True)
    state = models.SmallIntegerField(verbose_name='用户在直播间的状态', default=0, blank=True,
                                     help_text='0:不在直播间, 1:只观看, 2:申请上麦, 3:男上麦中，4:女上麦中')
    last_change = models.DateTimeField(verbose_name='上次修改时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '用户与直播间关系'
        verbose_name_plural = verbose_name
        unique_together = ['user_id', 'live_id']

    def __str__(self):
        return '%s-%s' % (self.user_id, self.live_id)


class Gift(models.Model):
    '''
    礼物
    '''
    name = models.CharField(verbose_name='礼物名称', max_length=16, default='', blank=True)
    image = models.URLField(verbose_name='礼物图片', max_length=512, default='', blank=True)
    gold = models.IntegerField(verbose_name='金币单价', default=0, blank=True)
    effect = models.URLField(verbose_name='特效图片', max_length=512, default='', blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '礼物'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class PayModel(models.Model):
    '''
    充值类型
    '''
    gold = models.IntegerField(verbose_name='金币数量', default=0, blank=True)
    price = models.FloatField(verbose_name='价格', default=0, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '充值类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}-{}".format(self.gold, self.price)


class Order(models.Model):
    '''
    订单
    '''
    order_id = models.CharField(verbose_name='订单ID', max_length=32, blank=True, primary_key=True)
    prepay_id = models.CharField(verbose_name='微信预支付标识', max_length=40, null=True, blank=True)
    cost = models.FloatField(verbose_name='金额', default=0, blank=True)
    gold = models.IntegerField(verbose_name='充值金币', default=0, blank=True)
    user_id = models.IntegerField(verbose_name='用户ID', default=0, blank=True, db_index=True)
    state = models.SmallIntegerField(verbose_name='支付状态', default=0, blank=True, help_text='{0:未支付, 1:已支付}')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "order_id-{}".format(self.order_id)


class Config(models.Model):
    '''
    公共配置
    '''
    itype = models.CharField(verbose_name='类型', max_length=50, null=False)
    ikey = models.CharField(verbose_name='配置名称', max_length=30, null=False)
    ival = models.CharField(verbose_name='配置值', max_length=512, null=False, default='')
    remark = models.CharField(verbose_name='备注', max_length=512, default='', blank='')
    ienable = models.SmallIntegerField(default=1)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s-%s' % (self.ikey, self.ival)


class Like(models.Model):
    '''
    点赞
    '''
    user_id = models.IntegerField(verbose_name='点赞人', default=0, blank=True)
    passive_user_id = models.IntegerField(verbose_name='被点赞人', default=0, blank=True)
    like_state = models.SmallIntegerField(verbose_name='点赞状态', default=1, blank=True, help_text='1:点赞, 0:取消点赞')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s-%s-%s' % (self.user_id, self.passive_user_id, self.like_state)
