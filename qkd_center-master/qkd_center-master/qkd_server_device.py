from socketserver import BaseRequestHandler, ThreadingTCPServer
import time


class Handler(BaseRequestHandler):
    # 处理客户端连接请求
    def handle(self) -> None:
        address, pid = self.client_address
        print(f'{address} connected!')

        while True:
            data = self.request.recv(1024)

            if len(data) <= 0:
                print(f'{address}close!')
                break

            # print(f'receive data: {data.decode()}')
            now = int(time.time())
            timeArr = time.localtime(now)
            current_time = time.strftime("%y-%m-%d-%H:%M:%S", timeArr)
            # f.write(current_time + "\n")
            # f.write(data.decode())
            # f.write("\n")
            log = current_time + "\n" + data.decode() + "\n"
            print(log)
            with open("log.txt", "a", encoding="utf-8") as f:
                f.write(log)

            self.request.sendall('response'.encode())


if __name__ == '__main__':
    # 创建一个多线程的 TCP 服务器，监听指定地址和端口
    server = ThreadingTCPServer(('10.38.174.164', 8000), Handler)
    print("Listening")
    with open("log.txt", "w") as f:
        f.write("---- qkd-server ----\n")
    # 启动服务器，无限循环处理客户端连接
    server.serve_forever()

