import base64
import os
import socket
import ssl
import json
from datetime import datetime
import imghdr
from Image import Image


HOST = 'test.yandex.ru'
PORT = 465


def request(user_socket, msg_request):
    user_socket.send((msg_request + '\n').encode('utf-8'))
    recv_data = user_socket.recv(65535)
    return recv_data


def generate_message(file_path: str, user_from, to, message, dir_name) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    current = datetime.now()
    boundary = "divide"
    headers = [
        f'Date: {current.strftime("%d/%m/%y")}',
        f'From: {user_from}',
        f'To: {to}',
        f'Subject: {message}',
        "MIME-Version: 1.0",
        "Content-Type: multipart/mixed;",
        f"  boundary={boundary}",
        '',
    ]

    pictures = []
    for file in os.listdir(dir_name):
        filetype = imghdr.what(f"{dir_name}\\{file}")

        with open(f"{dir_name}\\{file}", "rb") as pic:
            pictures.append(Image(base64.b64encode(pic.read()).decode(), file, filetype))

    message_body = [
        f"--{boundary}",
        "Content-Type: text/html",
        '',
        f"{content}",
        f"--{boundary}"
    ]

    for i, picture in enumerate(pictures):
        message_body.append("Content-Disposition: attachment;")
        message_body.append(f"  filename=\"{picture.filename}\"")
        message_body.append("Content-Transfer-Encoding: base64")
        message_body.append(f"Content-Type: image/{picture.filetype};")
        message_body.append(f"	name=\"{picture.filename}\"")
        message_body.append("")
        message_body.append(f"{picture.encoded}")
        if i != len(pictures) - 1:
            message_body.append(f"--{boundary}")
            continue
        message_body.append(f"--{boundary}--")

    headers_str = '\n'.join(headers)
    message_str = '\n'.join(message_body)
    message = f"{headers_str}\n{message_str}\n.\n"
    print(message)
    return message


def main():
    with open('password.json', 'r', encoding='utf-8') as f1, \
            open("config.json", 'r', encoding='utf-8') as f2:
        password = json.load(f1)
        config = json.load(f2)
        subject_message = config['Subject']
        user_name_from = config['From']
        user_name_to = config['To']
        directory = config['Directory']
        password = password['password']

        ssl_contex = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_contex.check_hostname = False
        ssl_contex.verify_mode = ssl.CERT_NONE

        with socket.create_connection((HOST, PORT)) as sock:
            with ssl_contex.wrap_socket(sock, server_hostname=HOST) as client:
                print(client.recv(1024))
                print(request(client, f'EHLO {user_name_from}'))  #

                base64login = base64.b64encode(user_name_from.encode()).decode()
                base64password = base64.b64encode(password.encode()).decode()

                print(request(client, 'AUTH LOGIN'))
                print(request(client, base64login))
                print(request(client, base64password))
                print(request(client, f'MAIL FROM:{user_name_from}'))
                print(request(client, f"RCPT TO:{user_name_to}"))
                print(request(client, 'DATA'))
                print(request(client, generate_message("msg.txt", user_name_from, user_name_to, subject_message, directory)))


if __name__ == "__main__":
    main()
