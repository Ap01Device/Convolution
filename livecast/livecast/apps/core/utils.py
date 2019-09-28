import logging
import requests
import uuid
import re

from qiniu import put_file, Auth, BucketManager

from django_redis import get_redis_connection
from django.conf import settings

from core import constants as core_constants
from core.WXBizDataCrypt import WXBizDataCrypt

IS_DEV = getattr(settings, "IS_DEV", True)

logger = logging.getLogger(__name__)

phone_pattern = re.compile(r'^1((3[0-9])|(4[5,7])|(5[0-3,5-9])|(7[0,3,5-8])|(8[0-9])|66|98|99|47)\d{8}')

qiniu_auth = Auth('BvpiseMZraqxVG9Ba8X88tajIq6GlQYZyRSiXUyn', 'rGxJxvHbihI26FR4ejdjHnauF7oNVHDOBnu1Ytn1')

openIdUrl = 'https://api.weixin.qq.com/sns/jscode2session'
accessTokenUrl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'
templateMessageUrl = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'
customerMessageUrl = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={}'
uploadMediaUrl = 'https://api.weixin.qq.com/cgi-bin/media/upload?access_token={}&type=image'
codeUrl = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={}'

wxappid = {
    "qlive": {"name": "心莲相亲直播", "app_id": "wxca891295c56f2c79"},
}


def get_app_secret(app_id):
    """
    获取app_secret
    :param app_id:
    :return: app_secret
    """
    try:
        app_secret = core_constants.WEIXINAPP.get(app_id).get('secret')
    except:
        raise Exception('Invalid APPID')
    else:
        return app_secret


def get_openid(app_id, code):
    """
    获取openid
    :param app_id:
    :param code:
    :return:
    """
    app_secret = get_app_secret(app_id)

    params = dict(
        appid=app_id,
        secret=app_secret,
        js_code=code,
        grant_type='authorization_code')

    try:
        result = requests.post(openIdUrl, data=params)
    except:
        logger.info('request openid error')
    else:
        return result.json()


def get_wx_access_token(app_id):
    app_secret = get_app_secret(app_id)

    try:
        result = requests.get(accessTokenUrl.format(app_id, app_secret))
    except:
        logger.info('request access_token error')
    else:
        if 'access_token' not in result.json():
            logger.info('get access_token error')
            raise Exception('ACCESS_TOKEN ERROR')
        else:
            return result.json()


def get_access_token(app_id):
    """
    获取access_token
    """
    if IS_DEV:
        access_token = requests.get('https://qlive.wxapp.daqinjia.cn/wx/api/access_token/?app_id={}'.format(app_id))
        try:
            access_token = access_token.json()
        except:
            logger.info('测试服获取access_token失败')
            access_token = ''
        else:
            access_token = access_token['access_token']
    else:
        con = get_redis_connection()
        key = core_constants.WX_ACCESS_TOKEN % app_id
        access_token = con.get(key)
        if not access_token:
            token = get_wx_access_token(app_id)['access_token']
            con.set(key, token)
            con.expire(key, 60 * 60)
            access_token = token

    return {'access_token': access_token}


def get_user_info(app_id, session_key, encrypted_data, iv):
    """
    获取用户详细信息
    :param app_id:
    :param session_key:
    :param encrypted_data:
    :param iv:
    :return:
    """
    pc = WXBizDataCrypt(app_id, session_key)
    return pc.decrypt(encrypted_data, iv)


def upload_images(local_file):
    """
    上传七牛云图片
    :param local_file: 本地图片路径
    :return: 图片url
    """
    token = 'BvpiseMZraqxVG9Ba8X88tajIq6GlQYZyRSiXUyn:Je6d2EWcQfV7gml8tXM1uq0K6rw=:eyJzY29wZSI6Imh5c3RlcmlhIiwic2F2ZUtleSI6IiQoZXRhZyktJCh5ZWFyKSQobW9uKSQoZGF5KSQoaG91cikkKG1pbikkKHNlYykkKGV4dCkiLCJkZWFkbGluZSI6MTU3ODMxNzgyMH0='

    filename = "%s.png" % (uuid.uuid1())
    key = '%s/%s' % ('wen', filename)
    ret, info = put_file(token, key, local_file)
    if ret:
        image_url = 'https://images.daqinjia.cn/' + key
        return image_url
    else:
        return 'http://storage.daqinjia.cn/logo.png'


def upload_images_by_url(url):
    auth = qiniu_auth
    bucket = BucketManager(auth)
    filename = "%s.jpg" % (uuid.uuid1())
    key = '%s/%s' % ('wen', filename)

    ret, info = bucket.fetch(url, 'hysteria', key)
    if ret:
        return 'https://images.daqinjia.cn/' + key
    else:
        return 'http://storage.daqinjia.cn/logo.png'


def is_valid_phone(phone):
    matchs = phone_pattern.match(phone)
    return matchs is not None
