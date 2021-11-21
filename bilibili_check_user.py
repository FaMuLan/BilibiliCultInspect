from time import sleep
import threading
import websocket
import zlib
import brotli
import json

ws_client = websocket.WebSocket()
ws_client.connect("ws://broadcastlv.chat.bilibili.com:2244/sub")
is_quit = False

enter_pack_post = json.dumps({"roomid": 1006525, "clientver": "1.5.10.1", "type": 2, "platform": "web"})
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
	def get_pack(pack):
		pack_header = pack[:16]
		pack_size = int.from_bytes(pack[:4], "big")
		pack_get = pack[16:pack_size]
		operation = int.from_bytes(pack_header[8:12], "big")
		protocol_version = int.from_bytes(pack_header[6:8], "big")
		if protocol_version == 0:
			if operation == 5:
				return pack_get.decode("UTF-8")
			return None
		elif protocol_version == 1:
			new_population = int.from_bytes(pack_get, "big")
			print("population_change: " + (new_population - population))
			population = new_population
			return None
		elif protocol_version == 2:
			inner_pack = zlib.decompress(pack_get)
			return get_pack(inner_pack)
			#需要用zlib解压出数据包，再把那个数据包按照协议版本解压一遍，所以才需要另外写个函数并递归（搁这套娃干什么在那难怪我手机用这玩意儿这么卡）
		elif protocol_version == 3:
			inner_pack = brotli.decompress(pack_get)
			return get_pack(inner_pack)
			#没有遇到这种情况，先闲置不管
		
	while not is_quit:
		recv_pack = ws_client.recv()
		recv_text = get_pack(recv_pack)
		if recv_text != None:
			recv = json.loads(recv_text)
			if recv["cmd"] != "STOP_LIVE_ROOM_LIST" and recv["cmd"] != "WIDGET_BANNER" and ["cmd"] != "NOTICE_MSG":
				print(recv_text)


t1 = threading.Thread(target = send_heartbeat_pack)
t2 = threading.Thread(target = receive_pack)
t1.setDaemon(True)
t2.setDaemon(True)
t1.start()
t2.start()
temp = input()	#按一下回车就退出
is_quit = True
ws_client.close()
