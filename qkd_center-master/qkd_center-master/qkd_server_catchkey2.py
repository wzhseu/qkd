from socketserver import BaseRequestHandler, ThreadingTCPServer
import time


class Handler(BaseRequestHandler):

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
            log = current_time + " " + data.decode() + "\n"
            print(log)
            with open("log2.txt", "a", encoding="utf-8") as f:
                f.write(log)

            self.request.sendall('response'.encode())


if __name__ == '__main__':
    server2 = ThreadingTCPServer(('10.38.174.164', 8002), Handler)
    print("Listening")
    with open("log3.txt", "w") as f:
        f.write("---- qkd-server ----\n")
    server2.serve_forever()

