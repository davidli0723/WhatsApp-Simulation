"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: David LI
"""
from socket import *
from threading import Thread, Lock
import sys, select
import time
import datetime
import logging
from collections import defaultdict


# acquire server host and port from command line parameter
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT number_of_consecutive_failed_attempts======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)
max_fail_attempts = int(sys.argv[2])

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""

account = {}
with open("credentials.txt") as file:
    for line in file:
        name, password = line.split()
        account[name] = password
# print(account)
wrong_password_count = defaultdict(lambda: [0, datetime.datetime.now()])
sequence_number = 1
message_number = 1

active_user_list = {}

group_list = {}
group_list_pending = {}
groupmessage_log = defaultdict(list)

with open("userlog.txt", 'w') as file:
    file.write("Active user sequence number; timestamp; username; client IP address; client UDP server port number\n")

with open("messagelog.txt", 'w') as file:
    file.write("messageNumber; timestamp; username; message\n")

class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False

        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True
        self.username = ''
        self.login_status = False

    def run(self):
        message = ''
        
        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            message = data.decode()

            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if not self.login_status:
                if message == '':
                    self.clientAlive = False
                    print("===== the user disconnected - ", clientAddress)
                    break
                
                # handle message from the client
                if message[:5] == 'login':
                    print("[recv] New login request")
                    self.username = message[5:]
                    print(self.username)
                    self.process_login()
                elif message == 'download':
                    print("[recv] Download request")
                    message = 'download filename'
                    print("[send] " + message)
                    self.clientSocket.send(message.encode())
                else:
                    print("[recv] " + message)
                    print("[send] Cannot understand this message")
                    message = 'Cannot understand this message'
                    self.clientSocket.send(message.encode())
            else:
                if message == "/logout":
                    self.clientAlive = False
                    self.login_status = False
                    # update active_user_list
                    active_user_list.pop(self.username, None)
                    # update userlog.txt
                    with Lock():
                        with open("userlog.txt", 'w') as file:
                            file.write("Active user sequence number; timestamp; username; client IP address; client UDP server port number\n")
                            number = 1
                            for k, v in active_user_list.items():
                                file.write(f"{number}; {v[1]}; {k}; {v[2]}; {v[3]}\n")
                                number += 1
                            global sequence_number
                            sequence_number -= 1
                    print(f"{self.username} logout")
                    message = f"Bye, {self.username}!"
                    self.clientSocket.send(message.encode())
                    break

                elif message[:6] == "/msgto":
                    print(f"{self.username} issued /msgto command")
                    # if len(message.split(" ")) < 3 or (len(message.split(" ")) == 3 and message.split(" ")[2] == ''):
                    if len(message.split(" ")) < 3:
                        print("Invalid msgto command")
                        message = "Error usage, format = /msgto receiver message\n"
                        self.clientSocket.send(message.encode())
                    else:
                        action, receiver, msg = message.split(" ", 2)
                        if receiver in active_user_list.keys():
                            # update messagelog.txt
                            timestamp = datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')
                            with Lock():
                                with open("messagelog.txt", 'a') as file:
                                    global message_number
                                    file.write(f"{message_number}; {timestamp}; {receiver}; {msg}\n")
                                    message_number+=1
                            # sending message to receiver
                            message = f'{self.username} message to {receiver} \"{msg}\" at {timestamp}'
                            print(message)
                            message = "sending msg" + f"{timestamp}, {self.username}: {msg}"
                            active_user_list[receiver][0].send(message.encode())
                            # sending message to sender
                            message = f"message sent at {timestamp}"
                            self.clientSocket.send(message.encode())
                        else:
                            message = "User not found, please check with /activeuser\n"
                            print("user not found", message, "\n")
                            self.clientSocket.send(message.encode())
                            

                elif message == "/activeuser":
                    print(f"{self.username} issued /activeuser command")
                    if len(active_user_list) == 1:
                        message = "No other active user"
                        self.clientSocket.send(message.encode())
                    else:
                        message = "ActiveUser"
                        print("Return active user list:")
                        for k, v in active_user_list.items():
                            if k != self.username:
                                print(f"{k}; {v[2]}; {v[3]}; active since {v[1]}")
                                message += f"{k}, {v[2]}, {v[3]}, active since {v[1]}.\n"
                        self.clientSocket.send(message.encode())
                
                
                elif message[:12] == "/creategroup":
                    print(f"{self.username} issued /creategroup command")
                    if len(message.split()) < 3:
                        print("Return message: Group chat room is not created. Please enter at least one more active user")
                        message = "Please enter at least one more active users.\n"
                        self.clientSocket.send(message.encode())  
                    else:
                        with Lock():
                            create_group = True
                            action, groupname, user_list = message.split(" ", 2)
                            user_list = user_list.split()
                            if groupname in group_list.keys():
                                print(f"Groupname {groupname} already exists.")
                                message = f"Failed to create the group chat {groupname}: group name exists!"
                                self.clientSocket.send(message.encode())
                                create_group = False
                            else:
                                for name in user_list:
                                    if name not in active_user_list.keys():
                                        print(f"{name} is not active now")
                                        message = "members are inactive, please check with /activeuser command"
                                        self.clientSocket.send(message.encode())
                                        create_group = False
                                        break
                                if create_group:
                                    group_list[groupname] = [self.username]
                                    group_list_pending[groupname] = user_list
                                    print(f"Return message: Group chat room has been created, room name: {groupname}, users in this room: {self.username}, pending user: {group_list_pending[groupname]}")
                                    message = f"Group chat created {groupname}"
                                    self.clientSocket.send(message.encode())                   
                                    with open(f"{groupname}_messagelog.txt", 'w') as file:
                                        file.write("messageNumber; timestamp; username; message\n")
                
                elif message[:10] == "/joingroup":
                    print(f"{self.username} issued /joingroup command")
                    if len(message.split()) < 2 or len(message.split()) >= 3:
                        print("Incorrect joingroup input")
                        message = "Error usage, format = /joingroup Groupname\n"
                        self.clientSocket.send(message.encode())  
                    else:
                        action, groupname = message.split(" ")
                        if groupname in group_list.keys():
                            if self.username in group_list_pending[groupname]:
                                group_list[groupname].append(self.username)
                                group_list_pending[groupname].remove(self.username)
                                print(f"Return message: Join group successfully, room name: {groupname}, users in this room: {group_list[groupname]}, pending user: {group_list_pending[groupname]}")
                                message = f"Joined the group chat: {groupname} successfully"
                                self.clientSocket.send(message.encode())
                            elif self.username in group_list[groupname]:
                                print(f"{self.username} already in the group")
                                message = "you already in the group"
                                self.clientSocket.send(message.encode())
                            elif self.username not in group_list_pending[groupname]:
                                print(f"{self.username} is not group member")
                                message = "you are not group member"
                                self.clientSocket.send(message.encode())
                            # group_list[groupname].add(self.username)
                            # print(f"Return message: Join group chat room successfully, room name: {groupname}, users in this room: {list(group_list[groupname])}")
                            # message = f"Joined the group chat: {groupname} successfully."
                            # self.clientSocket.send(message.encode())  
                        else:
                            print("groupname not found")
                            message = "groupname not found"
                            self.clientSocket.send(message.encode())

                elif message[:9] == "/groupmsg":
                    print(f"{self.username} issued /groupmessage command")
                    if len(message.split(" ")) < 3:
                        print("Invalid groupmessage command")
                        message = "Error usage, format = /groupmsg Groupname message\n"
                        self.clientSocket.send(message.encode())  
                    else:
                        action, groupname, groupmessage = message.split(" ", 2)
                        if groupname not in group_list.keys():
                            print("The group chat does not exists")
                            message = "The group chat does not exists"
                            self.clientSocket.send(message.encode())
                        else:
                            if self.username not in group_list[groupname]:
                                print("You are not in this group chat")
                                message = "You are not in this group chat"
                                self.clientSocket.send(message.encode())
                            else:
                                timestamp = datetime.datetime.now().strftime('%d %b %Y %H:%M:%S') 
                                groupmessage_log[groupname].append(f"#{len(groupmessage_log[groupname])+1}; {timestamp}; {self.username}; {groupmessage}")
                                print(f"{self.username} issued a message in a group chat {groupname}")
                                print(f"{groupmessage_log[groupname][-1]}")
                                message = "Group chat message sent."
                                self.clientSocket.send(message.encode())
                                with Lock():
                                    with open(f"{groupname}_messagelog.txt", 'a') as file:
                                        file.write(f"{groupmessage_log[groupname][-1]}\n")   
                                for user in group_list[groupname]:
                                    if user in active_user_list and user != self.username:
                                        message = "groupmsg"
                                        message += f"{timestamp}, {groupname}, {self.username}: {groupmessage}"
                                        active_user_list[user][0].send(message.encode())
                                            
                # elif message[:16] == "request user udp":
                #     receiver_name = message[16:]
                #     receiver_udp = ""
                #     if receiver_name in active_user_list.keys():
                #         receiver_udp = active_user_list[receiver_name][3]
                #         message = f"receiver_udp{receiver_udp}"
                #         self.clientSocket.send(message.encode())
                #     else:
                #         message = f"receiver_udp{receiver_udp}"
                #         self.clientSocket.send(message.encode())

                else:
                    print("Invalid command!")
                    message = "Error. Invalid command!\n"
                    self.clientSocket.send(message.encode())
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
    def process_login(self):
        while self.username not in account.keys():
            message = "invalid username"
            print('[send] ' + message)
            self.clientSocket.send(message.encode())
            data = self.clientSocket.recv(1024)
            self.username = data.decode()

        message = 'Password'
        print('[send] ' + message)
        self.clientSocket.send(message.encode())
        data = self.clientSocket.recv(1024)
        password = data.decode() 

        while True:
            now = datetime.datetime.now()
            time_diff = now-wrong_password_count[self.username][1]
            time_diff = time_diff.total_seconds()
            # print(wrong_password_count[self.username], time_diff)
            if password == account[self.username]:
                if wrong_password_count[self.username][0] < max_fail_attempts or (wrong_password_count[self.username][0] >= max_fail_attempts and time_diff > 10):
                    with Lock():
                        message = "correct password"
                        print('sending approval')
                        self.clientSocket.send(message.encode())
                        self.login_status = True
                        data = self.clientSocket.recv(1024)
                        user_information = data.decode()
                        Serverhost, UDP_port = user_information.split()
                        message = f"{self.username}"
                        self.clientSocket.send(message.encode())
                        timestamp = datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')
                        active_user_list[self.username] = [self.clientSocket, timestamp, serverHost, UDP_port]
                        wrong_password_count[self.username] = [0, datetime.datetime.now()]
                        global sequence_number
                        with open("userlog.txt", 'a') as file:
                            file.write(f"{sequence_number}; {timestamp}; {self.username}; {Serverhost}; {UDP_port}\n")
                            sequence_number+=1
                        print(f"{self.username} login and written in log")
                    break
                elif wrong_password_count[self.username][0] >= 3 and time_diff <= 10:
                    print(f"correct password but enter within 10s block")
                    message = "correct password but enter within 10s block"
                    self.clientSocket.send(message.encode())
                    break
            else:
                latest_attempt = datetime.datetime.now()
                wrong_password_count[self.username][0] += 1
                wrong_password_count[self.username][1] = latest_attempt
                # print(wrong_password_count)
                if wrong_password_count[self.username][0] >= max_fail_attempts:
                    print("block login after consecutive fail attempt")
                    message = "block login after consecutive fail attempt"
                    self.clientSocket.send(message.encode())
                    break
                else:
                    message = 'Invalid password'
                    print('[send] ' + message)
                    self.clientSocket.send(message.encode())
                    data = self.clientSocket.recv(1024)
                    password = data.decode()
                


                
                



                
        


print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
