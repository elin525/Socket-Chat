import socket
import threading
import os

BUFFER_SIZE = 4096

#creates a folder to store files
serverFolder = "server_files"
os.makedirs(serverFolder, exist_ok=True)

# store active client sockets
client_sockets = []
# lock to protect shared data in multithreaded context
lock = threading.Lock()


def read_line(sock: socket.socket) -> str:
    """
    Read a single line (ending with '\\n') from a socket.
    """
    data = b""
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed while reading line")
        data += chunk
        if chunk == b"\n":
            break
    return data.decode("utf-8").rstrip("\n")


def open_data_listener() -> tuple[socket.socket, int]:
    """
    Open a data socket listener on an ephemeral port and return (socket, port).
    """
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(("0.0.0.0", 0))  # 0 lets OS pick a free port
    data_socket.listen(1)
    port = data_socket.getsockname()[1]
    return data_socket, port

def broadcast(message, sender_socket=None):
    """
    Broadcast a message to all connected clients except the sender.
    """
    to_remove = []
    with lock:
        for client in client_sockets:
            if client == sender_socket:
                continue
            try:
                client.sendall(message.encode("utf-8"))
            except Exception as e:
                print(f"[Error] Broadcast failed: {e}")
                to_remove.append(client)

        # remove broken sockets after broadcasting
        for dead in to_remove:
            if dead in client_sockets:
                client_sockets.remove(dead)


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
        "Available Commands:\n"
        "LS               List Files\n"
        "GET <filename>   Download File\n"
        "PUT <filename>   Upload File\n"
        "EXIT             Leave chat\n"
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
            print(f"[Message] {user_id}: {message}")
            
            splitParts = message.split()
            if len(splitParts) == 0:
                continue
            
            theCommand= splitParts[0].upper()
            
            #first if type the ls command
            if theCommand == "LS":
                files = os.listdir(serverFolder)
                listing = "\n".join(files) + "\n" if files else "No Files Available\n"

                data_listener, data_port = open_data_listener()
                print(f"[Debug] LS data port opened: {data_port}")
                client_socket.sendall(b"OK\n")
                client_socket.sendall(f"DATAPORT {data_port}\n".encode())

                try:
                    data_conn, _ = data_listener.accept()
                    print(f"[Debug] LS data connection accepted on port {data_port}")
                    with data_conn:
                        data_conn.sendall(listing.encode("utf-8"))
                finally:
                    data_listener.close()
                
            #Get command to download a file
            elif theCommand == "GET":
                if len(splitParts) != 2:
                    client_socket.sendall(b"ERROR: GET <filename>\n")
                    continue
                
                filename = splitParts[1]
                filepath = os.path.join(serverFolder, filename)
                
                #lets check if the file exist
                if not os.path.exists(filepath):
                    client_socket.sendall(b"ERROR: File Not Found\n")
                    continue
                
                filesize = os.path.getsize(filepath)

                data_listener, data_port = open_data_listener()
                print(f"[Debug] GET data port opened: {data_port} for {filename}")
                client_socket.sendall(b"OK\n")            
                client_socket.sendall(f"FILESIZE {filesize}\n".encode())   
                client_socket.sendall(f"DATAPORT {data_port}\n".encode())

                try:
                    data_conn, _ = data_listener.accept()
                    print(f"[Debug] GET data connection accepted on port {data_port} for {filename}")
                    with data_conn, open(filepath, "rb") as f:
                        for chunk in iter(lambda: f.read(BUFFER_SIZE), b""):
                            data_conn.sendall(chunk)
                    print(f"[INFO] SENT FILE: {filename}")
                finally:
                    data_listener.close()
                
            #when typed PUT it should upload file
            elif theCommand == "PUT":
                if len(splitParts) != 2:
                    client_socket.sendall(b"ERROR: PUT <filename>\n")
                    continue
                
                filename = splitParts[1]
                filepath = os.path.join(serverFolder, filename)

                data_listener, data_port = open_data_listener()
                print(f"[Debug] PUT data port opened: {data_port} for {filename}")
                client_socket.sendall(b"OK\n")
                client_socket.sendall(f"DATAPORT {data_port}\n".encode())

                try:
                    data_conn, _ = data_listener.accept()
                    print(f"[Debug] PUT data connection accepted on port {data_port} for {filename}")
                    with data_conn:
                        try:
                            sizeInfo = read_line(data_conn)
                        except ConnectionError:
                            client_socket.sendall(b"ERROR: Connection lost during FILESIZE\n")
                            continue

                        if not sizeInfo.startswith("FILESIZE"):
                            client_socket.sendall(b"ERROR: Expected FILESIZE <bytes>\n")
                            continue
                        
                        try:
                            filesize = int(sizeInfo.split()[1])
                        except (IndexError, ValueError):
                            client_socket.sendall(b"ERROR: Invalid FILESIZE value\n")
                            continue

                        print(f"[INFO] Receiving file {filename} ({filesize} bytes)")
                        
                        leftOver = filesize
                        with open(filepath, "wb") as f:
                            while leftOver > 0:
                                chunk = data_conn.recv(min(BUFFER_SIZE, leftOver))
                                if not chunk:
                                    break
                                f.write(chunk)
                                leftOver -= len(chunk)
                        
                        if leftOver == 0:
                            client_socket.sendall(b"OK\n")
                            print(f"[INFO] Saved file: {filename}")
                        else:
                            client_socket.sendall(b"ERROR Incomplete file received\n")
                finally:
                    data_listener.close()
                    
                #exit command 
            elif theCommand == "EXIT":
                 print(f"[Info] {user_id} requested to exit.")
                 break
             
            else:
                 client_socket.sendall(b"ERROR: Command is Unknown\n")
    
    finally:
        with lock:
            if client_socket in client_sockets:
                client_sockets.remove(client_socket)
        client_socket.close()
        print(f"[Info] Connection closed for {user_id}")
        #notify others
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
