#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#==============================================================================
#     FileName: sign_util.py
#         Desc: sign utils for signing and validating
#      License: GPL
#       Author: Steve Lemuel
#        Email: wlemuel@hotmail.com
#      Version: 0.0.1
#   LastChange: 2019-06-18 10:52:30
#    CreatedAt: 2019-06-18 10:27:34
#==============================================================================
"""
from hashlib import md5, sha256
import datetime


class SignUtil(object):
    SALT = 'Qlive@Daqinjiacn!'
    VALID_DURATION = 3600

    @classmethod
    def sign(cls, timestamp, content):
        raw = (timestamp + cls.SALT + content).encode('utf-8')
        return md5(sha256(raw).hexdigest().encode('utf-8')).hexdigest()

    @classmethod
    def sign_validate(cls, timestamp, sign, content):
        current_time = datetime.datetime.now()
        stamp_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        delta = datetime.timedelta(seconds=cls.VALID_DURATION)

        if current_time - stamp_time > delta or \
           stamp_time - current_time > delta:
            return False

        return cls.sign(timestamp, content) == sign
