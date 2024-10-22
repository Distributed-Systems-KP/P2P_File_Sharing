import socket

TRACKER_HOST = '0.0.0.0'  # Listens on all available network interfaces
TRACKER_PORT = 9090       # Port to listen on
peers = []                # List of active peers

def start_tracker():
    """
    Starts the tracker server which keeps track of peers and allows them to discover each other.
    """
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.bind((TRACKER_HOST, TRACKER_PORT))
    tracker_socket.listen(5)
    print(f"Tracker started on {TRACKER_HOST}:{TRACKER_PORT}, waiting for peers...")

    while True:
        client_socket, addr = tracker_socket.accept()
        print(f"Peer {addr} connected.")
        data = client_socket.recv(1024).decode()

        if data == "REQUEST_PEERS":
            # Send the list of known peers to the client
            peer_list = "\n".join(peers)
            print(f"Sending peer list to {addr}: {peer_list}")  # Log the peer list sent
            client_socket.send(peer_list.encode())
        elif data.startswith("ADD_PEER"):
            peer_ip = data.split(" ")[1]
            if peer_ip not in peers:
                peers.append(peer_ip)
                print(f"Peer {peer_ip} added.")
                print(f"Current list of peers: {peers}")  # Log current peer list after addition
                client_socket.send("PEER_ADDED".encode())
            else:
                client_socket.send("PEER_ALREADY_EXISTS".encode())
        
        client_socket.close()

if __name__ == "__main__":
    start_tracker()
