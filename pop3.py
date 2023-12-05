import socket

MAX_BUFFER = 3 * 1024 * 1024 + 2048

class POP3Client:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        self.socket.connect((self.server, self.port))
        self.receive_response()

    def send_command(self, command):
        self.socket.send((command + '\n').encode())
        self.receive_response()

    def receive_response(self):
        response = self.socket.recv(MAX_BUFFER).decode()
        #print(response)
        return response

    def login(self, username, password):
        self.send_command(f'USER {username}')
        self.send_command(f'PASS {password}') # useless since password can be randomly typed

    def list_emails(self):
        self.socket.send('LIST\r\n'.encode())
        return self.receive_response()

    def retrieve_email(self, email_number):
        self.socket.send((f'RETR {email_number}\r\n').encode())
        return self.receive_response()

    def close(self):
        self.send_command('QUIT')
        self.socket.close()

# Usage example
if __name__ == "__main__":
    username = "abc@example.com"
    password = "your_password"

    pop3_client = POP3Client("127.0.0.1", 1100)
    pop3_client.login(username, password)
    pop3_client.list_emails()
    print(pop3_client.retrieve_email(13))
    pop3_client.close()
