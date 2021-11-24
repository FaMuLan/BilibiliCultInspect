from time import sleep
from urllib.request import urlopen
import threading
import websocket
import zlib
import brotli
import json

setting_file = open("setting.json", mode="r", encoding="UTF-8")
setting_json = json.loads(setting_file.read())
#用户配置文件设置
ws_client = websocket.WebSocket()
ws_client.connect("ws://broadcastlv.chat.bilibili.com:2244/sub")
is_quit = False

enter_pack_post = json.dumps({"roomid": setting_json["roomid"], "clientver": "1.5.10.1", "type": 2, "platform": "web"})
enter_pack_header = (len(enter_pack_post) + 16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (7).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
enter_pack = enter_pack_header + enter_pack_post.encode("utf-8")
ws_client.send(enter_pack)
enter_recv_pack = ws_client.recv()

def inspect_user(uid):
	follow = []
	page = 1;
	while True:
		follow_url = urlopen("https://api.bilibili.com/x/relation/followings?vmid={0}&pn={1}".format(uid, page))
		follow_text = follow_url.read()
		follow_json = json.loads(follow_text)
		if follow_json["code"] == 0:
			total_follow = follow_json["data"]["total"]
			for i in follow_json["data"]["list"]:
				follow.append(i["mid"])
			if page * 50 >= total_follow:
				break
			page += 1
		else:
			break
	return follow



def send_heartbeat_pack():
	while not is_quit:
		heartbeat_pack_header = (16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (2).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
		ws_client.send(heartbeat_pack_header)
		sleep(30)

def get_text(pack):
	operation = int.from_bytes(pack[8:12], "big")
	if operation == 5:
		return pack[16:].decode("UTF-8")
	return None

def split_pack(pack):
	pack_size = int.from_bytes(pack[:4], "big")
	pack_total = []
	protocol_version = int.from_bytes(pack[6:8], "big")
	if protocol_version == 2:
		pack_total += split_pack(zlib.decompress(pack[16:]))
	elif protocol_version == 3:
		pack_total += split_pack(brotli.decompress(pack[16:]))
	#一个数据包套多个小数据包的情况
	elif len(pack) > pack_size:
		pack_total.append(pack[:pack_size])
		pack_total += split_pack(pack[pack_size:])
	#多个数据包的情况
	else:
		pack_total.append(pack)
	return pack_total

def receive_pack():
	while not is_quit:
		recv_pack = ws_client.recv()
		recv_pack = split_pack(recv_pack)
		for i in recv_pack:
			recv_text = get_text(i)
			if recv_text:
				recv = json.loads(recv_text)
				if recv["cmd"] == "INTERACT_WORD":
					print("uid: ", recv["data"]["uid"], "name: ", recv["data"]["uname"])
					follow = inspect_user(recv["data"]["uid"])
					for i in setting_json["inspect_following"]:
						if follow.count(i["uid"]):
							print(i["notification"])


t1 = threading.Thread(target = send_heartbeat_pack)
t2 = threading.Thread(target = receive_pack)
t1.setDaemon(True)
t2.setDaemon(True)
t1.start()
t2.start()
temp = input()	#按一下回车就退出
is_quit = True
ws_client.close()
