SQL_TEMPLATE_QLIVE = {
    # 获取直播间列表
    'get_live_list': "SELECT qlbr.id,qlbr.image,qlbr.group_id,qlbr.is_live,qlbr.play_url_owner,qlbr.play_url_male,qlbr.play_url_female,qu2l.num FROM (SELECT id,image,group_id,is_live,start_time,play_url_owner,play_url_male,play_url_female FROM qlive_livebroadcastroom WHERE is_live=1 LIMIT %s,%s) qlbr LEFT JOIN (SELECT live_id,COUNT(1) num FROM qlive_user2live WHERE state!=0 GROUP BY live_id) qu2l on qlbr.id=qu2l.live_id ORDER BY qu2l.num DESC,qlbr.start_time DESC",
    # 获取拉流地址
    "get_play_url": "SELECT qu.id,qu.user_id,qu.nickname,qu.face_url,qu.area,qu.age{} FROM qlive_user2live qu2l LEFT JOIN qlive_user qu ON qu.user_id=qu2l.user_id LEFT JOIN qlive_livebroadcastroom qlbr ON qu2l.live_id=qlbr.id WHERE qu2l.is_host=%s AND qu2l.state=%s AND qlbr.id=%s",
    # 根据直播间获取用户头像和昵称
    "get_anchor_info": "SELECT qu.id,qu.nickname,qu.face_url FROM qlive_user qu WHERE qu.user_id=(SELECT user_id FROM qlive_user2live WHERE is_host=1 AND live_id=%s)",
    # 根据id获取直播间名称
    "get_room_name": "SELECT qu.nickname FROM (SELECT user_id FROM qlive_user2live WHERE is_host=1 AND live_id=%s) qu2l LEFT JOIN qlive_user qu ON qu.user_id=qu2l.user_id",
    # 根据id获取直播间图片
    "get_room_image": "SELECT qu.face_url FROM (SELECT user_id FROM qlive_user2live WHERE is_host=1 AND live_id=%s) qu2l LEFT JOIN qlive_user qu ON qu.user_id=qu2l.user_id",
    # 获取直播间嘉宾头像
    "get_player_face": "SELECT qu.face_url,qu.gender FROM (SELECT user_id FROM qlive_user2live WHERE is_host=0 AND live_id=%s AND (state=3 OR state=4)) qu2l LEFT JOIN qlive_user qu ON qu.user_id=qu2l.user_id",
    # 查询%s房间的性别为%s的信息
    "get_user_info": "SELECT qu.id,qu.user_id,qu.face_url,qu.nickname,qu2l.state FROM qlive_user qu LEFT JOIN qlive_user2live qu2l ON qu.user_id=qu2l.user_id WHERE qu2l.is_host=0 AND (qu2l.state=1 OR qu2l.state=2) AND qu2l.live_id=%s AND qu.gender=%s ORDER BY qu2l.state ASC,qu2l.last_change ASC LIMIT %s,%s",
    # 获取直播间人数（live_id）
    "get_live_people_num": "SELECT COUNT(CASE WHEN qu2l.state=2 AND qu.gender=1 THEN 1 END) male_up,COUNT(CASE WHEN qu2l.state!=0 AND qu.gender=1 AND qu2l.is_host=0 THEN 1 END) male_all,COUNT(CASE WHEN qu2l.state=2 AND qu.gender=2 THEN 1 END) female_up,COUNT(CASE WHEN qu2l.state!=0 AND qu.gender=2 AND qu2l.is_host=0 THEN 1 END) female_all FROM qlive_user2live qu2l LEFT JOIN qlive_user qu ON qu2l.user_id=qu.user_id WHERE qu2l.live_id=%s",
    # 根据IM群id获取主播user_id
    "get_host_id_by_group": "SELECT qu2l.user_id,qu2l.live_id FROM qlive_user2live qu2l LEFT JOIN qlive_livebroadcastroom qlbr ON qlbr.id=qu2l.live_id WHERE qlbr.group_id='%s' AND qu2l.is_host=1",
    # 根据主播id查IM群id
    "get_group_id": "SELECT qlbr.id ,qlbr.group_id FROM qlive_livebroadcastroom qlbr RIGHT JOIN (SELECT live_id FROM qlive_user2live WHERE is_host=1 AND user_id=%s) qu2l ON qu2l.live_id=qlbr.id",
}
MSG_TEMPLATE_QLIVE = {
    # c2c
    # 邀请上麦
    "INVITE": {"content": {"group_id": ""}, "type": "invite"},

    # 同意 / 拒绝上麦  "accept" / "reject"
    "RESPONSE": {"content": {"group_id": "", "data": ""}, "type": "response"},

    # 小主播被动下麦
    "KICKOUT": {"content": {"group_id": ""}, "type": "kickout"},

    # 通知红娘直播间人数 [男上麦/男全部/女上麦/女全部]  (后台发给红娘)
    "NUM": {"content": {"group_id": "", "num_list": []}, "type": "num"},

    # 群消息
    # 更新直播地址/小主播异常退出   content_type值为off时，只传user_id
    "RESET": {
        "content": {
            "content_type": "off",  # "on"：上麦 "off"：下麦
            "user_id": "",
            "play_url": "",
            "nickname": "",
            "area": "",
            "age": "",
            "face_url": "",
            "gender": "",
        },
        "type": "reset"
    },

    # 送礼物
    "GIFT": {"content": {"gift_id": "", "gift_title": "", "gift_num": "", "gift_image": ""}, "type": "gift"},

    # 发布评论
    "MESSAGE": {"content": "", "type": "message"},

    # 大主播退出直播间 / 大主播异常退出直播间
    "OVER": {"content": "", "type": "over"}
}
