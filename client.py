import socket
import threading


def receive_messages(client_socket):
    """
    Receive broadcast messages from the server in a separate thread.
    """
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("\n[Server] Connection closed by server.")
                break

            message = data.decode("utf-8")
            print(f"\n[Chat] {message}")
            print("Enter your message: ", end="", flush=True)
        except Exception as e:
            print(f"\n[Error] Receive failed: {e}")
            break


def start_client(server_host="127.0.0.1", server_port=8080):
    """
    Start a chat client and connect to the server.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_host, server_port))
        print(f"[Info] Connected to server {server_host}:{server_port}")
        print("Type your message and press Enter. Type 'exit' to quit.\n")

        # start thread to receive broadcast messages
        receiver_thread = threading.Thread(
            target=receive_messages, args=(client_socket,), daemon=True
        )
        receiver_thread.start()

        # send user input to server
        while True:
            try:
                message = input("Enter your message: ").strip()
                if not message:
                    continue
                if message.lower() == "exit":
                    break
                client_socket.sendall(message.encode("utf-8"))
            except Exception as e:
                print(f"[Error] Send failed: {e}")
                break

    except Exception as e:
        print(f"[Error] Could not connect to server: {e}")
    finally:
        client_socket.close()
        print("[Info] Disconnected from server.")


if __name__ == "__main__":
    # local testing
    start_client(server_host="127.0.0.1", server_port=8080)
