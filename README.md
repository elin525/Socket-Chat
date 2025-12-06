````markdown
# Network Programming Project – Multi-Client FTP Server

A small FTP-style system written in Python.  
One server accepts many clients at the same time. Clients can list files, upload and download files.  
We also deployed the server on AWS EC2 so different laptops can connect over the Internet.

---

## 1. Team

- Jane Lin – janelin25@csu.fullerton.edu  
- Kathy Nguyen – KathyLNguyen@csu.fullerton.edu  
- Abhinav Sharma – abhiinaav820@gmail.com  
- Jennifer Arellano – arellanojennifer8@gmail.com  
- Trisha Prajapati – trishap04@csu.fullerton.edu  

---

## 2. Technology

- **Language:** Python 3 (3.8+)
- **Libraries:** only Python standard library  
  (`socket`, `threading`, `os`, `sys`, etc.)
- **Platforms tested:** macOS, Linux, AWS EC2 (Amazon Linux)

---

## 3. Files in This Project

All files are under one folder:

- `server.py`  
  TCP server. Listens on a control port (8080).  
  Uses threads to serve multiple clients.  
  Opens a short-lived data port for each `LS`, `GET`, `PUT`.

- `client.py`  
  Terminal client. Connects to the server and supports commands:

  ```text
  LS                 # list files on server
  GET <filename>     # download file
  PUT <filename>     # upload file
  EXIT               # close connection
````

* Runtime folders:

  * `server_files/` – server-side storage for uploaded files
  * `client_downloads/` – client-side folder for downloaded files

---

## 4. How to Run (Local or Same LAN)

### 4.1 Requirements

* Python 3 installed on server and clients.
* Put `server.py`, `client.py`, README in the same folder, e.g.:

```text
Network-Programming/
  server.py
  client.py
  README.md
```

### 4.2 Start the Server

On the machine that will act as the server:

```bash
cd path/to/Network-Programming
python3 server.py --host 0.0.0.0 --port 8080
```

If you omit arguments, it also defaults to `0.0.0.0:8080`.
Keep this terminal open.

### 4.3 Start a Client

On the same machine (or another machine in the same LAN):

```bash
cd path/to/Network-Programming
python3 client.py --host <SERVER_IP> --port 8080
```

Examples:

* Same machine: `--host 127.0.0.1`
* Another machine in LAN: `--host 192.168.x.x` (server’s LAN IP)

At the `ftp>` prompt you can type:

```text
LS
PUT hello.txt
GET hello.txt
EXIT
```

To show **concurrency**, open two client terminals:

* Client A: `PUT message.txt`
* Client B (at the same time): `LS` and `GET hello.txt`

The server stays responsive and both clients finish their commands.

---

## 5. How to Run on AWS EC2 (Used in Our Testing)

We deployed the server on an Amazon Linux EC2 instance so two physical laptops
could connect from different places.

### 5.1 EC2 Setup (summary)

* AMI: Amazon Linux
* Instance type: t2.micro / t3.micro
* Security Group inbound rules:

  * SSH: TCP 22 from our IP (for management)
  * All TCP: ports `0–65535` from `0.0.0.0/0`

### 5.2 Upload Code and Start Server

From local machine:

```bash
scp -i ~/.ssh/socket-chat-key.pem server.py client.py \
  ec2-user@<EC2_PUBLIC_IP>:~/Network-Programming/
```

SSH into EC2:

```bash
ssh -i ~/.ssh/socket-chat-key.pem ec2-user@<EC2_PUBLIC_IP>
cd ~/Network-Programming
mkdir -p server_files
python3 server.py --host 0.0.0.0 --port 8080
```

### 5.3 Connect from Two Different Laptops

On each laptop:

```bash
cd path/to/Network-Programming
python3 client.py --host <EC2_PUBLIC_IP> --port 8080
```

Both laptops were connected to the same EC2 server and could upload / download
at the same time.
