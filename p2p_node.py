import socket
import threading

# Keep track of all socket connections in this node
connections = []

def handle_client(conn, addr):
    """Receive messages from a connected peer and broadcast them to others."""
    print(f"[INFO] New connection from {addr}")
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break  # Peer disconnected
            # Show the received message in this node's console
            print(f"[{addr}] {msg.decode('utf-8')}")
            # Broadcast to all other connected peers
            broadcast(msg, conn)
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    conn.close()
    if conn in connections:
        connections.remove(conn)
    print(f"[INFO] Connection closed from {addr}")

def broadcast(msg, sender_conn):
    """Send the given msg to all peers except the sender."""
    for conn in connections:
        if conn != sender_conn:
            try:
                conn.send(msg)
            except Exception as e:
                print(f"[ERROR] Broadcast failed: {e}")
                conn.close()
                if conn in connections:
                    connections.remove(conn)

def start_server(host, port):
    """Listen for incoming peer connections in a loop."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen()
    print(f"[INFO] Server listening on {host}:{port}")

    while True:
        conn, addr = server_sock.accept()
        connections.append(conn)
        # Handle each new connection in a separate thread
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

def connect_to_peer(peer_host, peer_port):
    """Connect to an existing peer (another instance of this script)."""
    peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_sock.connect((peer_host, peer_port))
    connections.append(peer_sock)
    print(f"[INFO] Connected to peer at {peer_host}:{peer_port}")

    # Start a thread to continuously receive messages from this peer
    thread = threading.Thread(target=receive_from_peer, args=(peer_sock,))
    thread.start()

def receive_from_peer(peer_sock):
    """Continuously receive and display messages from a connected peer."""
    while True:
        try:
            msg = peer_sock.recv(1024)
            if not msg:
                break
            print(f"[PEER] {msg.decode('utf-8')}")
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    peer_sock.close()
    if peer_sock in connections:
        connections.remove(peer_sock)
    print("[INFO] Disconnected from peer")

def user_input_loop():
    """Continuously read user input and broadcast it to all connected peers."""
    print("[INFO] Type messages below. Type 'exit' to quit.")
    while True:
        msg = input()
        if msg.lower() == 'exit':
            break
        if msg:
            broadcast(msg.encode('utf-8'), None)

if __name__ == "__main__":
    # Prompt user for host/port to listen on
    host = input("Enter host to listen on (default=127.0.0.1): ") or "127.0.0.1"
    port_input = input("Enter port to listen on (default=65432): ")
    port = int(port_input) if port_input else 65432

    # Start the server in a background thread
    server_thread = threading.Thread(target=start_server, args=(host, port), daemon=True)
    server_thread.start()

    # Ask if you want to connect to another peer
    choice = input("Do you want to connect to a peer? (y/n) ")
    if choice.lower() == 'y':
        peer_host = input("Enter peer host (default=127.0.0.1): ") or "127.0.0.1"
        peer_port_input = input("Enter peer port (default=65432): ")
        peer_port = int(peer_port_input) if peer_port_input else 65432
        connect_to_peer(peer_host, peer_port)

    # Start reading user input and broadcasting messages
    user_input_loop()
    print("[INFO] Exiting node...")