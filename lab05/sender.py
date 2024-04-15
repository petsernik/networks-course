import socket
import ssl
import os
import sys
import mimetypes

from enum import Enum

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import base64

class MessageType(Enum):
    TEXT = 1
    HTML = 2

    @staticmethod
    def getTypeByFile(file):
        file_extension = mimetypes.guess_extension(mimetypes.guess_type(file)[0]) if file else None
        if file_extension in (".html", ".htm"):
            return MessageType.HTML
        else:
            return MessageType.TEXT


class SmtpSender:
    def __init__(self):
        self.login = os.environ.get("LOGIN")
        self.password = os.environ.get("PASSWORD")
        self.host = os.environ.get("HOST")
        self.port = int(os.environ.get("PORT", 587))
        self.sender_email = f"{self.login}@{self.host}"
        self.server = f"smtp.{self.host}"
        self.error_message = "[ERROR] UNEXPECTED ANSWER AFTER "
        self.smtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_context = ssl.create_default_context()

    def safety_receive(self, action_description, expected_code):
        while True:
            recv = self.smtp_socket.recv(2048)
            recv = recv.decode()
            if recv[:len(str(expected_code))] != str(expected_code):
                raise RuntimeError(self.error_message + action_description + "\r\n RECEIVED: " + recv)
            print("RECEIVED: " + recv)
            return

    def connect(self):
        self.smtp_socket.connect((self.server, self.port))
        self.safety_receive("CONNECT", 220)    
    
    @staticmethod   
    def extract(file):
        body = ''
        with open(file, "r") as f:
            body = f.read()
        type = MessageType.getTypeByFile(file)
        return body, type
    
    def send_email(self, recipient, subject, message_file, attachment_file=None):
        self.connect()

        ehlo = f"EHLO {self.login}.{self.host}\r\n"
        self.smtp_socket.send(ehlo.encode())
        self.safety_receive("ID", 250)

        start_tls = "STARTTLS\r\n"
        self.smtp_socket.send(start_tls.encode())
        self.safety_receive("START TLS", 220)

        with self.ssl_context.wrap_socket(self.smtp_socket, server_hostname=self.server) as secured_socket:
            self.smtp_socket = secured_socket

            secured_socket.send(ehlo.encode())
            self.safety_receive("RE-ID", 250)

            auth_login = "AUTH LOGIN\r\n"
            secured_socket.send(auth_login.encode())
            self.safety_receive("AUTH LOGIN", 334)

            login_data = base64.b64encode(bytes(self.login, "utf-8")).decode("utf-8") + "\r\n"
            secured_socket.send(login_data.encode())
            self.safety_receive("SENT LOGIN", 334)

            password_data = base64.b64encode(bytes(self.password, "utf-8")).decode("utf-8") + "\r\n"
            secured_socket.send(password_data.encode())
            self.safety_receive("SENT PASSWORD", 235)

            mail_from = "MAIL FROM:<" + self.sender_email + ">\r\n"
            secured_socket.send(mail_from.encode())
            self.safety_receive("SENT FROM", 250)

            rcpt_to = "RCPT TO:<" + recipient + ">\r\n"
            secured_socket.send(rcpt_to.encode())
            self.safety_receive("SENT RECIPIENT", 250)

            secured_socket.send("DATA\r\n".encode())
            self.safety_receive("START SENDING DATA", 354)

            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient
            message["Subject"] = subject

            message_body, message_type = SmtpSender.extract(message_file)

            print(f"MESSAGE_TYPE: {message_type}\r\n")

            if message_type == MessageType.TEXT:
                message.attach(MIMEText(message_body))
            else:
                message.attach(MIMEText(message_body, "html"))

            if attachment_file:
                with open(attachment_file, "rb") as file:
                    attachment = file.read()
                message.attach(MIMEImage(attachment))

            data_to_send = message.as_string() + "\r\n.\r\n"
            secured_socket.sendall(data_to_send.encode())
            self.safety_receive("SENT MAIL", 250)

            quit = "QUIT\r\n"
            secured_socket.send(quit.encode())
            self.safety_receive("QUIT", 221)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: LOGIN=... PASSWORD=... HOST=... PORT=... python3 sender.py <recipient> <subject> <message_file> [attachment_file]")
        sys.exit(1)

    recipient = sys.argv[1]
    subject = sys.argv[2]
    message_file = sys.argv[3]
    attachment_file = sys.argv[4] if len(sys.argv) > 4 else None

    sender = SmtpSender()
    sender.send_email(recipient, subject, message_file, attachment_file)
