#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#==============================================================================
#     FileName: alert_util.py
#         Desc: 钉钉机器人通知相关
#      License: GPL
#       Author: Steve Lemuel
#        Email: wlemuel@hotmail.com
#      Version: 0.0.1
#   LastChange: 2019-06-28 14:58:13
#    CreatedAt: 2019-06-28 14:58:03
#==============================================================================
"""
# https://open-doc.dingtalk.com/microapp/serverapi2/qf2nxq

import requests

from django.conf import settings

IS_DEV = getattr(settings, "IS_DEV", True)
HOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token={}"
ACCESS_TOKEN_PROD = "182635c266c503c11315a7be9f6c9af6a2598e6b4383ed82d680d93d3ad50a12"
ACCESS_TOKEN_TEST = "24dca01214de61c293834859ecdb40d672717c4dedaa4a486916d2c76cf04474"


def send_alert(content):
    if IS_DEV:
        ALERT_URL = HOOK_URL.format(ACCESS_TOKEN_TEST)
    else:
        ALERT_URL = HOOK_URL.format(ACCESS_TOKEN_PROD)

    if content == "":
        return

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'msgtype': 'text',
        'text': {
            "content": content
        }
    }

    try:
        requests.post(ALERT_URL, json=data, headers=headers)
    except Exception as e:
        pass


def send_alert_format(title, content):
    send_alert("[{}] - {}".format(title, content))


if __name__ == '__main__':
    # send_alert("it is a test message")
    send_alert("中文字符测试&%$#@")
    send_alert_format("测试", "测试内容")
