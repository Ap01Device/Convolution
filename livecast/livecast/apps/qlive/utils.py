import re
import json
import time
import random
import requests
import hashlib
import logging
from datetime import datetime, timedelta

from qlive import models
from qlive.TLSSigAPI import TLSSigAPI
from qlive.constants import SQL_TEMPLATE_QLIVE as sql
from django.conf import settings
from django.db import connection
from django.db.models import Q

from qlive.constants import MSG_TEMPLATE_QLIVE as msg

IS_DEV = settings.IS_DEV
PAGE_SIZE = 8
logger = logging.getLogger(__name__)
if IS_DEV:
    # IM私钥
    PRI_KEY_CONTENT = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg03DXckeiqjKUExsF
+mVGcZaJP91YE6jDicTiYqFShEahRANCAASfKb7vsCPH7F3tKuT515Fg1mgAGzbf
3gSC6tXvn81/4ydux0R9fBP1szdJDcM9KdWcLbzvSQ5y7QUfr7BWqtiS
-----END PRIVATE KEY-----
"""
    # IM公钥
    PUB_KEY_CONTENT = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEnym+77Ajx+xd7Srk+deRYNZoABs2
394EgurV75/Nf+MnbsdEfXwT9bM3SQ3DPSnVnC2870kOcu0FH6+wVqrYkg==
-----END PUBLIC KEY-----
"""
    # IM管理员身份
    ADMIN_IDENTIFIER = "dqjadmin"
    # IM管理员UserSig 过期时间：2020-01-26 10:08:45
    ADMIN_USER_SIG = 'eJxlj0tPg0AUhff8CsLamGFgpJp0AT4ppS1FbVlNkBnMRWFwGB7V*N9VbCKJ5y6-L-fkfGi6rhv3y-g0zTLRVoqqQ80N-UI3kHHyB*saGE0VtST7B-lQg*Q0zRWXIzQJIRihqQOMVwpyOBrsrUhZCdXEaNgLHWt*X9gIYcsiaDZV4HmE4XV06d9mIJKb3lu87kXbBQ-rMHzfkMc4S56UE4TdVWIP29kuyuOtC17cF1g4d*fkgFxZD6ty1fYLbkX7xpMbP1r6rumsd3FQdO58PqlUUPLjpjPbJvj7JrTjsgFRjQJGJjGxhX5iaJ-aF81KXpE_'
    # IM的APPID
    SDKAPPID = 1400233508
else:
    # IM私钥
    PRI_KEY_CONTENT = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgolDMPbjQ00/pwwRD
rWSjqgifRyWcspLktbNWhrS/WiKhRANCAASgG+kKxoe18UWwae1sBJmhGl2EspZT
9LawhVNke89xNmPa2VP3qYBFzvCNKKggaq4Bb2Y1XzZh0SEiQbRu9K6H
-----END PRIVATE KEY-----
"""
    # IM公钥
    PUB_KEY_CONTENT = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEoBvpCsaHtfFFsGntbASZoRpdhLKW
U/S2sIVTZHvPcTZj2tlT96mARc7wjSioIGquAW9mNV82YdEhIkG0bvSuhw==
-----END PUBLIC KEY-----
"""
    # IM管理员身份
    ADMIN_IDENTIFIER = "dqjadmin"
    # IM管理员UserSig 过期时间：2020-01-26 10:13:04
    ADMIN_USER_SIG = 'eJxlj1FPgzAYRd-5FYRXjbSUopj4YMjCCFtwMhzbC6m0ww*zrkA1iPG-m7Elknhfz8m9ud*GaZrWepHesLI8fkhd6C8lLPPetJB1-QeVAl4wXZCW-4OiV9CKgu21aEeIKaUOQlMHuJAa9nAxeFMzfgA5MTr*Xowz5woXIYdQ4vtTBaoRLmdZEK0CID1EsEhDZUe7IfZxZ3v18ypxd02WyzKVXlY94pd1nlVRxVR4ldQ9St66PpoPG-aKyWBv8224GZIqjvVy3pR1*NQFs4fJpIaDuHzyXJc6t3fuhH6KtoOjHAUHYYodgk6xjB-jF59JXpA_'
    # IM的APPID
    SDKAPPID = 1400235399
# UserSig过期时间 （单位/秒）
UserSigExpired = 24 * 3600 * 180

# IM REST API
# 单个帐号导入接口
ACCOUNT_IMPORT = "https://console.tim.qq.com/v4/im_open_login_svc/account_import?"
# 批量帐号导入接口
MULTIACCOUNT_IMPORT = "https://console.tim.qq.com/v4/im_open_login_svc/multiaccount_import?"
# 帐号登录态失效接口
IM_OPEN_LOGIN_SVC_KICK = "https://console.tim.qq.com/v4/im_open_login_svc/kick?"
# 单发单聊消息
SENDMSG = "https://console.tim.qq.com/v4/openim/sendmsg?"
# 批量发单聊消息
BATCHSENDMSG = "https://console.tim.qq.com/v4/openim/batchsendmsg?"
# 获取用户在线状态
QUERYSTATE = "https://console.tim.qq.com/v4/openim/querystate?"
# 拉取个人资料
PORTRAIT_GET = "https://console.tim.qq.com/v4/profile/portrait_get?"
# 设置资料(用户)
PORTRAIT_SET = "https://console.tim.qq.com/v4/profile/portrait_set?"
# 获取 App 中的所有群组
GET_APPID_GROUP_LIST = "https://console.tim.qq.com/v4/group_open_http_svc/get_appid_group_list?"
# 创建群组
CREATE_GROUP = "https://console.tim.qq.com/v4/group_open_http_svc/create_group?"
# 获取群组详细资料
GET_GROUP_INFO = "https://console.tim.qq.com/v4/group_open_http_svc/get_group_info?"
# 修改群组基础资料
MODIFY_GROUP_BASE_INFO = "https://console.tim.qq.com/v4/group_open_http_svc/modify_group_base_info?"
# 在群组中发送普通消息
SEND_GROUP_MSG = "https://console.tim.qq.com/v4/group_open_http_svc/send_group_msg?"
# 在群组中发送系统通知
SEND_GROUP_SYSTEM_NOTIFICATION = "https://console.tim.qq.com/v4/group_open_http_svc/send_group_system_notification?"
# 查询 App 自定义脏字
OPENIM_DIRTY_WORDS_GET = "https://console.tim.qq.com/v4/openim_dirty_words/get?"
# 添加 App 自定义脏字
OPENIM_DIRTY_WORDS_ADD = "https://console.tim.qq.com/v4/openim_dirty_words/add?"
# 删除 App 自定义脏字
OPENIM_DIRTY_WORDS_DELETE = "https://console.tim.qq.com/v4/openim_dirty_words/delete?"
# 批量删除账号
DELETE_USER = "https://console.tim.qq.com/v4/im_open_login_svc/account_delete?"

QLIVE_HASH_LIKE_NAME = "qlive:like_hashes"
QLIVE_HASH_LIKE_FORMAT = "{0}-{1}"  # 0是点赞人 1是被点赞人

# 推流相关

# 推流防盗链的KEY
PUSH_KEY = "cd1d4589240c979ca1551346f1445963"

if IS_DEV:
    # 推流地址
    PUSH_URL_HEAD = "push.qlive-test.daqinjia.cn"
    # 拉流地址
    PLAY_URL_HEAD = "play.qlive-test.daqinjia.cn"
else:
    PUSH_URL_HEAD = "push.qlive.daqinjia.cn"
    PLAY_URL_HEAD = "play.qlive.daqinjia.cn"

PARAMS = dict(
    sdkappid=SDKAPPID,
    identifier=ADMIN_IDENTIFIER,
    usersig=ADMIN_USER_SIG,
    random='',
    contenttype='json'
)


def generate_user_id(user):
    '''
    生成用户id
    '''
    user.user_id = int("{}{}{}".format(random.randint(10, 99), str(user.id).rjust(4, '0'), random.randint(10, 99)))
    user.save(update_fields=['user_id'])


def generate_user_sig(user_id):
    '''
    生成IM的UserSig
    :param user_id:用户的identifier
    :return:UserSig
    '''
    api = TLSSigAPI(SDKAPPID, PRI_KEY_CONTENT, PUB_KEY_CONTENT)
    sig = api.gen_sig(str(user_id), UserSigExpired)
    return sig


def generate_32_unsigned_integer():
    """
    生成32位无符号整数
    """
    dateStr = time.strftime('%Y%m%d%H%M%S', time.localtime())[2:]
    timeStamp = str(time.time()).replace('.', str(random.randint(100, 1000)))
    return timeStamp + dateStr


def generate_params(params=PARAMS):
    '''
    拼接请求参数
    '''
    params['random'] = generate_32_unsigned_integer()
    params_str = "&".join(["{}={}".format(k, v) for k, v in params.items()])
    return params_str


def post(url, data):
    return requests.post(url, data, verify=False)


def get(url):
    return requests.get(url, verify=False)


def account_import(user_id, nickname='', face_url=''):
    '''
    单个导入账号
    :param user_id:用户id
    :param nickname: 昵称
    :param face_url: 头像
    :return:响应结果
    '''
    url = ACCOUNT_IMPORT + generate_params()
    data = {
        "Identifier": str(user_id),
        "Nick": nickname,
        "FaceUrl": face_url
    }
    res = post(url, json.dumps(data))
    return res.json()


def multiaccount_import(accounts):
    '''
    多个账号导入
    :param accounts:账号ID列表
    :return:响应结果
    '''
    url = MULTIACCOUNT_IMPORT + generate_params()
    data = dict(
        Accounts=accounts
    )
    res = post(url, json.dumps(data))
    return res.json()


def kick(user_id):
    '''
    帐号登录态失效
    :param user_id:用户id
    :return: 响应结果
    '''
    url = IM_OPEN_LOGIN_SVC_KICK + generate_params()
    data = dict(
        Identifier=str(user_id)
    )
    res = post(url, json.dumps(data))
    return res.json()


def send_msg(to_account, msg):
    '''
    单对单发消息（管理员对用户发消息）
    :param to_account:接收者id
    :param msg:消息内容
    :return:响应结果
    '''
    url = SENDMSG + generate_params()
    data = dict(
        SyncOtherMachine=2,
        To_Account=str(to_account),
        MsgLifeTime=60,
        MsgRandom=int(random.random() * time.time()),
        MsgTimeStamp=int(time.time()),
        MsgBody=[
            {
                "MsgType": "TIMTextElem",
                "MsgContent": {
                    "Text": json.dumps(msg)
                }
            }
        ]
    )
    res = post(url, json.dumps(data))
    return res.json()


def create_pushurl(stream_name, tx_time):
    '''
    自主拼装推流URL
    :param:stream_name:流id
    :param:tx_time:过期时间
    :return:推流URL
    '''
    tx_secret = generate_txsecret(stream_name, tx_time)
    live_push_url = 'rtmp://{0}/live/{1}?txSecret={2}&txTime={3}'.format(PUSH_URL_HEAD, stream_name, tx_secret, tx_time)
    return live_push_url


def create_playurl(stream_name):
    '''
    自主拼装播放URL
    :param stream_name:流id
    :return:播放URL
    '''
    live_play_url = 'rtmp://{0}/live/{1}'.format(PLAY_URL_HEAD, stream_name)
    return live_play_url


def generate_txsecret(stream_name, tx_time):
    '''
    生成防盗链签名
    :param:stream_name:流id
    :param:tx_time:过期时间
    :return:防盗链签名
    '''
    tx_secret = hashlib.md5()
    tx_secret.update(PUSH_KEY.encode('utf8') + stream_name.encode('utf8') + tx_time.encode('utf8'))
    return tx_secret.hexdigest()


def generate_txtime():
    '''
    生成十六进制的UNIX时间戳过期时间
    :return:
    '''
    tx_time = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d%H%M%S')
    time_array = time.strptime(tx_time, '%Y%m%d%H%M%S')
    ans_time = int(time.mktime(time_array))
    return hex(ans_time)[2:]


def batch_send_msg(to_account_list, msg):
    '''
    单对单批量发送消息
    :param to_account_list: 接收消息的用户id列表
    :param msg: 消息内容
    :return: 响应结果
    '''
    url = BATCHSENDMSG + generate_params()
    data = dict(
        SyncOtherMachine=2,
        To_Account=to_account_list,
        MsgRandom=int(random.random() * time.time()),
        MsgBody=[
            {
                "MsgType": "TIMTextElem",
                "MsgContent": {
                    "Text": json.dumps(msg)
                }
            }
        ]
    )
    res = post(url, json.dumps(data))
    return res.json()


def query_state(to_account_list):
    '''
    获取用户在线状态
    :param to_account_list:接收消息的用户id列表
    :return:响应结果
    '''
    url = QUERYSTATE + generate_params()
    data = dict(
        To_Account=to_account_list
    )
    res = post(url, json.dumps(data))
    return res.json()


def portrait_get(to_account_list, tag_list):
    '''
    批量获取用户的信息
    :param to_account_list:要获取的id列表
    :param tag_list: 要获取的字段列表
    :return: 响应结果
    '''
    url = PORTRAIT_GET + generate_params()
    data = dict(
        To_Account=to_account_list,
        TagList=tag_list,
    )
    res = post(url, json.dumps(data))
    return res.json()


def portrait_set(from_account, nickname="", face_url=""):
    '''
    设置资料
    :param from_account:需要设置该用户的资料
    :param nickname:昵称
    :param face_url:头像
    :return:响应结果
    '''
    url = PORTRAIT_SET + generate_params()
    profile_item = []
    if nickname:
        profile_item.append(
            {
                "Tag": "Tag_Profile_Custom_Nickname",
                "Value": nickname
            }
        )
    if face_url:
        profile_item.append(
            {
                "Tag": "Tag_Profile_IM_Image",
                "Value": face_url
            }
        )
    data = dict(
        From_Account=str(from_account),
        ProfileItem=profile_item
    )
    res = post(url, json.dumps(data))
    return res.json()


def get_appid_group_list():
    '''
    获取APP中所有的群组
    :return:响应结果
    '''
    url = GET_APPID_GROUP_LIST + generate_params()
    data = dict()
    res = post(url, json.dumps(data))
    return res.json()


def create_group(owner_account, name, face_url):
    '''
    创建群组
    :param owner_account:群主id
    :param name:群名称
    :param face_url:群头像
    :return:响应结果
    '''
    url = CREATE_GROUP + generate_params()
    data = dict(
        Owner_Account=str(owner_account),
        Type="AVChatRoom",
        Name=name,
        FaceUrl=face_url,
    )
    res = post(url, json.dumps(data))
    return res.json()


def get_group_info(group_id_list):
    '''
    获取群组详细资料
    :param group_id_list:群组id列表
    :return:响应结果
    '''
    url = GET_GROUP_INFO + generate_params()
    data = dict(
        GroupIdList=group_id_list,
    )
    res = post(url, json.dumps(data))
    return res.json()


def modify_group_base_info(group_id, name="", face_url=""):
    '''
    修改IM群基本信息
    :param group_id:IM群id
    :param name: 群昵称
    :param face_url: 群头像
    :return: 响应结果
    '''
    url = MODIFY_GROUP_BASE_INFO + generate_params()
    data = dict(
        GroupId=group_id
    )
    if name:
        data['Name'] = name
    if face_url:
        data['FaceUrl'] = face_url
    res = post(url, json.dumps(data))
    return res.json()


def send_group_msg(group_id, msg):
    '''
    在群组中发送普通消息
    :param group_id:群id
    :param msg:消息内容
    :return:响应结果
    '''
    url = SEND_GROUP_MSG + generate_params()
    data = dict(
        GroupId=group_id,
        Random=int(random.random() * time.time()),
        MsgBody=[
            {
                "MsgType": "TIMTextElem",
                "MsgContent": {
                    "Text": json.dumps(msg)
                }
            }
        ]
    )
    res = post(url, json.dumps(data))
    return res.json()


def send_group_system_notification(group_id, msg):
    '''
    在群组中发送系统通知
    :param group_id:群id
    :param msg:消息内容
    :return:响应结果
    '''
    url = SEND_GROUP_SYSTEM_NOTIFICATION + generate_params()
    data = dict(
        GroupId=group_id,
        Content=json.dumps(msg)
    )
    res = post(url, json.dumps(data))
    return res.json()


def openim_dirty_words_add(dirty_words_list):
    '''
    添加 App 自定义脏字
    :param dirty_words_list:自定义脏字列表
    :return:响应结果
    '''
    url = OPENIM_DIRTY_WORDS_ADD + generate_params()
    data = dict(
        DirtyWordsList=dirty_words_list
    )
    res = post(url, json.dumps(data))
    return res.json()


def openim_dirty_words_get():
    '''
    查询 App 自定义脏字
    :return: 响应结果
    '''
    url = OPENIM_DIRTY_WORDS_GET + generate_params()
    res = get(url)
    return res.json()


def openim_dirty_words_delete(dirty_words_list):
    '''
    删除 App 自定义脏字
    :param dirty_words_list:自定义脏字列表
    :return:响应结果
    '''
    url = OPENIM_DIRTY_WORDS_DELETE + generate_params()
    data = dict(
        DirtyWordsList=dirty_words_list
    )
    res = post(url, data)
    return res.json()


def delete_user(accounts):
    '''
    删除账号
    :param accounts:账号列表
    :return:响应结果
    '''
    url = DELETE_USER + generate_params()
    delete_item = []
    for a in accounts:
        delete_item.append({"UserID": a})
    data = {
        "DeleteItem": delete_item
    }
    res = post(url, json.dumps(data))
    return res.json()


def get_live_people_num(live_id):
    '''
    获取指定直播间人数
    :param live_id: 直播间id
    :return: 直播间人数列表[男上麦,全部男，女上麦，全部女]
    '''
    cursor = connection.cursor()
    cursor_sql = sql['get_live_people_num'] % live_id
    cursor.execute(cursor_sql)
    num_list = cursor.fetchone()
    if num_list:
        return num_list
    else:
        return []


def logout(account):
    '''
    清理用户信息
    :param account: 用户id
    '''
    try:
        user = models.User.objects.get(user_id=account)
    except models.User.DoesNotExist:
        logger.info('user_id:%s不存在' % account)
        return
    u2l = models.User2Live.objects.filter(Q(user_id=account) & ~Q(state=0)).first()
    if not u2l:
        logger.info('User2Live实例对象不存在:%s' % account)
        return

    try:
        live_room = models.LiveBroadcastRoom.objects.get(id=u2l.live_id)
    except models.LiveBroadcastRoom.DoesNotExist:
        logger.info('直播间:%s不存在' % u2l.live_id)
        return

    if u2l.is_host == 1:
        # 大主播
        u2l.state = 0
        u2l.save(update_fields=['state'])
        live_room.is_live = False
        live_room.play_url_male = ""
        live_room.play_url_female = ""
        live_room.continuous_time += int(datetime.now().timestamp() - live_room.start_time.timestamp())
        live_room.save(update_fields=['is_live', 'play_url_male', 'play_url_female', 'continuous_time'])
        m = msg['OVER']
        res = send_group_msg(live_room.group_id, m)
        logger.info(res)
    else:
        # 不是大主播
        if u2l.state == 3:
            live_room.play_url_male = ""
            live_room.save(update_fields=['play_url_male'])
            m = msg['RESET']
            m['content']['user_id'] = user.user_id
            m['content']['gender'] = user.gender
            send_group_msg(live_room.group_id, m)
        elif u2l.state == 4:
            live_room.play_url_female = ""
            live_room.save(update_fields=['play_url_female'])
            m = msg['RESET']
            m['content']['user_id'] = user.user_id
            m['content']['gender'] = user.gender
            send_group_msg(live_room.group_id, m)
        u2l.state = 0
        u2l.save(update_fields=['state'])
        cursor = connection.cursor()
        cursor_sql = sql['get_host_id_by_group'] % live_room.group_id
        cursor.execute(cursor_sql)
        owner = cursor.fetchone()
        if not owner:
            logger.info("%s 主播不存在" % live_room.group_id)
        owner_id = owner[0]
        m = msg['NUM']
        m['content']['num_list'] = get_live_people_num(live_room.pk)
        m['content']['group_id'] = live_room.group_id
        res = send_msg(to_account=owner_id, msg=m)
        logger.info(res)


def check_len(string):
    '''
    裁剪字符串
    :param string: 要被裁剪的字符串
    :return: 裁剪结果
    '''
    l = 0
    i = 0
    while i < len(string):
        if re.match('[\u2E80-\u9FFF]', string[i]):
            l += 3
        else:
            l += 1
        if l > 20:
            return string[:i]
        i += 1
    return string


def send_num_to_owner(live_id, group_id=""):
    '''
    向主播发送直播间人数
    :param live_id: 直播间id
    '''
    owner = models.User2Live.objects.filter(live_id=live_id, is_host=True).values('user_id').first()
    if owner:
        if not group_id:
            try:
                live_room = models.LiveBroadcastRoom.objects.get(id=live_id)
            except models.LiveBroadcastRoom.DoesNotExist:
                logger.info("直播间不存在%s" % live_id)
                return
            group_id = live_room.group_id
        owner_id = owner['user_id']
        try:
            m = msg["NUM"]
            m['content']['num_list'] = get_live_people_num(live_id)
            m['content']['group_id'] = group_id
            res = send_msg(owner_id, m)
            logger.info(res)
        except Exception as e:
            logger.info(e)
            logger.info("live_id:%s,向红娘发送失败" % live_id)
