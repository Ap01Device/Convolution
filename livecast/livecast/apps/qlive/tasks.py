import datetime
import time

from django.db import connection
from django_redis import get_redis_connection

from celery.utils.log import get_task_logger
from celery.decorators import task
from celery.decorators import periodic_task
from celery.task.schedules import crontab

from qlive import utils as us
from qlive.models import (
    User,
    User2Live,
    LiveBroadcastRoom,
    Like,
)
from qlive.constants import SQL_TEMPLATE_QLIVE as sql
from qlive.constants import MSG_TEMPLATE_QLIVE as msg

logger = get_task_logger(__name__)


@task(name='qlive.after_member_exit')
def after_member_exit_async(data):
    logger.info('群成员离开之后回调 ')
    logger.info(data)
    group_id = data.get('GroupId', '')
    cursor = connection.cursor()
    cursor_sql = sql['get_host_id_by_group'] % group_id
    cursor.execute(cursor_sql)
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        members = data.get('ExitMemberList', [])
        for member in members:
            if User2Live.objects.filter(user_id=member['Member_Account'], live_id=user[1]).exists():
                User2Live.objects.filter(user_id=member['Member_Account'], live_id=user[1]).update(state=0)
            else:
                User2Live.objects.create(user_id=member['Member_Account'],
                                         live_id=user[1],
                                         is_host=False,
                                         state=0,
                                         last_change=datetime.datetime.now())
        m = msg['NUM']
        m['content']['num_list'] = us.get_live_people_num(user[1])
        m['content']['group_id'] = group_id
        res = us.send_msg(to_account=user_id, msg=m)
        logger.info(res)
        if res.get('ActionStatus', "") == "OK":
            logger.info("发送给主播：%s成功" % user_id)
        else:
            logger.info("发送给主播：%s失败" % user_id)
    else:
        logger.info("IM群为group_id:%s的主播不存在" % group_id)


# @task(name='qlive.member_join_async')
# def member_join_async(data):
#     logger.info('新成员入群之后回调 ')
#     logger.info(data)
#     group_id = data.get('GroupId', '')
#     cursor = connection.cursor()
#     cursor_sql = sql['get_host_id_by_group'] % group_id
#     cursor.execute(cursor_sql)
#     user = cursor.fetchone()
#     if user:
#         user_id = user[0]
#         members = data.get('NewMemberList', [])
#         for member in members:
#             if User2Live.objects.filter(user_id=member['Member_Account'], live_id=user[1]).exists():
#                 User2Live.objects.filter(user_id=member['Member_Account'], live_id=user[1]).update(state=1)
#             else:
#                 User2Live.objects.create(user_id=member['Member_Account'],
#                                          live_id=user[1],
#                                          is_host=False,
#                                          state=1,
#                                          last_change=datetime.datetime.now())
#         m = msg['NUM']
#         m['content']['num_list'] = us.get_live_people_num(user[1])
#         m['content']['group_id'] = group_id
#         res = us.send_msg(to_account=user_id, msg=m)
#         logger.info(res)
#         if res.get('ActionStatus', "") == "OK":
#             logger.info("发送给主播：%s成功" % user_id)
#         else:
#             logger.info("发送给主播：%s失败" % user_id)
#     else:
#         logger.info("IM群为group_id:%s的主播不存在" % group_id)


@task(name='qlive.state_change')
def state_change_async(data):
    logger.info('在线状态变更回调 ')
    logger.info(data)
    try:
        if data['Info']['Action'] != "Logout":
            return
    except Exception as e:
        logger.info(e)
    account = data['Info']['To_Account']
    us.logout(account)


@task(name='qlive.account_import')
def account_import_async(user_id, nickname, face_url):
    logger.info('导入IM %s, %s, %s' % (user_id, nickname, face_url))
    res = us.account_import(user_id, nickname, face_url)
    logger.info(res)
    if res['ActionStatus'] != "OK":
        logger.info("%s导入失败" % user_id)
    else:
        result = us.portrait_set(user_id, nickname)
        logger.info(result)


@periodic_task(run_every=(crontab(minute=0, hour=2)), name='qlive.save_like_database',
               ignore_result=True)
def save_like_database():
    logger.info('每天凌晨同步redis的点赞数据到数据库')
    con = get_redis_connection()
    cursor = 0
    while True:
        page = con.hscan(us.QLIVE_HASH_LIKE_NAME, cursor=cursor, count=100)
        cursor = page[0]
        data = page[1]
        for d in data:
            user_id, passive_user_id = d.split('-')
            like = Like.objects.filter(user_id=user_id, passive_user_id=passive_user_id).first()
            if not like:
                Like.objects.create(user_id=user_id, passive_user_id=passive_user_id, like_state=data[d])
                continue
            try:
                like_state = int(data[d])
            except Exception:
                continue
            if like.like_state != like_state:
                like.like_state = like_state
                like.save(update_fields=["like_state"])
        if not cursor:
            break
    con.delete(us.QLIVE_HASH_LIKE_NAME)
    return "同步完成"


cmd = {
    # "Group.CallbackAfterNewMemberJoin": member_join_async,
    "Group.CallbackAfterMemberExit": after_member_exit_async,
    "State.StateChange": state_change_async,
}
