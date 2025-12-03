# Socket Chat / Simple FTP (How to Run)

- `server.py` - starts the server (control channel on 8080, per-transfer data sockets)
- `client.py` - connects to the server; supports LS / GET / PUT / EXIT
- Files stored on server under `server_files/`; downloads saved locally to `client_downloads/`

---

## 1. Requirements

- Python 3.8+ installed
- No extra packages needed (`socket`, `threading` are stdlib)

---

## 2. Start the Server

1. Open a terminal and go to the project folder:

   ```bash
   cd path/to/Socket-Chat
   ```

2. Run:

   ```bash
   python server.py
   ```

You should see:

```
[Info] Server started, listening on 0.0.0.0:8080
```

Keep this terminal open. The server opens a short-lived data port for each LS/GET/PUT.

---

## 3. Start a Client (Same Machine)

1. Open another terminal in the same folder.
2. Run:

   ```bash
   python client.py
   ```

Commands at the `ftp>` prompt:

- `LS` – list files on the server (`server_files/`)
- `GET <filename>` – download; saved to `client_downloads/<filename>`
- `PUT <path-to-file>` – upload local file; stored in `server_files/`
- `EXIT` – disconnect

---

## 4. Start Multiple Clients

1. Keep the server running.
2. Open more terminals and run `python client.py` in each.
3. Use LS/GET/PUT from any client; uploads appear in `server_files/` and can be downloaded by others.

---

## 5. Different Machines

- Start `server.py` on the host and note its IP.
- Edit the defaults in `client.py` (at the bottom) or add CLI args if desired, then run the client from other machines on the same network.
- Ensure the server machine allows inbound on the chosen port (default 8080).
