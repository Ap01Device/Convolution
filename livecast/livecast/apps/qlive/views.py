import time
import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import HttpResponse
from django_redis import get_redis_connection
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    authentication_classes,
)

from qlive.models import (
    User,
    UserToken,
    Gift,
    PayModel,
    LiveBroadcastRoom,
    User2Live,
    Config,
    Order,
    Like
)
from qlive.serializers import (
    UserSerializer,
    LiveBroadcastRoomSerializer,
    LiveRoomSerializer,
    UserStateSerializer,
    ConfigSerializer,
)
from qlive import utils as us
from qlive import payutils as ps
from qlive import tasks as ts
from qlive.authentication import UserTokenAuthentication
from qlive.pagination import QLivePagination
from qlive.constants import SQL_TEMPLATE_QLIVE as sql
from qlive.constants import MSG_TEMPLATE_QLIVE as msg
from qlive.pywxpay import WXPayUtil
from qlive.sign_util import SignUtil
from core.permissions import IsOwnerOrReadOnly
from core import utils as core_utils

logger = logging.getLogger(__name__)


class UsersView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    ordering = ('-id',)

    def create(self, request, *args, **kwargs):
        logger.debug('授权直播小程序')
        data = request.data
        logger.info(data)
        if any([_ not in data for _ in ('appId', 'code', 'encryptedData', 'iv')]):
            return Response({'detail': 'Parameter error'}, status=status.HTTP_400_BAD_REQUEST)

        sessionData = core_utils.get_openid(data['appId'], data['code'])  # 获取openid
        logger.info(sessionData)
        try:
            openid = sessionData['openid']
            sessionkey = sessionData['session_key']
        except Exception as e:
            logging.info(e)
            return Response({'detail': 'Code error'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(open_id=openid)  # 根据openid查询用户
        except User.DoesNotExist:
            try:
                userInfo = core_utils.get_user_info(data['appId'], sessionkey, data['encryptedData'], data['iv'])
            except:
                return Response({'detail': 'Encrypted failed'}, status=status.HTTP_400_BAD_REQUEST)
            logger.info(userInfo)
            gender = userInfo["gender"] if userInfo["gender"] else 1
            if gender == 2:
                height = 165
            else:
                height = 180

            new_user = User.objects.create(  # 新建QLive用户
                open_id=openid,
                app_id=data['appId'],
                session_key=sessionkey,
                nickname=us.check_len(userInfo["nickName"]),
                gender=gender,
                height=height,
                area='310100',
                face_url=userInfo["avatarUrl"]
            )
            us.generate_user_id(new_user)
            logger.info({"new_user": new_user.user_id})
            token = UserToken.objects.create(user_id=new_user.user_id)

            new_user.user_sig = us.generate_user_sig(new_user.user_id)
            new_user.user_sig_expired = datetime.now() + timedelta(seconds=us.UserSigExpired)
            new_user.save(update_fields=('user_sig', 'user_sig_expired',))

            results = {'token': token.key, 'user_id': str(new_user.user_id), 'user_sign': new_user.user_sig,
                       'sdk_app_id': us.SDKAPPID}
            logger.info("%s, %s, %s" % (new_user.user_id, new_user.nickname, new_user.face_url))
            ts.account_import_async.delay(new_user.user_id, new_user.nickname, new_user.face_url)
        else:
            logger.debug('用户存在')
            try:
                token = UserToken.objects.get(user_id=user.user_id)  # 获取token
            except UserToken.DoesNotExist:
                return Response({'detail': 'Token does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            User.objects.filter(open_id=openid).update(session_key=sessionkey)
            results = {'token': token.key, 'user_id': str(user.user_id), 'user_sign': user.user_sig,
                       'sdk_app_id': us.SDKAPPID}
        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsOwnerOrReadOnly])
    def login(self, request, *args, **kwargs):
        logger.debug('登录直播小程序')
        data = request.data
        logger.info(data)

        if any([_ not in data for _ in ('appId', 'code')]):
            return Response({'detail': 'Parameter error'}, status=status.HTTP_400_BAD_REQUEST)

        sessionData = core_utils.get_openid(data['appId'], data['code'])  # 获取openid

        logger.info(sessionData)

        try:
            openid = sessionData['openid']
            sessionkey = sessionData['session_key']
        except Exception as e:
            logger.info(e)
            return Response({'detail': 'Code error'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(open_id=openid)  # 根据openid查询用户
        except User.DoesNotExist:
            logger.debug("用户不存在")
            results = {'status': 1}
            return Response(results, status=status.HTTP_200_OK)
        else:
            logger.debug('用户存在')
            try:
                token = UserToken.objects.get(user_id=user.user_id)  # 获取token
            except UserToken.DoesNotExist:
                return Response({'detail': 'Token does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            now_time = datetime.now()
            user.session_key = sessionkey
            user.last_login_time = now_time
            if user.user_sig_expired < now_time:
                user.user_sig = us.generate_user_sig(user.user_id)
                user.user_sig_expired = now_time + timedelta(seconds=us.UserSigExpired)
                user.save(update_fields=('session_key', 'last_login_time', 'user_sig', 'user_sig_expired'))
            else:
                user.save(update_fields=('session_key', 'last_login_time',))
            results = {'status': 0, 'token': token.key, 'user_id': str(user.user_id), 'user_sign': user.user_sig,
                       'sdk_app_id': us.SDKAPPID}
            u2l = User2Live.objects.filter(Q(user_id=user.user_id) & ~Q(state=0)).first()
            if u2l:
                try:
                    live_room = LiveBroadcastRoom.objects.get(id=u2l.live_id)
                except LiveBroadcastRoom.DoesNotExist:
                    logger.info('直播间不存在:%s' % u2l.live_id)
                    return Response('直播间不存在:%s' % u2l.live_id, status=status.HTTP_400_BAD_REQUEST)
                live_room_info = LiveRoomSerializer(live_room, many=False).data
                results['live_room_name'] = live_room_info.get('owner', {}).get('nickname', '')
                results['live_id'] = live_room.id
                results['group_id'] = live_room.group_id
                results['user_type'] = u2l.state
                if u2l.is_host:
                    results['user_type'] = 5
                results['login_type'] = 1
            else:
                results['login_type'] = 0

        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsOwnerOrReadOnly],
            authentication_classes=[UserTokenAuthentication])
    def get_user_state(self, request, *args, **kwargs):
        '''
        获取用户状态
        '''
        results = dict(
            live_room_name="",
            live_id="",
            group_id="",
            user_type=0
        )
        user = request.user
        u2l = User2Live.objects.filter(Q(user_id=user.user_id) & ~Q(state=0)).first()
        if not u2l:
            return Response(results, status=status.HTTP_200_OK)
        try:
            live_room = LiveBroadcastRoom.objects.get(id=u2l.live_id)
        except LiveBroadcastRoom.DoesNotExist:
            logger.info('直播间不存在:%s' % u2l.live_id)
            return Response('直播间不存在:%s' % u2l.live_id, status=status.HTTP_400_BAD_REQUEST)

        user2live = User2Live.objects.filter(live_id=live_room.id, is_host=True).first()
        if not user2live:
            logger.info('主播与直播间关系不存在:%s' % live_room.id)
            return Response('主播与直播间关系不存在:%s' % live_room.id, status=status.HTTP_400_BAD_REQUEST)
        try:
            owner = User.objects.get(user_id=user2live.user_id)
        except User.DoesNotExist:
            logger.info('主播不存在:%s' % user2live.user_id)
            return Response('主播不存在:%s' % user2live.user_id, status=status.HTTP_400_BAD_REQUEST)
        results = dict(
            live_room_name=owner.nickname,
            live_id=u2l.live_id,
            group_id=live_room.group_id
        )
        if u2l.is_host:
            results['user_type'] = 5
        else:
            results['user_type'] = u2l.state
        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def update_userinfo(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        logger.debug("{}修改个人信息".format(user.user_id))
        logger.info(data)
        im_update = {}
        group_update = {}
        if "nickname" in data:
            im_update["nickname"] = data['nickname']
            group_update['name'] = data['nickname']
        if "face_url" in data:
            im_update["face_url"] = data['face_url']
            group_update['face_url'] = data['face_url']
        new_user = self.get_serializer(instance=user, data=data)
        try:
            new_user.is_valid(raise_exception=True)
            new_user.save()
        except exceptions.ValidationError as e:
            logger.info("user_id:%s" % user.user_id)
            logger.info(e)
            return Response("UPDATE FAIL", status=status.HTTP_400_BAD_REQUEST)
        if user.is_matchmaker:
            live_rooms = LiveBroadcastRoom.objects.raw(sql['get_group_id'], params=(user.user_id,))
            if live_rooms:
                live_room = live_rooms[0]
                group_update['group_id'] = live_room.group_id
                group_res = us.modify_group_base_info(**group_update)
                logger.info(group_res)
            else:
                logger.info("%s的直播间不存在" % user.user_id)
        res = us.portrait_set(user.user_id, **im_update)
        logger.info(res)
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsOwnerOrReadOnly],
            authentication_classes=[UserTokenAuthentication])
    def get_userinfo(self, request, *args, **kwargs):
        '''
        根据用户id获取用户信息
        '''
        user_id = request.GET.get('user_id', '')
        logger.debug("查询%s的信息" % user_id)
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            logger.info("user_id:%s" % user_id)
            return Response("user_id不存在", status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(user, many=False)
        config = Config.objects.filter(ikey='WITHDRAW_RATE').values('ival').first()
        if not config:
            logger.info("提现汇率WITHDRAW_RATE不存在")
            return Response("提现汇率WITHDRAW_RATE不存在", status=status.HTTP_400_BAD_REQUEST)
        res = {'rate': config['ival']}
        res.update(serializer.data)
        return Response(res, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsOwnerOrReadOnly],
            authentication_classes=[UserTokenAuthentication])
    def get_users_info(self, request, *args, **kwargs):
        gender = request.GET.get('gender', '')
        live_id = request.GET.get('live_id', '')
        page = request.GET.get('page', 1)
        if isinstance(page, str) and not page.isdigit():
            page = 1
        page_begin = int(page) * us.PAGE_SIZE - us.PAGE_SIZE
        page_end = us.PAGE_SIZE
        logger.debug("查询%s房间的性别为%s的信息" % (live_id, gender))
        if not gender or not live_id or not gender.isdigit() or not live_id.isdigit():
            logger.info('参数错误（room_id:%s,gender:%s）' % (live_id, gender))
            return Response('参数错误（room_id:%s,gender:%s）' % (live_id, gender), status=status.HTTP_400_BAD_REQUEST)
        users = User.objects.raw(sql['get_user_info'], params=(live_id, gender, page_begin, page_end))
        serializer = UserStateSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsOwnerOrReadOnly],
            authentication_classes=[UserTokenAuthentication])
    def logout(self, request, *args, **kwargs):
        '''
        用户退出小程序
        '''
        user = request.user
        logger.info("%s退出小程序" % user.user_id)
        us.logout(user.user_id)
        return Response({'detail': "OK"}, status=status.HTTP_200_OK)


class GiftViewSet(viewsets.ModelViewSet):
    queryset = Gift.objects.all()
    permission_classes = (IsAuthenticated,)
    authentication_classes = (UserTokenAuthentication,)
    pagination_class = QLivePagination

    def list(self, request, *args, **kwargs):
        user = request.user
        logger.debug('{}获取礼物列表'.format(user.user_id))
        gifts = Gift.objects.all()
        gifts_list = [{
            "id": gift.id,
            "name": gift.name,
            "image": gift.image,
            "gold": gift.gold,
            "effect": gift.effect
        } for gift in gifts]
        page_list = self.paginate_queryset(queryset=gifts_list)
        return self.get_paginated_response(page_list)

    @action(detail=False, methods=['GET'], permission_classes=[IsOwnerOrReadOnly],
            authentication_classes=[UserTokenAuthentication])
    def push_gift(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id', '')
        gift_id = request.GET.get('gift_id', '')
        num = request.GET.get('num', '')
        user = request.user
        logger.debug("%s送礼物" % user.user_id)
        logger.info(request.GET)
        if not user_id or not gift_id or not num or not user_id.isdigit() or not gift_id.isdigit() or not num.isdigit():
            return Response("参数错误（user_id:%s,gift_id:%s,num:%s）" % (user_id, gift_id, num),
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            gift = Gift.objects.get(id=gift_id)
        except Gift.DoesNotExist:
            return Response("gift_id:%s不存在" % gift_id, status=status.HTTP_400_BAD_REQUEST)
        try:
            rec_user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response("user_id:%s不存在" % user_id, status=status.HTTP_400_BAD_REQUEST)
        num = int(num)
        if num <= 0:
            return Response("num:%s不能低于1" % num, status=status.HTTP_400_BAD_REQUEST)
        amount = gift.gold * num
        if amount > user.gold + user.income:
            res = dict(
                code="failed",
                detail='账户余额不足'
            )
            return Response(res, status=status.HTTP_200_OK)
        else:
            try:
                ex_rate = Config.objects.filter(ikey="EXCHANGE_RATE").values('ival').first()
                ex_rate = float(ex_rate['ival'])
            except Exception as e:
                logger.info("EXCHANGE_RATE 不存在,需要配置到config")
                return Response("EXCHANGE_RATE不存在")
            if user.gold >= amount:
                user.gold -= amount
                user.save(update_fields=["gold"])
            else:
                amount -= user.gold
                user.gold = 0
                user.income -= amount
                user.save(update_fields=["gold", "income"])
            rec_user.income += int(amount * ex_rate)
            rec_user.save(update_fields=["income"])
            res = dict(
                code="success",
                gold=user.gold,
                income=user.income,
                detail='赠送成功'
            )
            return Response(res, status=status.HTTP_200_OK)


class PayViewSet(viewsets.ModelViewSet):
    queryset = PayModel.objects.all().order_by('price')
    permission_classes = (IsAuthenticated,)
    authentication_classes = (UserTokenAuthentication,)

    def list(self, request, *args, **kwargs):
        user = request.user
        logger.debug('{}获取充值列表'.format(user.user_id))
        pay_list = [{
            "id": pay.id,
            "price": pay.price,
            "gold": pay.gold
        } for pay in self.get_queryset()]
        return Response(pay_list, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        logger.debug("%s 充值金币" % user.user_id)
        logger.info(data)
        try:
            block_id = data['block_id']
        except Exception as e:
            logger.info(e)
            return Response("缺少block_id参数", status=status.HTTP_400_BAD_REQUEST)
        try:
            pay_model = PayModel.objects.get(id=block_id)
        except PayModel.DoesNotExist:
            return Response("block_id：%s不存在" % block_id, status=status.HTTP_400_BAD_REQUEST)
        else:
            order = Order.objects.create(
                order_id=ps.generate_out_trade_no(),
                cost=pay_model.price,
                gold=pay_model.gold,
                user_id=user.user_id,
            )
            order_form = ps.wx_unifieorder(appid=user.app_id,
                                           openid=user.open_id,
                                           out_trade_no=order.pk,
                                           money=order.cost,
                                           body="大亲家-心恋视频相亲-金币充值")
            if order_form['return_code'] == 'SUCCESS' and order_form['result_code'] == 'SUCCESS':
                logger.info(order_form)
                content_dict = dict(
                    appId=user.app_id,
                    timeStamp=str(int(time.time())),
                    nonceStr=order_form['nonce_str'],
                    package='prepay_id={}'.format(order_form['prepay_id']),
                    signType='MD5',
                )
                content_dict['paySign'] = WXPayUtil.generate_signature(content_dict, settings.WEIXINAPP_KEY)
                del content_dict['appId']
                order.prepay_id = order_form['prepay_id']
                order.save(update_fields=['prepay_id'])
                timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                content_list = ['{}={}'.format(key, value) for key, value in content_dict.items()]
                content_str = '&'.join(content_list)
                sign = SignUtil.sign(timestamp, content_str)
                logger.info(content_str)
                return Response({'timestamp': timestamp, 'sign': sign, 'content': content_str},
                                status=status.HTTP_200_OK)
            else:
                logger.info(order_form)
            return Response({'detail': 'Request payment failed'}, status=status.HTTP_200_OK)


class LiveShowViewSet(viewsets.ModelViewSet):
    queryset = LiveBroadcastRoom.objects.all()
    permission_classes = (IsAuthenticated,)
    authentication_classes = (UserTokenAuthentication,)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def matchmaker_enter(self, request, *args, **kwargs):
        logger.debug('红娘开始直播')
        user = request.user

        if not user.is_matchmaker:
            return Response({'detail': "The user's identity is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if user.banned != 0:
            return Response({"status": "failed"}, status=status.HTTP_200_OK)
        try:
            user_live = User2Live.objects.get(user_id=user.user_id, is_host=True)
        except User2Live.DoesNotExist:
            return Response({'detail': 'There is no relationship between users and live broadcasters'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            live_room = LiveBroadcastRoom.objects.get(pk=user_live.live_id)
        except LiveBroadcastRoom.DoesNotExist:
            return Response({'detail': 'There is no live studio.'}, status=status.HTTP_400_BAD_REQUEST)
        user_live.state = 1
        user_live.save(update_fields=('state',))

        live_room.is_live = True
        live_room.start_time = datetime.now()
        live_room.save(update_fields=('is_live', 'start_time'))

        tx_time = us.generate_txtime()
        push_url = us.create_pushurl(str(user.user_id), tx_time)

        result = {
            "status": "ok",
            "user_id": str(user.user_id),
            "live_id": live_room.pk,
            "nickname": user.nickname,
            "face_url": user.face_url,
            "push_url": push_url,
            "play_url": live_room.play_url_owner,
            "group_id": live_room.group_id
        }

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def apply_micro(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        logger.debug('{}用户申请上麦'.format(user.user_id))
        logger.info(data)

        if "live_id" not in data:
            return Response({'detail': 'parameter error.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_live = User2Live.objects.get(live_id=data["live_id"], user_id=user.user_id, state=1)
        except User2Live.DoesNotExist:
            logger.info('{} Users are not in the live studio.'.format(user.user_id))
            return Response({'detail': 'Users are not in the live studio'}, status=status.HTTP_400_BAD_REQUEST)
        user_live.state = 2
        user_live.save(update_fields=('state',))
        us.send_num_to_owner(data["live_id"])

        return Response({'detail': 'OK'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def accept_micro(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        logger.debug('{}用户接受上麦'.format(user.user_id))
        logger.info(data)

        if "live_id" not in data:
            return Response({'detail': 'parameter error.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            live_room = LiveBroadcastRoom.objects.get(pk=data["live_id"])
        except LiveBroadcastRoom.DoesNotExist:
            logger.debug('{} There is no live studio.'.format(user.user_id))
            return Response({'detail': 'There is no live studio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_live = User2Live.objects.get(live_id=data["live_id"], user_id=user.user_id)
        except User2Live.DoesNotExist:
            logger.debug('{} Users are not in the live studio.'.format(user.user_id))
            return Response({'detail': 'Users are not in the live studio'}, status=status.HTTP_400_BAD_REQUEST)

        tx_time = us.generate_txtime()
        push_url = us.create_pushurl(str(user.user_id), tx_time)
        play_url = us.create_playurl(str(user.user_id))
        result = {
            "code": "failed",
            "error_msg": "抢麦失败",
        }
        if user.gender == 1:
            if User2Live.objects.filter(live_id=data["live_id"], state=3).exists():
                return Response(result, status=status.HTTP_200_OK)
            user_live.state = 3
            live_room.play_url_male = play_url
            live_room.save(update_fields=('play_url_male',))
        else:
            if User2Live.objects.filter(live_id=data["live_id"], state=4).exists():
                return Response(result, status=status.HTTP_200_OK)
            user_live.state = 4
            live_room.play_url_female = play_url
            live_room.save(update_fields=('play_url_female',))
        user_live.save(update_fields=('state',))
        us.send_num_to_owner(data["live_id"], live_room.group_id)
        result = {
            "code": "success",
            "play_url": play_url,
            "push_url": push_url,
            "nickname": user.nickname,
            "area": user.area,
            "age": user.age,
            "user_id": str(user.user_id),
            "gender": user.gender,
            "face_url": user.face_url,
        }

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def leave_micro(self, request, *args, **kwargs):
        logger.debug("下麦")
        logger.info(request.GET)
        user_id = request.GET.get('user_id', '')
        live_id = request.GET.get('live_id', '')
        gender = request.GET.get('gender', '')
        if not user_id or not live_id or not gender or not user_id.isdigit() or not live_id.isdigit() or not gender.isdigit():
            logger.info('参数错误（live_id:%s,user_id:%s,gender:%s）' % (live_id, user_id, gender))
            return Response('参数错误（live_id:%s,user_id:%s,gender:%s）' % (live_id, user_id, gender),
                            status=status.HTTP_400_BAD_REQUEST)
        if gender == '2':
            LiveBroadcastRoom.objects.filter(id=live_id).update(play_url_female='')
        elif gender == '1':
            LiveBroadcastRoom.objects.filter(id=live_id).update(play_url_male='')
        else:
            logger.info(gender)
            return Response('参数错误（gender:%s）{1:男，2:女}' % gender, status=status.HTTP_400_BAD_REQUEST)
        User2Live.objects.filter(user_id=user_id, live_id=live_id).update(state=1)

        try:
            live_room = LiveBroadcastRoom.objects.get(pk=live_id)
        except LiveBroadcastRoom.DoesNotExist:
            logger.debug('{} There is no live studio.'.format(user_id))
            return Response({'detail': 'There is no live studio.'}, status=status.HTTP_400_BAD_REQUEST)
        us.send_num_to_owner(live_id, live_room.group_id)
        return Response({"detail": "OK"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def live_end(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        logger.debug('{}直播结束'.format(user.user_id))
        logger.info(data)

        if "live_id" not in data:
            return Response({'detail': 'parameter error.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            User2Live.objects.filter(live_id=data["live_id"]).update(state=0)
        except User2Live.DoesNotExist:
            logger.debug('{} Users are not in the live studio.'.format(user.user_id))
            return Response({'detail': 'Users are not in the live studio'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            live_room = LiveBroadcastRoom.objects.get(pk=data["live_id"])
        except LiveBroadcastRoom.DoesNotExist:
            logger.debug('{} There is no live studio.'.format(user.user_id))
            return Response({'detail': 'There is no live studio.'}, status=status.HTTP_400_BAD_REQUEST)
        live_room.continuous_time += int(datetime.now().timestamp() - live_room.start_time.timestamp())
        live_room.is_live = False
        live_room.play_url_male = ''
        live_room.play_url_female = ''
        live_room.save(update_fields=('is_live', 'play_url_male', 'play_url_female', 'continuous_time'))
        User2Live.objects.filter(live_id=data["live_id"]).update(state=0)
        return Response({"detail": "OK"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def leave_room(self, request, *args, **kwargs):
        user = request.user
        live_id = request.GET.get('live_id', '')
        logger.debug("%s 退出直播间:%s" % (user.user_id, live_id))
        try:
            live_room = LiveBroadcastRoom.objects.get(id=live_id)
        except LiveBroadcastRoom.DoesNotExist:
            logger.info("%s 直播间不存在" % live_id)
            return Response({"detail": "%s 直播间不存在" % live_id}, status=status.HTTP_400_BAD_REQUEST)
        user_live = User2Live.objects.filter(user_id=user.user_id, live_id=live_id).first()
        if not user_live:
            return Response({"detail": "用户与直播间关系不存在，user_id:%s,live_id:%s" % (user.user_id, live_id)},
                            status=status.HTTP_400_BAD_REQUEST)
        if user_live.state == 3:
            live_room.play_url_male = ''
            live_room.save(update_fields=['play_url_male'])
            m = msg['RESET']
            m['content']['user_id'] = str(user.user_id)
            us.send_group_msg(live_room.group_id, m)
        elif user_live.state == 4:
            live_room.play_url_female = ''
            live_room.save(update_fields=['play_url_female'])
            m = msg['RESET']
            m['content']['user_id'] = str(user.user_id)
            us.send_group_msg(live_room.group_id, m)
        user_live.state = 0
        user_live.save(update_fields=['state'])
        us.send_num_to_owner(live_id, live_room.group_id)
        return Response({"detail": "OK"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated],
            authentication_classes=[UserTokenAuthentication])
    def refuse_micro(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        logger.debug("拒绝上麦")
        logger.info(data)
        if "live_id" not in data or not data["live_id"]:
            return Response({'detail': 'parameter error.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_live = User2Live.objects.get(live_id=data["live_id"], user_id=user.user_id)
        except User2Live.DoesNotExist:
            logger.info('{} Users are not in the live studio.'.format(user.user_id))
            return Response({'detail': 'Users are not in the live studio'}, status=status.HTTP_400_BAD_REQUEST)

        user_live.state = 1
        user_live.save(update_fields=('state',))
        us.send_num_to_owner(data["live_id"])
        return Response({"detail": "OK"}, status=status.HTTP_200_OK)


class LiveRoomsView(viewsets.ModelViewSet):
    serializer_class = LiveBroadcastRoomSerializer
    queryset = LiveBroadcastRoom.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    authentication_classes = [UserTokenAuthentication]

    def list(self, request, *args, **kwargs):
        logger.debug('获取直播间列表')
        page = request.GET.get('page', 1)
        if isinstance(page, str) and not page.isdigit():
            page = 1
        page_begin = int(page) * us.PAGE_SIZE - us.PAGE_SIZE
        page_end = us.PAGE_SIZE
        rooms = self.get_queryset().raw(sql['get_live_list'], params=[page_begin, page_end])
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LiveRoomView(viewsets.ModelViewSet):
    serializer_class = LiveRoomSerializer
    queryset = LiveBroadcastRoom.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    authentication_classes = [UserTokenAuthentication]

    def list(self, request, *args, **kwargs):
        logger.debug('获取直播间拉流地址')
        user = request.user
        live_id = request.GET.get('live_id', '')
        try:
            live_room = LiveBroadcastRoom.objects.get(id=live_id)
        except LiveBroadcastRoom.DoesNotExist:
            logger.info("live_id:%s不存在" % live_id)
            return Response("live_id:%s不存在" % live_id, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(live_room, many=False)
        results = serializer.data
        u2l = User2Live.objects.filter(Q(user_id=user.user_id) & ~Q(state=0)).first()
        logger.debug("上次直播间关系%s" % u2l)
        if u2l and u2l.is_host:
            # 大主播异常退出
            logger.debug("大主播异常退出%s" % u2l.id)
            tx_time = us.generate_txtime()
            results['user_type'] = 5
            results['push_url'] = us.create_pushurl(str(user.user_id), tx_time)
            results['num_list'] = us.get_live_people_num(u2l.live_id)
        elif u2l and (u2l.state == 3 or u2l.state == 4):
            # 嘉宾异常退出
            logger.debug("嘉宾异常退出%s" % u2l.id)
            tx_time = us.generate_txtime()
            results['user_type'] = u2l.state
            results['push_url'] = us.create_pushurl(str(user.user_id), tx_time)
            results['num_list'] = []
        # elif u2l and u2l.state == 2:
        #     # 申请上麦中异常退出
        #     logger.debug("申请上麦中异常退出%s" % u2l.id)
        #     results['user_type'] = u2l.state
        #     results['push_url'] = ''
        #     results['num_list'] = []
        else:
            # 普通观众
            logger.debug("普通观众%s" % u2l)
            User2Live.objects.filter(user_id=user.user_id).update(state=0)
            if u2l:
                # 异常退出
                us.send_num_to_owner(u2l.live_id)
            if User2Live.objects.filter(user_id=user.user_id, live_id=live_id).exists():
                User2Live.objects.filter(user_id=user.user_id, live_id=live_id).update(state=1,
                                                                                       last_change=datetime.now())
            else:
                User2Live.objects.create(user_id=user.user_id, live_id=live_id, state=1, last_change=datetime.now())
            us.send_num_to_owner(live_id, live_room.group_id)
            results['user_type'] = 1
            results['push_url'] = ""
            results['num_list'] = []
        return Response(results, status=status.HTTP_200_OK)


class LikeView(viewsets.ModelViewSet):
    serializer_class = LiveRoomSerializer
    queryset = LiveBroadcastRoom.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    authentication_classes = [UserTokenAuthentication]

    def list(self, request, *args, **kwargs):
        logger.debug('获取点赞状态')
        user = request.user
        user_id = request.GET.get('user_id', "")
        con = get_redis_connection()
        like = con.hget(us.QLIVE_HASH_LIKE_NAME, us.QLIVE_HASH_LIKE_FORMAT.format(user.user_id, user_id))
        if like:
            try:
                like = int(like)
            except Exception:
                return Response({"like_state": 0}, status=status.HTTP_200_OK)
            return Response({"like_state": like}, status=status.HTTP_200_OK)
        like = Like.objects.filter(user_id=user.user_id, passive_user_id=user_id).first()
        if like:
            return Response({"like_state": like.like_state}, status=status.HTTP_200_OK)
        return Response({"like_state": 0}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        logger.debug('点赞和取消点赞')
        user = request.user
        data = request.data
        logging.info(data)

        if "user_id" not in data or "like_state" not in data or not data["user_id"].isdigit() or (
                isinstance(data["like_state"], str) and not data["like_state"].isdigit()):
            logging.info({'detail': 'Parameter error'})
            return Response({'detail': 'Parameter error'}, status=status.HTTP_400_BAD_REQUEST)

        con = get_redis_connection()
        like_key = us.QLIVE_HASH_LIKE_FORMAT.format(user.user_id, data["user_id"])
        con.hset(us.QLIVE_HASH_LIKE_NAME, like_key, data["like_state"])
        return Response({"detail": "ok"}, status=status.HTTP_200_OK)


class ConfigsView(viewsets.ModelViewSet):
    serializer_class = ConfigSerializer
    queryset = Config.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    authentication_classes = [UserTokenAuthentication]

    def list(self, request, *args, **kwargs):
        logger.info("获取配置")
        config = self.get_queryset().filter(ienable="1")
        serializer = self.get_serializer(config, many=True)
        data = serializer.data
        res = {
            "PROGRAM_SHARE": [],
            "LIVEROOM_SHARE": []
        }
        for k in data:
            if k['ikey'] == 'BACKGROUND':
                res['BACKGROUND'] = json.loads(k['ival'])
                continue
            if k['ikey'] == 'PROGRAM_SHARE':
                res['PROGRAM_SHARE'].append(json.loads(k['ival']))
                continue
            if k['ikey'] == 'LIVEROOM_SHARE':
                res['LIVEROOM_SHARE'].append(json.loads(k['ival']))
                continue
            res[k['ikey']] = k['ival']
        return Response(res, status=status.HTTP_200_OK)


class PayNotifyView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        '''
        接收微信支付结果接口
        '''
        xml = request.body
        data = ps.wx_lxml2dict(xml)
        logger.debug("收到微信支付结果通知")
        logger.info(data)
        sign_type = data.get('sign_type', 'MD5')
        if not WXPayUtil.is_signature_valid(data=data, key=settings.WEIXINAPP_KEY, sign_type=sign_type):
            return HttpResponse(ps.wx_dict2xml({'return_code': 'FAIL', 'return_msg': '签名失败'}))
        out_trade_no = data.get('out_trade_no', '')
        try:
            order = Order.objects.get(order_id=out_trade_no)
        except Order.DoesNotExist:
            return HttpResponse(ps.wx_dict2xml({'return_code': 'FAIL', 'return_msg': '参数格式校验错误'}))
        try:
            user = User.objects.get(user_id=order.user_id)
        except User.DoesNotExist:
            return HttpResponse(ps.wx_dict2xml({'return_code': 'FAIL', 'return_msg': '参数格式校验错误'}))
        user.gold += order.gold
        user.save(update_fields=['gold'])
        order.state = 1
        order.save(update_fields=['state'])
        return HttpResponse(ps.wx_dict2xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))


class IMNotifyView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        logger.debug("收到IM回调请求")
        logger.info(request.GET)
        logger.info(request.data)
        sdk_app_id = request.GET.get('SdkAppid', '')
        callback_cmd = request.GET.get('CallbackCommand', '')
        result = dict(
            ActionStatus="OK",
            ErrorInfo="",
            ErrorCode=0
        )
        try:
            sdk_app_id = int(sdk_app_id)
        except Exception as e:
            logger.info(e)
            result["ActionStatus"] = "FAIL"
            result["ErrorInfo"] = "SdkAppid Error"
            return Response(result, status=status.HTTP_200_OK)
        if sdk_app_id != us.SDKAPPID:
            result["ActionStatus"] = "FAIL"
            result["ErrorInfo"] = "SdkAppid Error"
            return Response(result, status=status.HTTP_200_OK)
        try:
            ts.cmd[callback_cmd].delay(request.data)
        except Exception as e:
            logger.info(e)
            result["ActionStatus"] = "FAIL"
            result["ErrorInfo"] = "CallbackCommand Error"
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_200_OK)
