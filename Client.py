"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: David LI
"""
from socket import *
import sys
import threading
import time
import os

#Server would be running on the same host as Client
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 Client3.py SERVER_IP SERVER_PORT UDP_PORT======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
UDPPort = int(sys.argv[3])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)
connection = True
command = "Enter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo, /logout):"
login = False
receiver_udp = ''
receiver_IP_address = ''
username = ""
active_user_list = {}

# sets for received message without specific handle
direct_receive_msg_set = {
    # possible received messages for /activeuser command
    "No other active user",

    # possible received messages for /msgto command
    "message sent at",
    "Error usage, format = /msgto receiver message\n",
    "User not found, please check with /activeuser\n",

    # possible received messages for /creategroup command
    "Please enter at least one more active users.\n",
    "group already exist, please try another name",
    "members are inactive, please check with /activeuser command",
    "Group chat created",

    # possible received messages for /joingroup command
    "Error usage, format = /joingroup Groupname\n",
    "Failed to create the group chat",
    "Joined the group chat",
    "you already in the group",
    "you are not group member",
    "groupname not found",

    # possible received messages for /groupmsg command
    "Error usage, format = /groupmsg Groupname message\n",
    "The group chat does not exists",
    "You are not in this group chat",
    "Group chat message sent."
}

print("Please login")
print("Username:")
while not login:
    message = input("")
    username = message
    message = "login" + message
    clientSocket.sendall(message.encode())
    data = clientSocket.recv(1024)
    receivedMessage = data.decode()
    while receivedMessage == "invalid username":
        print("Invalid username, please input again\nUsername: ", end='')
        message = input("")
        clientSocket.sendall(message.encode())
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        username = message

    while True:
        if receivedMessage == "Password":
            print("Password: ")
        elif receivedMessage == "Invalid password":
            print("Invalid password, please try again\nPassword: ")
        elif receivedMessage == "correct password":
            print("Welcome to TESSENGER!")
            print(command)
            message = f"{serverHost} {UDPPort}"
            clientSocket.sendall(message.encode())
            data = clientSocket.recv(1024)
            username = data.decode()
            login = True
            break
        elif receivedMessage == "correct password but enter within 10s block":
            print("Your account is blocked due to multiple login failures. Please try again later")
            connection = False
            time.sleep(1)
            sys.exit()
        elif receivedMessage == "block login after consecutive fail attempt":
            print("Invalid Password. Your account has been blocked. Please try again later")
            connection = False
            time.sleep(1)
            sys.exit()
        message = input("")
        clientSocket.sendall(message.encode())
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()


def receive_msg():
    global connection
    global login
    global username
    while connection:
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        # parse the message received from server and take corresponding actions
        if receivedMessage == "":
            print("[recv] Message from server is empty!")
            time.sleep(5)

        # handle receivedMessage with specific print format
        # handle activeuser command
        elif receivedMessage[:10] == "ActiveUser":
            global active_user_list
            active_user_list = {}
            active_users = receivedMessage[10:].split("\n")
            active_users = active_users[:-1]
            for i in range(len(active_users)):
                name, ip_address, udp, active_time = active_users[i].split(", ")
                active_user_list[name] = [ip_address, udp, active_time]
            print(active_user_list)
            print(receivedMessage[10:])
            print(command)
            
        # handle msgto command
        elif receivedMessage[:11] == "sending msg":
            print(receivedMessage[11:])
            print(command)

        # handle udp video
        elif receivedMessage[:12] == "receiver_udp":
            global receiver_udp
            receiver_udp = receivedMessage[12:]

        # handle groupmsg command
        elif receivedMessage[:8] == "groupmsg":
            print(receivedMessage[8:])
            print(command)

        # handle logout command
        elif receivedMessage[:3] == "Bye":
            print(receivedMessage)
            connection = False
            break
        elif receivedMessage == "download filename":
            print("[recv] You need to provide the file name you want to download")
        
        # handle received message that only need to print receivedMessage and command
        elif any(receivedMessage.startswith(msg) for msg in direct_receive_msg_set):
            print(receivedMessage)
            print(command)
            
        else:
            print(receivedMessage)
            print(command)

# this function serve as a server
# UDPPort is the terminal owner

def udp_receive():
    server_udpsocket = socket(AF_INET, SOCK_DGRAM)
    server_udpsocket.bind((serverHost, UDPPort))
    # print('The server is ready to receive UDPPort:', UDPPort)
    global connection
    while connection:
        data, udpaddress = server_udpsocket.recvfrom(2048)
        videofile = data.decode()
        data, udpaddress = server_udpsocket.recvfrom(2048)
        sender = data.decode()        
        with open(f"{sender}_{videofile}", 'wb') as file:
            while True:
                data, udpaddress = server_udpsocket.recvfrom(40960)
                # print(data)
                if not data:
                    # print("done")
                    break
                # print("writing")
                file.write(data)
        print(f"received {videofile} from {sender}")
        print(command)

p1 = threading.Thread(target=receive_msg)
p2 = threading.Thread(target=udp_receive)
p2.daemon = True
p1.start()
p2.start()

while connection:
    message = input("")
    # this part is served as client
    if login:
        if message[:9] == "/p2pvideo":
            if len(message.split(" ", 3)) != 3:
                print("Error usage, format = /p2pvideo receiver video_name")
            else:
                action, receiver, videofile = message.split(" ", 3)
                # print(action, receiver, videofile)
                # print(active_user_list)
                if not os.path.exists(videofile):
                    print(f"File {videofile} does not exist in the folder.")
                else:
                    if receiver not in active_user_list.keys():
                        print(f"{receiver} is not active, execute /activeuser to check current active user")
                    else:
                        receiver_udp = int(active_user_list[receiver][1])
                        address = active_user_list[receiver][0]
                        # print(receiver_udp, videofile)
                        client_udpSocket = socket(AF_INET, SOCK_DGRAM)
                        message = str(videofile)
                        client_udpSocket.sendto(message.encode(),(address, receiver_udp))
                        message = username
                        client_udpSocket.sendto(message.encode(),(address, receiver_udp))
                        with open(videofile, "rb") as file:
                            while True:
                                data = file.read(40960)
                                time.sleep(0.1)
                                # print(data)
                                if not data:
                                    data = ""
                                    client_udpSocket.sendto(data.encode(),(serverHost, int(receiver_udp)))
                                    break
                                client_udpSocket.sendto(data,(serverHost, int(receiver_udp)))
                        print(f"{videofile} has been uploaded")
                        client_udpSocket.close()
            print(command)
        elif message == "/logout":
            clientSocket.sendall(message.encode())
            time.sleep(1)
            break
        else:
            clientSocket.sendall(message.encode())
    else:
        clientSocket.sendall(message.encode())
    # receive response from the server
    # 1024 is a suggested packet size, you can specify it as 2048 or others
    # data = clientSocket.recv(1024)
    # receivedMessage = data.decode()

# close the socket
clientSocket.close()
sys.exit()