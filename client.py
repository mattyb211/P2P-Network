import socket
import threading

# Server configuration (make sure HOST and PORT match the server)
HOST = '127.0.0.1'
PORT = 65432

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive_messages():
    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if not msg:
                break
            print(msg)
        except Exception as e:
            print(f"Receive error: {e}")
            break

def send_messages():
    while True:
        msg = input()  # Read user input from console
        if msg:
            try:
                client.send(msg.encode('utf-8'))
            except Exception as e:
                print(f"Send error: {e}")
                break

# Start a thread to handle incoming messages
thread_recv = threading.Thread(target=receive_messages)
thread_recv.start()

# Main thread for sending messages (blocking loop)
send_messages()