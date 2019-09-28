# -*- coding: utf-8 -*-
# @Author  : itswcg
# @File    : connectionfactory
# @Time    : 19-4-17 下午2:24
# @Blog    : https://blog.itswcg.com
# @github  : https://github.com/itswcg

from django_redis.pool import ConnectionFactory


class DecodeConnectionFactory(ConnectionFactory):
    """解决python3 django-redis 默认输出bytes类型"""

    def get_connection(self, params):
        params['decode_responses'] = True
        return super().get_connection(params)
