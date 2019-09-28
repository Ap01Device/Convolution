### 亲名片+小程序接口
```
"base_qlive": "http://test.daqinjia.cn/wx/api/qlive"
"token":"d18c8d9db48fcb06cee8083d159c8661c9a65a29"
```
#### 登录小程序
```
POST {{base_qlive}}/qlive_user/login/
Accept:application/json
Content-Type: application/json

Parameter
{
  "appId": "wxca891295c56f2c79",
  "code": ""
}

Response
{
  "status":0,  # 0存在 1不存在
  "token":"",
  "user_id":"",
  "user_sign":"",
  "sdk_app_id":"",
  
  "login_type": 1, # 0 普通登录   1 登录后进直播间
  # 以下，在login_type=1，会返回
  "user_type": 3,  #1普通观众,2申请上麦,3男上麦,4女上麦，5红娘
  "live_room_name": "",  #直播间名称
  "live_id": "",
  "group_id": "",
}
```
#### 创建QLive用户
```
POST {{base_qlive}}/qlive_user/
Accept:application/json
Content-Type: application/json

Parameter
{
  "appId": "wxca891295c56f2c79",
  "code": "",
  "encryptedData": "",
  "iv": ""
}

Response
{
  "token":"",
  "user_id":"",
  "user_sign":"",
  "sdk_app_id":""
}
```

#### 修改用户信息
```
POST {{base_qlive}}/qlive_user/update_userinfo/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "nickname": "",
  "gender": "",
  "age": "",
  "area": "",
  "face_url":""
}

Response
{
    "user_id": "",
    "user_sig": "",
    "user_sig_expired": "",
    "nickname": "",
    "gender": 2,
    "age": 1,
    "face_url": "",
    "area": "",
    "gold": 0,
    "height": 150,
    "is_matchmaker": true,
    "income": 0,
    "last_login_time": null,
    "create_time": "2019-07-24T14:11:37"
}
```


#### 根据userid获取用户信息
```
GET {{base_qlive}}/qlive_user/get_userinfo/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "user_id": "",
}

Response
{
    "user_id": "",
    "user_sig": "",
    "user_sig_expired": null,
    "nickname": "",
    "gender": 2,
    "age": 1,
    "face_url": "",
    "area": "",
    "gold": 0,
    "height": 150,
    "is_matchmaker": true,
    "income": 0,
    "last_login_time": null,
    "create_time": "2019-07-24T14:11:37",
    "rate": "" # 提现汇率
}
```

#### 获取直播列表
```
GET {{base_qlive}}/get_livelist/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json
Parameter
{
  "page": "", #页码 从1开始
}
Response
[
    {
        "id": 1, # 直播间id
        "group_id": "12345678",  # IM群 ID
        "room_name": "hahah",
        "room_image": ""
        "player": {
            "boy":"", # 男头像
            "girl":"" # 女头像
        },
        "audience_count": 2  # 直播间总人数
    }
]
```


#### 获取礼物列表
```
GET {{base_qlive}}/qlive_gift/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "page": "",  # 页码
}

Response
{
  "count": 9,
  "next": "http://localhost:8000/wx/api/qlive/get_giftlist/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "dfafdafsa",
      "image": "",
      "gold": 0,
      "effect": ""
    },
    {
      "id": 2,
      "name": "dafdsafew",
      "image": "",
      "gold": 0,
      "effect": ""
    },...
]
```

#### 获取充值模块
```
GET {{base_qlive}}/qlive_pay/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Response
[{
  "id":"",
  "gold":"",
  "price":""
},{
  "id":"",
  "gold":"",
  "price":""
},...]

```

#### 获取直播间拉流地址及用户信息(用户进入直播间)
```
GET {{base_qlive}}/get_playurl/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json
Parameter
{
  "live_id": "",  # 直播间id
}
Response
{
    "anchor_info": {
        "nickname": "🇨🇳",
        "face_url": "https://wx.qlogo.cn/mmopen/vi_32/Q0j4TwGTfTLI2N2EugEticKmiaTxxc2ThndVbF5eEpXwibsGs2pk3VWhgy6AcNzm9ia4IFKdnNIXZkfYZ0gwATcOnA/132"
    },
    "owner": {
        "play_url": "rtmp://play.qlive.daqinjia.cn/live/75003883",
        "nickname": "考虑考虑看照",
        "area": "310100",
        "age": 27,
        "user_id": "75003883",
        "face_url": "https://images.daqinjia.cn/tmp_f1398a9bede30846dcbd219b0fbc138ae7305634cbe8e8e9.jpg"
    },
    "male": {
        "play_url": "rtmp://play.qlive-test.daqinjia.cn/live/66766865",
        "nickname": "🐷",
        "area": "310100",
        "age": 38,
        "user_id": "66766865",
        "face_url": "https://images.daqinjia.cn/tmp_27cd8ec800bd8c21572d9d4cba4485475f12b18650b39ab4.jpg"
    },
    "female": {
        "play_url": "rtmp://play.qlive.daqinjia.cn/live/10215436",
        "nickname": "hahah",
        "area": "",
        "age": 1,
        "user_id": "10215436",
        "face_url": ""
    },
    "user_type": 3,
    "push_url": "rtmp://push.qlive-test.daqinjia.cn/live/66766865?txSecret=3cfdae996ded60cff821f75a0d38268d&txTime=5d4d4c24",
    "num_list": [
        0,
        1,
        0,
        0
    ]
}
```

#### 获取直播间男(或女)用户信息
```
GET {{base_qlive}}/qlive_user/get_users_info/
Authorization: QLiveToken {{user_token}}
Accept: application/json

Parameter
{
    "live_id":"",
	"gender": 2,
	"page": 2
}

Response
[
    {
      "user_id": "12345678",
      "face_url": "in ea",
      "state": 0
    },
    {
      "user_id": "12345678",
      "face_url": "do culpa minim magna aliqua",
      "state": 0
    },
    {
      "user_id": "12345678",
      "face_url": "fugiat et",
      "state": 1
    },
    {
      "user_id": "12345678",
      "face_url": "eu reprehenderit",
      "state": 1
    },
    {
      "user_id": "12345678",
      "face_url": "in est velit",
      "state": 1
    }
]
```

#### 申请上麦
```
POST {{base_qlive}}/qlive_room/apply_micro/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "live_id": "",  #直播间id
}

Response
{
  'detail': 'OK'
}

```

#### 接受上麦
```
POST {{base_qlive}}/qlive_room/accept_micro/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "live_id": "",  # 直播间id
}

Response
{
  "play_url":"",  # 拉流地址
  "push_url":"",  # 推流地址
  "nickname":"",
  "area":"",
  "age":"",
  "user_id":"",
}
```

#### 用户下麦
```
GET {{base_qlive}}/qlive_room/leave_micro/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "live_id": "",  # 直播间id
  "user_id":"",   # 接受上麦的用户id
  "gender":"",  # 男嘉宾
}

Response
{
  'detail': 'OK'
}
```

#### 直播结束
```
POST {{base_qlive}}/qlive_room/live_end/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
  "live_id": "",  # 直播间id
}

Response
{
  'detail': 'OK'
}
```

#### 送礼物
```
GET {{base_qlive}}/qlive_gift/push_gift/
Authorization: QLiveToken {{user_token}}
Accept: application/json
Parameter
{
  "user_id": "12345678", # 收礼物用户id
  "gift_id": 1, # 礼物id
  "num": 2  # 礼物数量
}
Response
{
  "status": "success",
  "gold": 100,  # 充值的金币
  "income": 200  # 收益
}
```

#### 充值
```
POST {{base_qlive}}/qlive_pay/
Authorization: QLiveToken {{user_token}}
Accept: application/json
Content-Type: application/json
Parameter
{
	"block_id": 2
}
Response
{
  "success":"success",
  "timestamp": "2019-07-30 12:30:00",
  "sign": "asdasfgednkjcn",
  "content": "{}"
}
```

#### 红娘进入房间
```
POST {{base_qlive}}/qlive_room/matchmaker_enter/
Authorization: QLiveToken {{user_token}}
Accept: application/json
Content-Type: application/json

Response
{
  "status": "ok", # ok:正常 failed:被封号
  "user_id": "",
  "live_id":"",  # 直播间id
  "nickname": "",
  "face_url": "",
  "push_url": "",   # 推流地址
  "play_url": "",   # 拉流地址
  "group_id": ""
}
```

#### 普通观众/小主播退出直播间
```
GET {{base_qlive}}/qlive_room/leave_room/
Authorization: QLiveToken {{user_token}}
Accept: application/json
Parameter
{
	"live_id": 2   # 直播间id
}
Response
{
    "detail": "OK"
}
```


#### 用户退出小程序
```
GET {{base_qlive}}/qlive_user/logout/
Authorization: QLiveToken {{user_token}}
Accept: application/json

Response
{
    "detail": "OK"
}
```


#### 用户拒绝上麦
```
POST {{base_qlive}}/qlive_room/refuse_micro/
Authorization: QLiveToken {{user_token}}
Accept: application/json
Parameter
{
	"live_id": 2   # 直播间id
}
Response
{
    "detail": "OK"
}
```


#### 获取配置
```
GET {{base_qlive}}/get_configs/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Response
{
    "PROGRAM_SHARE": [
        {
            "title": "优质好男人都在这里等你！",
            "src": "https://images.daqinjia.cn/qlive/7a0d0740-ba76-11e9-a743-8c89a53fe892.png"
        },
        {
            "title": "单身相亲女士聚集地",
            "src": "https://images.daqinjia.cn/qlive/7a265bfe-ba76-11e9-95a3-8c89a53fe892.png"
        },
        {
            "title": "介绍对象也能赚钱？",
            "src": "https://images.daqinjia.cn/qlive/7a538728-ba76-11e9-a5d8-8c89a53fe892.png"
        },
        {
            "title": "一大波优质相亲者在这里等你",
            "src": "https://images.daqinjia.cn/qlive/7a452f12-ba76-11e9-acbc-8c89a53fe892.png"
        }
    ],
    "LIVEROOM_SHARE": [
        {
            "title": "又有一对情侣在一起了",
            "src": "https://images.daqinjia.cn/qlive/7a4d1e70-ba76-11e9-8d1e-8c89a53fe892.png"
        },
        {
            "title": "介绍对象成功了",
            "src": "https://images.daqinjia.cn/qlive/7a4d1e70-ba76-11e9-8d1e-8c89a53fe892.png"
        },
        {
            "title": "牵线又一次成功，你来吗？",
            "src": "https://images.daqinjia.cn/qlive/7a4d1e70-ba76-11e9-8d1e-8c89a53fe892.png"
        }
    ],
    "INDEX_BANNER": "https://images.daqinjia.cn/qlive/b91f4cdc-b8ee-11e9-a4e5-8c89a53fe892.png",
    "BACKGROUND": {
        "color": "#f69c9a",
        "height": 1954,
        "src": "https://images.daqinjia.cn/qlive/0eace3c6-b9c2-11e9-aec7-8c89a53fe892.png"
    }
}
```



#### 获取用户状态
```
GET {{base_qlive}}/qlive_user/get_user_state/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json
Response
{
    "live_room_name": "sasad",
    "live_id": 1,
    "group_id": "@TGS#a7HEPC7FD",
    "user_type": 1 # 0 没有直播间,1 普通观众,2 申请上麦,3 男上麦,4 女上麦,5大主播
}
```

#### 点赞和取消点赞
```
POST {{base_qlive}}/qlive_like/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
    "user_id": "2",  #被点赞人id
    "like_state": 1,  # 点赞状态 1是点赞 0是取消
}

Response
{
    "detail": "ok",
}
```
#### 获取点赞状态
```
GET {{base_qlive}}/qlive_like/
Authorization: QLiveToken {{user_token}}
Accept:application/json
Content-Type: application/json

Parameter
{
    "user_id": "2",  #被点赞人id
}

Response
{
    "like_state": 1  # 点赞状态 1是点赞 0是取消
}
```