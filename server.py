import socket
import threading

# store active client sockets
client_sockets = []
# lock to protect shared data in multithreaded context
lock = threading.Lock()

def broadcast(message, sender_socket=None):
    """
    Broadcast a message to all connected clients except the sender.
    """
    to_remove = []
    with lock:
        for client in client_sockets:
            if sender_socket is not None and client is sender_socket:
                continue
            try:
                client.sendall(message.encode("utf-8"))
            except Exception as e:
                print(f"[Error] Broadcast failed: {e}")
                to_remove.append(client)

        # remove broken sockets after broadcasting
        for client in to_remove:
            if client in client_sockets:
                client_sockets.remove(client)


def handle_client(client_socket, client_address):
    """
    Handle messages from a single client in a dedicated thread.
    """
    user_id = f"User_{client_address[1]}"
    print(f"[Info] Client connected: {client_address} as {user_id}")

    # add client to global list
    with lock:
        client_sockets.append(client_socket)

    # send welcome message
    welcome_msg = (
        f"Welcome to the chat! You are {user_id}.\n"
        "Type 'exit' to leave the chat."
    )
    try:
        client_socket.sendall(welcome_msg.encode("utf-8"))
    except Exception as e:
        print(f"[Error] Failed to send welcome message: {e}")

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                # client closed connection
                print(f"[Info] {user_id} disconnected (no data).")
                break

            message = data.decode("utf-8").strip()
            if message.lower() == "exit":
                print(f"[Info] {user_id} requested to exit.")
                break

            print(f"[Message] {user_id}: {message}")
            broadcast(f"{user_id}: {message}", sender_socket=client_socket)

    except Exception as e:
        print(f"[Error] Exception in handle_client for {user_id}: {e}")

    finally:
        with lock:
            if client_socket in client_sockets:
                client_sockets.remove(client_socket)
        client_socket.close()
        print(f"[Info] Connection closed for {user_id}")
        # Optional: notify others
        broadcast(f"*** {user_id} has left the chat. ***")


def start_server(host="0.0.0.0", port=8080):
    """
    Start the TCP chat server.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow quick restart on same port
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen(10)
    server_socket.settimeout(1.0) # set timeout to allow shutdown
    print(f"[Info] Server started, listening on {host}:{port}")
    print("[Info] Press Ctrl+C to stop the server.")

    try:
        while True:
            try:
                client_socket, addr = server_socket.accept()
            except socket.timeout:
                continue
            print(f"[Info] Accepted connection from {addr[0]}:{addr[1]}")
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, addr),
                daemon=True,
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[Info] Server is shutting down...")
    finally:
        server_socket.close()
        print("[Info] Server socket closed.")


if __name__ == "__main__":
    start_server()
