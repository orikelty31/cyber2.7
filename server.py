import socket
import protocol
import os
import glob
import shutil
import subprocess
import pyautogui
import logging

IP = '0.0.0.0'
PORT = 12345
SCREENSHOT_PATH = 'screen.jpg'


def handle_dir(path):
    """מטפל בפקודת DIR"""
    try:
        logging.info("DIR command received for path: %s", path)

        if not os.path.exists(path):
            logging.warning("Path does not exist: %s", path)
            return "ERROR:Path does not exist"

        files = glob.glob(os.path.join(path, '*.*'))
        if not files:
            logging.info("Directory is empty: %s", path)
            return "SUCCESS:Directory is empty"

        file_names = [os.path.basename(z) for z in files]
        logging.info("Found %s files in directory: %s", len(file_names), path)
        return "SUCCESS:" + ";".join(file_names)
    except Exception as e:
        logging.error("Error in handle_dir: %s", e)
        return "ERROR:" + str(e)


def handle_delete(filepath):
    """מטפל בפקודת DELETE"""
    try:
        logging.info("DELETE command received for file: %s", filepath)

        if not os.path.exists(filepath):
            logging.warning("File not found: %s", filepath)
            return "ERROR:File not found"

        os.remove(filepath)
        logging.info("File deleted successfully: %s", filepath)
        return "SUCCESS:File deleted successfully"
    except Exception as e:
        logging.error("Error in handle_delete: %s", e)
        return "ERROR:" + str(e)


def handle_copy(source, dest):
    """מטפל בפקודת COPY"""
    try:
        logging.info("COPY command received. Source: %s, Dest: %s", source, dest)

        if not os.path.exists(source):
            logging.warning("Source file not found: %s", source)
            return "ERROR:Source file not found"

        shutil.copy(source, dest)
        logging.info("File copied successfully from %s to %s", source, dest)
        return "SUCCESS:File copied successfully"
    except Exception as e:
        logging.error("Error in handle_copy: %s", e)
        return "ERROR:" + str(e)


def handle_execute(program_path):
    """מטפל בפקודת EXECUTE"""
    try:
        logging.info("EXECUTE command received for program: %s", program_path)

        if not os.path.exists(program_path):
            logging.warning("Program not found: %s", program_path)
            return "ERROR:Program not found"

        subprocess.Popen(program_path)
        logging.info("Program executed successfully: %s", program_path)
        return "SUCCESS:Program executed successfully"
    except Exception as e:
        logging.error("Error in handle_execute: %s", e)
        return "ERROR:" + str(e)


def handle_screenshot():
    """מטפל בפקודת TAKE_SCREENSHOT"""
    try:
        logging.info("TAKE_SCREENSHOT command received")

        image = pyautogui.screenshot()
        image.save(SCREENSHOT_PATH)

        logging.info("Screenshot saved successfully to: %s", SCREENSHOT_PATH)
        return "SUCCESS:Screenshot saved to " + SCREENSHOT_PATH
    except Exception as e:
        logging.error("Error in handle_screenshot: %s", e)
        return "ERROR:" + str(e)


def handle_send_photo(client_socket):
    """מטפל בפקודת SEND_PHOTO"""
    try:
        logging.info("SEND_PHOTO command received")

        if not os.path.exists(SCREENSHOT_PATH):
            logging.warning("Screenshot not found at: %s", SCREENSHOT_PATH)
            protocol.send_message(client_socket, "ERROR:Screenshot not found")
            return None

        with open(SCREENSHOT_PATH, 'rb') as o:
            photo_data = o.read()

        # שליחה בפורמט מיוחד לבינארי
        length = str(len(photo_data)).zfill(10)
        client_socket.send(length.encode() + b':')
        client_socket.send(photo_data)

        logging.info("Photo sent successfully. Size: %s bytes", len(photo_data))
        print("The Photo Was Sent")
    except Exception as e:
        logging.error("Error in handle_send_photo: %s", e)
        protocol.send_message(client_socket, "ERROR:" + str(e))


def handle_client_command(command, client_socket):
    """מעבד פקודה מהלקוח"""
    parts = command.split(' ', 1)
    cmd = parts[0].upper()

    logging.info("Processing command: %s", cmd)

    if cmd == "DIR":
        if len(parts) < 2:
            logging.warning("DIR command missing path parameter")
            protocol.send_message(client_socket, "ERROR:Missing path parameter")
            return "OK"
        response = handle_dir(parts[1])
        protocol.send_message(client_socket, response)

    elif cmd == "DELETE":
        if len(parts) < 2:
            logging.warning("DELETE command missing file parameter")
            protocol.send_message(client_socket, "ERROR:Missing file parameter")
            return "OK"
        response = handle_delete(parts[1])
        protocol.send_message(client_socket, response)

    elif cmd == "COPY":
        if len(parts) < 2:
            logging.warning("COPY command missing parameters")
            protocol.send_message(client_socket, "ERROR:Missing parameters")
            return "OK"
        params = parts[1].split(' ', 1)
        if len(params) < 2:
            logging.warning("COPY command missing destination parameter")
            protocol.send_message(client_socket, "ERROR:Missing destination parameter")
            return "OK"
        response = handle_copy(params[0], params[1])
        protocol.send_message(client_socket, response)

    elif cmd == "EXECUTE":
        if len(parts) < 2:
            logging.warning("EXECUTE command missing program parameter")
            protocol.send_message(client_socket, "ERROR:Missing program parameter")
            return "OK"
        response = handle_execute(parts[1])
        protocol.send_message(client_socket, response)

    elif cmd == "TAKE_SCREENSHOT":
        response = handle_screenshot()
        protocol.send_message(client_socket, response)

    elif cmd == "SEND_PHOTO":
        handle_send_photo(client_socket)
        return "PHOTO WAS SENT"

    elif cmd == "EXIT":
        logging.info("EXIT command received")
        protocol.send_message(client_socket, "SUCCESS:Goodbye")
        return "EXIT"

    else:
        logging.warning("Unknown command received: %s", cmd)
        protocol.send_message(client_socket, "ERROR:Unknown command")

    return "OK"


def handle_client(client_socket, client_address):
    """מטפל בלקוח בודד"""
    print("New Client Connected:", client_address)
    logging.info("New client connected: %s", client_address)

    try:
        while True:
            command = protocol.receive_message(client_socket)
            if not command:
                logging.info("No command received, closing connection")
                break

            print("Command Was Recived:", command)
            result = handle_client_command(command, client_socket)

            if result == "EXIT":
                logging.info("Client requested exit")
                break

    except Exception as e:
        logging.error("Client socket error: %s", e)
        print("Client Socket Error:", e)

    finally:
        client_socket.close()
        logging.info("Connection with %s was closed", client_address)
        print("The Connection With", client_address, "Was Closed")


def main():
    """פונקציה ראשית של השרת"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(5)
        print("The Server Is Listening On", IP, ":", PORT)
        logging.info("Server started successfully on %s:%s", IP, PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            logging.info("Accepted connection from: %s", client_address)
            handle_client(client_socket, client_address)

    except Exception as e:
        logging.error("Server error: %s", e)
        print("Error:", e)
    finally:
        server_socket.close()
        logging.info("Server was closed")
        print("The Server Was Closed")


if __name__ == "__main__":
    # Logging configuration
    logging.basicConfig(
        filename="server.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
    )


    with open("cyber1.txt", "w") as f:
        f.write("hello")
    with open("cyber2.txt", "w") as f:
        f.write("data")

    success= handle_dir(".")
    if success.startswith("SUCCESS:"):
        success = True
    else:
        success = False
    assert success is True, "Assertation FAILED"

    assert handle_copy("cyber2.txt", "cyber3.txt") == "SUCCESS:File copied successfully", "Assertation FAILED"

    assert handle_delete("cyber3.txt") == "SUCCESS:File deleted successfully", "Assertation FAILED"
    assert handle_delete("cyber2.txt") == "SUCCESS:File deleted successfully", "Assertation FAILED"
    assert handle_delete("cyber1.txt") == "SUCCESS:File deleted successfully", "Assertation FAILED"

    assert handle_screenshot() == "SUCCESS:Screenshot saved to screen.jpg", "Assertation FAILED"

    logging.info("All Assert Tests Passed")


    main()