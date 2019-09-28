from django.contrib import admin
from qlive.models import Config, PayModel, Gift


# Register your models here.
@admin.register(Config)
class QLiveConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'itype', 'ikey', 'ival', 'remark', 'ienable')


@admin.register(PayModel)
class QLivePayModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'gold', 'price')


@admin.register(Gift)
class QLiveGiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image', 'gold', 'effect')
