import socket
import threading

# Server configuration
HOST = '127.0.0.1'  # Localhost for testing
PORT = 65432        # Arbitrary non-privileged port

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break  # No message means client disconnected
            # Broadcast the message to all other clients
            broadcast(msg, conn)
        except Exception as e:
            print(f"Error: {e}")
            break
    conn.close()
    if conn in clients:
        clients.remove(conn)
    print(f"Connection closed from {addr}")

def broadcast(message, connection):
    for client in clients:
        if client != connection:
            try:
                client.send(message)
            except Exception as e:
                print(f"Broadcast error: {e}")
                client.close()
                clients.remove(client)

print("Server is listening...")
while True:
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()