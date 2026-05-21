from socketserver import BaseRequestHandler, ThreadingTCPServer


class Handler(BaseRequestHandler):

    def handle(self) -> None:
        address, pid = self.client_address
        print(f'{address} connected!')
        while True:
            data = self.request.recv(1024)

            if len(data) <= 0:
                print(f'{address}close!')
                break
            print(f'receive data: {data.decode()}')
            self.request.sendall('response'.encode())


if __name__ == '__main__':
    server = ThreadingTCPServer(('192.168.201.131', 8000), Handler)
    print("Listening")
    server.serve_forever()

