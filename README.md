# TCP Chat (How to Run)

- `server.py` – starts the chat server  
- `client.py` – connects to the server and sends/receives messages  

---

## 1. Requirements

- Python 3.8+ installed  
- No extra packages needed (`socket` and `threading` are in the standard library)

---

## 2. Start the Server

1. Open a terminal.

2. Go to the folder that contains `server.py`:

   ```bash
   cd path/to/your/project
   ```

3. Run:

   ```bash
   python3 server.py
   ```

You should see something like:

```text
[Info] Server started, listening on 0.0.0.0:8080
```

Keep this terminal open. This is your running server.

---

## 3. Start a Client (Same Machine)

1. Open **another** terminal window.

2. Go to the same folder

3. Run:

   ```bash
   python3 client.py
   ```

* Type a message and press **Enter** → it will be sent to the server
* Type `exit` → the client will disconnect and close

---

## 4. Start Multiple Clients

To simulate multiple users:

1. Keep the server running.
2. Open a **third**, **fourth**, … terminal window.
3. In each one, run:

   ```bash
   cd path/to/your/project
   python client.py
   ```
   
Now all clients are connected to the same server:

* Anything typed in one client will appear in the others.
* When a client types `exit`, they leave the chat.

---
