# -*- coding: utf-8 -*-
# @Author  : itswcg
# @File    : payutils.py
# @Time    : 19-4-12 下午4:07
# @Blog    : https://blog.itswcg.com
# @github  : https://github.com/itswcg

import time
import logging
from django.conf import settings
from .pywxpay import WXPay, WXPayUtil, WXPayConstants

logger = logging.getLogger(__name__)

WEIXINAPP_APPID = getattr(settings, 'WEIXINAPP_APPID', '')
WEIXINAPP_MCHID = getattr(settings, 'WEIXINAPP_MCHID', '')
WEIXINAPP_KEY = getattr(settings, 'WEIXINAPP_KEY', '')
WEIXINAPP_CERT_PEM = getattr(settings, 'WEIXINAPP_CERT_PEM_PATH', '')
WEIXINAPP_KEY_PEM = getattr(settings, 'WEIXINAPP_KEY_PEM_PATH', '')

IS_DEV = getattr(settings, "IS_DEV", True)
if IS_DEV:
    WEIXINAPP_NOTIFY_URL_TEMPLATE = 'https://%s/wx/api/qlive/pay_notify/'
else:
    WEIXINAPP_NOTIFY_URL_TEMPLATE = 'https://%s/wx/api/qlive/pay_notify/'


def get_wx_pay(appid):
    return WXPay(
        app_id=appid,
        mch_id=WEIXINAPP_MCHID,
        key=WEIXINAPP_KEY,
        cert_pem_path=WEIXINAPP_CERT_PEM,
        key_pem_path=WEIXINAPP_KEY_PEM,
        timeout=6000)


def generate_out_trade_no():
    """
    生成订单号
    :return: 订单号
    """
    dateStr = time.strftime('%Y%m%d%H%M%S', time.localtime())[2:]
    timeStamp = str(int(time.perf_counter() * 10)) + str(int(time.perf_counter() * 100))
    return dateStr + timeStamp


def wx_dict2xml(data):
    """dict转xml"""
    return WXPayUtil.dict2xml(data)


def wx_lxml2dict(xml):
    """xml转dict"""
    return WXPayUtil.lxml2dict(xml)


def wx_notify_url():
    if IS_DEV:
        return WEIXINAPP_NOTIFY_URL_TEMPLATE % "test.daqinjia.cn"
    else:
        return WEIXINAPP_NOTIFY_URL_TEMPLATE % "qlive.wxapp.daqinjia.cn"


def wx_is_success(status):
    return status == WXPayConstants.SUCCESS


def wx_notify_check(data):
    if data['mch_id'] != WEIXINAPP_MCHID:
        return False
    return True


def wx_unifieorder(appid, openid, out_trade_no, money, body, spbill_create_ip='192.168.2.34'):
    """
    微信统一下单
    """
    request_dict = dict(
        device_info='WEB',
        body=body,
        openid=openid,
        out_trade_no=out_trade_no,
        total_fee=int(money * 100),
        fee_type='CNY',
        notify_url=wx_notify_url(),
        spbill_create_ip=spbill_create_ip,
        trade_type='JSAPI')

    return get_wx_pay(appid).unifiedorder(request_dict)


def wx_withdraw(appid, openid, out_trade_no, money, body, spbill_create_ip='139.224.212.27'):
    request_dict = {
        "partner_trade_no": out_trade_no,
        "openid": openid,
        "check_name": "NO_CHECK",  # 校验真名
        "amount": int(money * 100),  # 提现金额，单位为分
        "desc": body,  # 提现说明
        "spbill_create_ip": spbill_create_ip,
    }

    return get_wx_pay(appid).withdraw(request_dict)


def wx_refund(appid, out_trade_no, total_fee, refund_fee, refund_desc="拼团失败"):
    """
    微信统一退款
    """
    request_dict = dict(
        out_trade_no=out_trade_no,
        out_refund_no=generate_out_trade_no(),
        total_fee=int(total_fee * 100),
        refund_fee=int(refund_fee * 100),
        refund_fee_type='CNY',
        refund_desc=refund_desc
    )

    return get_wx_pay(appid).refund(request_dict)


if __name__ == '__main__':
    print(generate_out_trade_no())
