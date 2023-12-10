from socket import *
import time
from datetime import datetime
import os
import hashlib
import base64
import uuid
import mimetypes
import smtplib

FORMAT = 'utf-8'
now = datetime.now()
cur_time = now.strftime("%a, %d-%b-%Y %H:%M:%S")
max_size_file = 35 * 1024 * 1024  + 2048# 35 MB

class SMTPClient:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.connect()
    
    def generate_msg_id(self, from_addr):
        domain = from_addr.split('@')[1]
        msg_id = str(uuid.uuid4())
        msg_id = f"Message ID:<{msg_id}@{domain}>"
        return msg_id

    def generate_mime_boundary(self):
        seed = str(time.time())
        input_dat = seed.encode(FORMAT) + os.urandom(16)

        hash_obj = hashlib.sha256(input_dat)
        hash_val = hash_obj.hexdigest()

        mime_boundary = f'----MIMEBoundary_{hash_val[:16]}'
        return mime_boundary

    def encode_file(self, file_path):
        with open(file_path, 'rb') as file:
            raw_file = file.read()
            encode_file = base64.b64encode(raw_file).decode('utf-8')
            msg = f"{encode_file}\r\n"
        return msg

    def mime_format(self, subject, msg, from_addr, to_addr, cc, bcc, attachments=None):
        to_header = "To: "
        cc_header = "Cc: "
        bcc_header = "Bcc: "
        # Assuming To, Cc & Bcc are list
        for addr in to_addr:
            to_header += f"<{addr}> "
        for addr in cc:
            cc_header += f"<{addr}> "
        for addr in bcc:
            bcc_header += f"<{addr}> "
        
        mime_boundary = self.generate_mime_boundary()
        mime_type, encoding = mimetypes.guess_type(msg)
        
        if attachments:
            mime_msg = f"""
From: <{from_addr}>
{to_header}
{cc_header}
{bcc_header}
Subject: {subject}
{self.generate_msg_id(from_addr)}
Date: {cur_time}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{mime_boundary}"
Content-Language: EN

--{mime_boundary}
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: {encoding}

{msg}\r\n
"""

            for attach in attachments:
                mime_type, encoding = mimetypes.guess_type(attach['filename'])
                mime_msg += f"""
--{mime_boundary}
Content-Type: {mime_type}
Content-Disposition: attachment; filename="{attach['filename']}"
Content-Transfer-Encoding: base64
"""
                mime_msg += self.encode_file(attach['file_path'])
            mime_msg += f"--{mime_boundary}"
        else:
            mime_msg = f"""
From: <{from_addr}>
{to_header}
{cc_header}
{bcc_header}
Subject: {subject}
{self.generate_msg_id(from_addr)}
Date: {cur_time}
MIME-Version: 1.0
Content-Language: EN

Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: {encoding}

{msg}
"""
        return mime_msg + '\r\n.'

    def connect(self):
        self.socket.connect((self.server, self.port))
        self.receive_response()

    def send_command(self, command):
        self.socket.send((command + '\r\n').encode())
        self.receive_response()

    def receive_response(self):
        response = self.socket.recv(1024).decode()
        print(response)

    def login(self):
        self.send_command('EHLO example.com')

    def send_mail(self, sender, to, cc, bcc, subject, body, attachments=None):
        recipients = []
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        if to:
            recipients.extend(to)
        self.send_command(f'MAIL FROM: <{sender}>')
        for recipient in recipients:
            self.send_command(f'RCPT TO: <{recipient}>')
        self.send_command('DATA')
        self.send_command(f'{self.mime_format(subject, body, sender, to, cc, bcc, attachments)}')
        self.send_command('QUIT')

    def close(self):
        self.send_command('QUIT')
        self.socket.close()

"""# Usage example
if __name__ == "__main__":
    sender = "teacher@testing.com"
    recipient = ["your_email@example.com", "abc@example.com"]
    subject = "Test Email"
    body = "This is the 3rd test email sent using a simple Python SMTP client."
    attachments = [
    {'filename': 'config.html', 'file_path': 'config.html'}
    ,{'filename': 'B.txt', 'file_path': 'B.txt'}
    ,{'filename': 'socket Mail.zip', 'file_path': 'socket Mail.zip'}
]

    smtp_client = SMTPClient("127.0.0.1", 2500)
    smtp_client.login()
    smtp_client.send_mail(sender, [], recipient, [], subject, body, attachments)
    smtp_client.close()"""