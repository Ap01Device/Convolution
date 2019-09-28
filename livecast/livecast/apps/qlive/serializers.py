import logging
import re

from django.db import connection

from rest_framework import serializers
from rest_framework import exceptions
from .models import User, LiveBroadcastRoom, User2Live, Gift, PayModel, Config
from .constants import SQL_TEMPLATE_QLIVE as sql

logger = logging.getLogger()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = "__all__"
        exclude = ["open_id", 'app_id', 'session_key']

    user_id = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return str(obj.user_id)

    def validate_nickname(self, attrs):
        if not isinstance(attrs, str) or not attrs:
            raise exceptions.ValidationError("昵称错误:%s" % attrs)
        return attrs

    def validate_gender(self, attrs):
        if attrs not in [1, 2, '1', '2']:
            raise exceptions.ValidationError("性别错误:%s" % attrs)
        return attrs

    def validate_age(self, attrs):
        if not (isinstance(attrs, int) or (isinstance(attrs, str) and attrs.isdigit())):
            raise exceptions.ValidationError("年龄错误:%s" % attrs)
        return attrs

    def validate_face_url(self, attrs):
        url_complie = re.compile('(http|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?')
        if not url_complie.match(attrs):
            raise exceptions.ValidationError("头像地址错误:%s" % attrs)
        return attrs

    def validate_area(self, attrs):
        if not (isinstance(attrs, int) or (isinstance(attrs, str) and attrs.isdigit())):
            raise exceptions.ValidationError("地区code错误:%s" % attrs)
        return attrs


class UserStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'nickname', 'face_url', 'state']

    state = serializers.SerializerMethodField()

    def get_state(self, obj):
        return obj.state


class LiveBroadcastRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveBroadcastRoom
        fields = ["id", "group_id", "room_name", "room_image", "player", "audience_count"]

    audience_count = serializers.SerializerMethodField()
    room_name = serializers.SerializerMethodField()
    room_image = serializers.SerializerMethodField()
    player = serializers.SerializerMethodField()

    def get_audience_count(self, obj):
        return obj.num

    def get_room_name(self, obj):
        cursor = connection.cursor()
        cursor_sql = sql['get_room_name'] % obj.id
        cursor.execute(cursor_sql)
        room = cursor.fetchone()
        if room:
            room_name = room[0]
        else:
            room_name = ""
        return room_name

    def get_room_image(self, obj):
        cursor = connection.cursor()
        cursor_sql = sql['get_room_image'] % obj.id
        cursor.execute(cursor_sql)
        room = cursor.fetchone()
        if room:
            room_image = room[0]
        else:
            room_image = ""
        return room_image

    def get_player(self, obj):
        player = {}
        cursor = connection.cursor()
        cursor_sql = sql['get_player_face'] % obj.id
        cursor.execute(cursor_sql)
        players = cursor.fetchall()
        for p in players:
            if p[1] == 2:
                player['girl'] = p[0]
            elif p[1] == 1:
                player['boy'] = p[0]
        if player.get('boy', '') and player.get('girl', ''):
            return [player.get('girl', ''), player.get('boy', '')]
        elif not player.get('boy', '') and not player.get('girl', ''):
            male = Config.objects.filter(ikey='avatar_url_male').values('ival').first()
            female = Config.objects.filter(ikey='avatar_url_female').values('ival').first()
            return [female['ival'], male['ival']]
        elif not player.get('boy', '') and player.get('girl', ''):
            male = Config.objects.filter(ikey='avatar_url_male').values('ival').first()
            return [player.get('girl', ''), male['ival']]
        else:
            female = Config.objects.filter(ikey='avatar_url_female').values('ival').first()
            return [player.get('boy', ''), female['ival']]


class LiveRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveBroadcastRoom
        fields = ["owner", 'male', 'female', 'anchor_info']

    anchor_info = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    male = serializers.SerializerMethodField()
    female = serializers.SerializerMethodField()

    def get_anchor_info(self, obj):
        users = User.objects.raw(sql['get_anchor_info'], params=(obj.id,))
        if users:
            user = users[0]
        else:
            return {}
        anchor = dict(
            nickname=user.nickname,
            face_url=user.face_url
        )
        return anchor

    def get_owner(self, obj):
        raw_sql = sql['get_play_url'].format(',qlbr.play_url_owner play_url')
        users = User.objects.raw(raw_sql, params=(1, 1, obj.id))
        if users:
            user = users[0]
        else:
            return {}
        owner = dict(
            play_url=user.play_url,
            nickname=user.nickname,
            area=user.area,
            age=user.age,
            user_id=str(user.user_id),
            face_url=user.face_url
        )
        return owner

    def get_male(self, obj):
        raw_sql = sql['get_play_url'].format(',qlbr.play_url_male play_url')
        users = User.objects.raw(raw_sql, params=(0, 3, obj.id))
        if users:
            user = users[0]
        else:
            return {}
        owner = dict(
            play_url=user.play_url,
            nickname=user.nickname,
            area=user.area,
            age=user.age,
            user_id=str(user.user_id),
            face_url=user.face_url
        )
        return owner

    def get_female(self, obj):
        raw_sql = sql['get_play_url'].format(',qlbr.play_url_female play_url')
        users = User.objects.raw(raw_sql, params=(0, 4, obj.id))
        if users:
            user = users[0]
        else:
            return {}
        owner = dict(
            play_url=user.play_url,
            nickname=user.nickname,
            area=user.area,
            age=user.age,
            user_id=str(user.user_id),
            face_url=user.face_url
        )
        return owner


class User2LiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User2Live
        fields = "__all__"


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = "__all__"


class PayModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayModel
        fields = "__all__"


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['ikey', 'ival']
