PHOTO_SAVE_PATH = 'received_screenshot.jpg'

def send_message(client_socket, message):
    """שולח הודעה עם פרוטוקול [אורך]:[נתונים]"""
    try:
        message_bytes = message.encode()
        length = str(len(message_bytes)).zfill(4)
        full_message = length.encode() + b':' + message_bytes
        client_socket.send(full_message)
    except Exception as e:
        print("Error With Sending A Message:", e)


def receive_message(client_socket):
    """מקבל הודעה לפי הפרוטוקול"""
    try:
        length = client_socket.recv(4).decode()
        if not length:
            return None
        client_socket.recv(1)  # קריאת ה-':'
        message = client_socket.recv(int(length)).decode()
        return message
    except Exception as e:
        print("Error With Receiving A Message:", e)
        return None

def receive_photo(sock):
    """מקבל תמונה מהשרת"""
    try:
        length = sock.recv(10).decode()
        sock.recv(1)  # קריאת ה-':'
        photo_data = b''
        bytes_to_receive = int(length)

        while len(photo_data) < bytes_to_receive:
            chunk = sock.recv(min(4096, bytes_to_receive - len(photo_data)))
            if not chunk:
                break
            photo_data += chunk

        with open(PHOTO_SAVE_PATH, 'wb') as f:
            f.write(photo_data)

        print("The Photo Was Sent To The Client:", PHOTO_SAVE_PATH)
    except Exception as e:
        print("Error With Receiving The Photo:", e)