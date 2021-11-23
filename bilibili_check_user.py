from time import sleep
import threading
import websocket
import zlib
import brotli
import json

ws_client = websocket.WebSocket()
ws_client.connect("ws://broadcastlv.chat.bilibili.com:2244/sub")
is_quit = False

enter_pack_post = json.dumps({"roomid": 174142, "clientver": "1.5.10.1", "type": 2, "platform": "web"})
enter_pack_header = (len(enter_pack_post) + 16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (7).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
enter_pack = enter_pack_header + enter_pack_post.encode("utf-8")
ws_client.send(enter_pack)
enter_recv_pack = ws_client.recv()

def send_heartbeat_pack():
	while not is_quit:
		heartbeat_pack_header = (16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (2).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
		ws_client.send(heartbeat_pack_header)
		sleep(30)

def receive_pack():
	def get_text(pack):
		pack_header = pack[:16]
		pack_get = pack[16:]
		operation = int.from_bytes(pack_header[8:12], "big")
		protocol_version = int.from_bytes(pack_header[6:8], "big")
		if protocol_version == 0:
			if operation == 5:
				return pack_get.decode("UTF-8")
			return None
		elif protocol_version == 2:
			child_pack = zlib.decompress(pack_get)
			return get_text(child_pack)
			#需要用zlib解压出数据包，再把那个数据包按照协议版本解压一遍，需要另外写个函数并递归（搁这套娃干什么在那难怪我手机用这玩意儿这么卡）
		elif protocol_version == 3:
			child_pack = brotli.decompress(pack_get)
			return get_text(child_pack)
			#没有遇到或者感知不到这种情况，先闲置不管
		return None

	def split_pack(pack):
		pack_size = int.from_bytes(pack[:4], "big")
		pack_total = [pack[0:pack_size]]
		if len(pack[pack_size:]) > 0:
			pack_second = pack[pack_size:]
			pack_total += split_pack(pack_second)
		return pack_total

	while not is_quit:
		recv_pack = ws_client.recv()
		recv_pack = split_pack(recv_pack)
		for i in recv_pack:
			recv_text = get_text(i)
			if recv_text:
				recv_text = recv_text.split(">")	#临时方案，要是把完整的JSON一分为二了就再改.jpg
				#TODO: 这脑瘫B站有的时候会在一个数据包里面塞两段JSON过来，需要进行切割再进行解析
				recv = json.loads(recv_text[0])
				if recv["cmd"] == "INTERACT_WORD":
					print("uid: ", recv["data"]["uid"], "name: ", recv["data"]["uname"])


t1 = threading.Thread(target = send_heartbeat_pack)
t2 = threading.Thread(target = receive_pack)
t1.setDaemon(True)
t2.setDaemon(True)
t1.start()
t2.start()
temp = input()	#按一下回车就退出
is_quit = True
ws_client.close()
