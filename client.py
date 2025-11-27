import socket
import protocol
import logging

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345


def print_menu():
    """מדפיס את התפריט"""
    print("\n" + "=" * 50)
    print("1. DIR <path>")
    print("2. DELETE <filepath>")
    print("3. COPY <src> <dest>")
    print("4. EXECUTE <program>")
    print("5. TAKE_SCREENSHOT")
    print("6. SEND_PHOTO")
    print("7. EXIT")
    print("=" * 50)


def print_response(response):
    """מדפיס תשובה מהשרת בצורה מעוצבת"""
    if response.startswith("SUCCESS:"):
        print("✓ Success:", response[8:])
        logging.info("Success response: %s", response[8:])
    elif response.startswith("ERROR:"):
        print("✗ Error:", response[6:])
        logging.warning("Error response: %s", response[6:])
    else:
        print("Response:", response)
        logging.info("Response: %s", response)


def main():
    """פונקציה ראשית של הלקוח"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        logging.info("Attempting to connect to server %s:%s", SERVER_IP, SERVER_PORT)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("Connected To The Server", SERVER_IP, ":", SERVER_PORT)
        logging.info("Successfully connected to server")

        print_menu()

        while True:
            command = input("\nPlease Enter A Valid Command: ").strip()

            if not command:
                logging.warning("Empty command entered")
                continue

            logging.info("User entered command: %s", command)

            # שליחת הפקודה לשרת
            protocol.send_message(client_socket, command)

            # טיפול מיוחד ב-SEND_PHOTO
            if command.upper().startswith("SEND_PHOTO"):
                logging.info("Receiving photo from server")
                protocol.receive_photo(client_socket)
            else:
                # קבלת תשובה רגילה
                response = protocol.receive_message(client_socket)
                if response:
                    print_response(response)

                    # אם זו פקודת EXIT, נסגור את החיבור
                    if command.upper() == "EXIT":
                        logging.info("EXIT command executed, closing connection")
                        break
                else:
                    logging.warning("No response received, connection may be closed")
                    print("The Connection Was Closed")
                    break

    except Exception as e:
        logging.error("Client error: %s", e)
        print("Error:", e)
    finally:
        client_socket.close()
        logging.info("Client connection closed")
        print("The Connection Was Closed")


if __name__ == "__main__":
    # Logging configuration
    logging.basicConfig(
        filename="client.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
    )

    main()