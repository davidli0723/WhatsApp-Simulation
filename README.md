# WhatsApp-Simulation

This project implements a custom messaging and video communication application in Python using a client-server model. Multiple clients communicate concurrently via TCP for text messages (reliable) and UDP for video file streaming (low latency). Features include user authentication, private and group chats, and video file uploads, simulating platforms like WhatsApp or Messenger.

## Features

- **User Authentication** – Secure login for multiple users.  
- **Private Chat** – One-to-one messaging between participants.  
- **Group Chat** – Messaging with multiple participants simultaneously.  
- **Video File Uploads** – Send and receive video files using UDP for low-latency streaming.  
- **Concurrent Communication** – Supports multiple clients communicating at the same time.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/WhatsApp-Simulation.git
   cd WhatsApp-Simulation

2. Run the Server
    Open a terminal and execute:

    ```bash
    python3 Server.py <server_IP> <server_port>
    # Example:
    python3 Server.py localhost 12000

3. open another terminal and Run the Client.py:
    ```bash
    python3 client.py server_IP server_port client_udp_server_port
    python3 Client.py localhost 12000 6000

> **Note:** You should open multiple terminals and run multiple instances of `Client.py` 
to simulate multiple users messaging simultaneously.