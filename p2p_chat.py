import socket
import threading
import sys
import time
import sqlite3

def init_db(db_file='chat.db'):
    """
    Initialize a local SQLite database for storing chat messages.
    """
    conn = sqlite3.connect(db_file, check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def log_chat(conn, direction, msg):
    """
    Log a message to the database.
    """
    cur = conn.cursor()
    cur.execute("INSERT INTO chat_log (direction, message) VALUES (?, ?)", (direction, msg))
    conn.commit()

def listen_for_messages(sock, db_conn):
    """
    Listen continuously for messages from the socket, print them,
    and store each incoming message in the local database.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("[*] Peer closed the connection.")
                break
            message = data.decode('utf-8')
            print(f"[Incoming] {message}")
            log_chat(db_conn, 'received', message)
        except ConnectionResetError:
            print("[*] Connection was reset by the peer.")
            break
        except Exception as e:
            print(f"[Error] Receiving message: {e}")
            break

def run_server(listen_port, db_conn, ready_evt, conn_container):
    """
    Create a server socket that listens for a single incoming connection.
    On connection, store the socket and signal that the connection is ready.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', listen_port))
    server_sock.listen(1)
    print(f"[*] Server listening on port {listen_port}...")

    try:
        client_sock, client_addr = server_sock.accept()
        print(f"[*] Accepted connection from {client_addr}")
        conn_container[0] = client_sock
        ready_evt.set()
        threading.Thread(target=listen_for_messages, args=(client_sock, db_conn), daemon=True).start()
    except Exception as e:
        print(f"[Server Error] {e}")
    finally:
        server_sock.close()

def run_client(target_ip, target_port, db_conn, ready_evt, conn_container):
    """
    Repeatedly try to connect to the peer's server until a connection is made.
    """
    while not ready_evt.is_set():
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect((target_ip, target_port))
            print(f"[*] Connected to peer at {target_ip}:{target_port}")
            conn_container[0] = client_sock
            ready_evt.set()
            threading.Thread(target=listen_for_messages, args=(client_sock, db_conn), daemon=True).start()
            return
        except ConnectionRefusedError:
            print("[*] Peer unavailable, retrying in 2 seconds...")
            time.sleep(2)
        except Exception as e:
            print(f"[Client Error] {e}")
            time.sleep(2)

def main():
    """
    Usage: python p2p_chat.py <my_port> <peer_ip> <peer_port>
    """
    if len(sys.argv) != 4:
        print("Usage: python p2p_chat.py <my_port> <peer_ip> <peer_port>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    peer_ip = sys.argv[2]
    peer_port = int(sys.argv[3])

    # Initialize local database
    db_conn = init_db()

    # Shared container for the connected socket
    connection_box = [None]

    # Event to signal that a connection has been established
    connection_ready = threading.Event()

    # Start server thread (listens on my_port)
    server_thread = threading.Thread(target=run_server, args=(my_port, db_conn, connection_ready, connection_box), daemon=True)
    server_thread.start()

    # Start client thread (tries to connect to peer)
    client_thread = threading.Thread(target=run_client, args=(peer_ip, peer_port, db_conn, connection_ready, connection_box), daemon=True)
    client_thread.start()

    print("\n[*] Establishing peer-to-peer connection...")
    while not connection_ready.is_set():
        time.sleep(1)

    peer_sock = connection_box[0]
    if not peer_sock:
        print("[!] Failed to establish a connection. Exiting.")
        sys.exit(1)

    print("\n[*] Connection established! Start chatting. Type 'exit' to quit.\n")
    while True:
        try:
            user_msg = input("")
            if user_msg.lower() == "exit":
                print("[*] Closing connection and exiting.")
                peer_sock.close()
                sys.exit(0)
            peer_sock.sendall(user_msg.encode('utf-8'))
            log_chat(db_conn, 'sent', user_msg)
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting chat.")
            peer_sock.close()
            sys.exit(0)
        except BrokenPipeError:
            print("[!] Lost connection to peer.")
            sys.exit(1)

if __name__ == "__main__":
    main()