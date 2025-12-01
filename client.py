import socket
import os

BUFFER_SIZE = 4096
ENCODING = "utf-8"


def read_line(sock: socket.socket) -> str:
    """
    Reads a line from the socket (until newline '\\n'), removes the trailing newline, and returns the string.
    """
    line_bytes = b""
    while True:
        ch = sock.recv(1)
        if not ch:
            # Connection closed
            raise ConnectionError("Connection closed while reading line.")
        line_bytes += ch
        if ch == b"\n":
            break
    return line_bytes.decode(ENCODING).rstrip("\n")


def read_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Reads exactly 'num_bytes' from the socket.
    """
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed during data transfer.")
        data += chunk
    return data


def handle_ls(sock: socket.socket) -> None:
    """
    Handles the LS command: requests a file listing from the server.
    """
    sock.sendall(b"LS\n")
    # Assume the server sends the entire listing at once
    listing = sock.recv(BUFFER_SIZE).decode(ENCODING).rstrip("\n")
    if not listing:
        print("[Server] No files returned.")
    else:
        print("[Server] Files on server:")
        print(listing)


def handle_get(sock: socket.socket, filename: str) -> None:
    """
    Handles the GET command: downloads a file from the server.
    Protocol: client sends 'GET <filename>', server responds with 'OK\\n', 
    'FILESIZE <bytes>\\n', and then the raw file bytes.
    """
    if not filename:
        print("[Error] Usage: GET <filename>")
        return

    # 1. Send command
    sock.sendall(f"GET {filename}\n".encode(ENCODING))

    # 2. Read status line
    status = read_line(sock)
    if not status.startswith("OK"):
        print(f"[Server] {status}")
        return

    # 3. Read FILESIZE line
    size_line = read_line(sock)
    if not size_line.startswith("FILESIZE"):
        print(f"[Error] Unexpected response from server: {size_line}")
        return

    try:
        filesize = int(size_line.split()[1])
    except (IndexError, ValueError):
        print(f"[Error] Invalid FILESIZE line: {size_line}")
        return

    print(f"[Info] Downloading {filename} ({filesize} bytes)...")

    # 4. Read file content
    file_bytes = read_exact(sock, filesize)

    # 5. Save to current directory
    target_name = os.path.basename(filename)
    with open(target_name, "wb") as f:
        f.write(file_bytes)

    print(f"[Success] Download complete: {target_name}")


def handle_put(sock: socket.socket, filename: str) -> None:
    """
    Handles the PUT command: uploads a local file to the server.
    Protocol: client sends 'PUT <filename>', server responds with 'OK\\n', 
    client sends 'FILESIZE <bytes>\\n', client sends raw file bytes, server responds with final 'OK\\n'.
    """
    if not filename:
        print("[Error] Usage: PUT <filename>")
        return

    if not os.path.isfile(filename):
        print(f"[Error] Local file not found: {filename}")
        return

    filesize = os.path.getsize(filename)
    basename = os.path.basename(filename)

    # 1. Send command
    sock.sendall(f"PUT {basename}\n".encode(ENCODING))

    # 2. Wait for server OK
    status = read_line(sock)
    if not status.startswith("OK"):
        print(f"[Server] {status}")
        return

    # 3. Send FILESIZE line
    sock.sendall(f"FILESIZE {filesize}\n".encode(ENCODING))

    # 4. Send file content
    print(f"[Info] Uploading {basename} ({filesize} bytes)...")
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)

    # 5. Wait for final server OK
    final_status = read_line(sock)
    if final_status.startswith("OK"):
        print(f"[Success] File uploaded: {basename}")
    else:
        print(f"[Error] Server reported error after upload: {final_status}")


def start_client(server_host: str = "127.0.0.1", server_port: int = 8080) -> None:
    """
    Simplified single-connection FTP client.
    Supported Commands: LS, GET <filename>, PUT <filename>, EXIT.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((server_host, server_port))
        except OSError as e:
            print(f"[Error] Could not connect to {server_host}:{server_port} - {e}")
            return

        print(f"[Info] Connected to {server_host}:{server_port}")

        # Read welcome message from server
        try:
            welcome = sock.recv(BUFFER_SIZE).decode(ENCODING)
            if welcome:
                print("-" * 40)
                print(welcome.rstrip("\n"))
                print("-" * 40)
        except Exception as e:
            print(f"[Error] Failed to read welcome message: {e}")

        print("\nCommands:")
        print("  LS")
        print("  GET <filename>")
        print("  PUT <filename>")
        print("  EXIT\n")

        while True:
            try:
                user_input = input("ftp> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Info] Exiting client.")
                break

            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            try:
                if cmd == "LS":
                    handle_ls(sock)
                elif cmd == "GET":
                    handle_get(sock, arg)
                elif cmd == "PUT":
                    handle_put(sock, arg)
                elif cmd == "EXIT":
                    sock.sendall(b"EXIT\n")
                    print("[Info] Closing connection...")
                    break
                else:
                    print("[Error] Unknown command. Use LS, GET, PUT, or EXIT.")
            except ConnectionError as e:
                print(f"[Error] Connection lost: {e}")
                break
            except Exception as e:
                print(f"[Error] Unexpected error: {e}")
                break

        print("[Info] Disconnected.")


if __name__ == "__main__":
    start_client(server_host="127.0.0.1", server_port=8080)
