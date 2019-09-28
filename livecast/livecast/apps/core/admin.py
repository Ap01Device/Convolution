from django.contrib import admin
from django.utils.html import format_html

from core.models import User, FormId, Config, Media, NoAuthFormId, NoAuthUser, AppConfig
from core import constants as core_constants

from rest_framework.authtoken.models import Token
from djcelery.models import (
    TaskState,
    WorkerState,
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
)

admin.site.unregister([
    Token,
    TaskState,
    WorkerState,
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
])


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fieldsets = ((None, {
        'fields': (
            'openId',
            'nickName',
            'avatarUrl',
            'gender',
            'city',
            'wallet',
            'noticeFee',
            'unionId',
            'appId',
        )
    }),)

    list_display = ('id', 'alias_avatar', 'nickName', 'alias_appId', 'createTime',
                    'wallet')
    search_fields = ('nickName',)

    def alias_appId(self, obj):
        appId = core_constants.WEIXINAPP.get(obj.appId, '')
        if appId:
            return appId.get('name')
        else:
            return ''

    def alias_avatar(self, obj):
        return format_html('<img src="{}" width=25px heith=25px>', obj.avatarUrl)

    alias_avatar.short_description = '头像'
    alias_appId.short_description = '所属小程序'


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'iapp', 'ikey', 'ival', 'iremark')


@admin.register(FormId)
class FormIdAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'formId', 'expired')
    search_fields = ('user__nickName',)


@admin.register(NoAuthUser)
class NoAuthUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'openId', 'appId', 'createTime')
    search_fields = ('openId',)


@admin.register(NoAuthFormId)
class NoAuthFormIdAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'formId', 'expired')
    search_fields = ('user__openId',)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'appId', 'mediaType', 'mediaVal', 'expired')

#
# @admin.register(AppConfig)
# class AppConfigAdmin(admin.ModelAdmin):
#     list_display = ('appid', 'title', 'descr', 'path', 'thumb')
