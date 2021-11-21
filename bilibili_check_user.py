from time import sleep
import threading
import websocket
import zlib
import json

ws_client = websocket.WebSocket()
ws_client.connect("ws://broadcastlv.chat.bilibili.com:2244/sub")
is_quit = False

enter_pack_post = json.dumps({"roomid": 1392204})
enter_pack_header = (len(enter_pack_post) + 16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (7).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
enter_pack = enter_pack_header + enter_pack_post.encode("utf-8")
print(enter_pack)
ws_client.send(enter_pack)
enter_recv_pack = ws_client.recv()
print(enter_recv_pack)

def send_heartbeat_pack():
	while not is_quit:
		print("sending heartbeat pack")
		heartbeat_pack_header = (16).to_bytes(4, byteorder="big") + (16).to_bytes(2, byteorder="big") + (0).to_bytes(2, byteorder="big") + (2).to_bytes(4, byteorder="big") + (1).to_bytes(4, byteorder="big")
		ws_client.send(heartbeat_pack_header)
		sleep(30)

def receive_pack():
	while not is_quit:
		print("listening to server")
		recv_pack = ws_client.recv()
		recv_pack_header = recv_pack[:16]
		recv_pack_get = recv_pack[16:]
		
		if recv_pack:
			print(recv_pack)

t1 = threading.Thread(target = send_heartbeat_pack)
t2 = threading.Thread(target = receive_pack)
t1.setDaemon(True)
t2.setDaemon(True)
t1.start()
t2.start()
#TODO:每30秒发送心跳包，同时要随时接收服务器发来的消息
temp = input()	#按一下回车就退出
is_quit = True
ws_client.close()
