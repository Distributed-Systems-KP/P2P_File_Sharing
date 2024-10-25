import socket

class Tracker:
    def __init__(self, host='0.0.0.0', port=9090):
        self.host = host
        self.port = port
        self.peers = []  # List to store peer addresses

    def start(self):
        """
        Starts the tracker server to manage peers.
        """
        try:
            tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tracker_socket.bind((self.host, self.port))
            tracker_socket.listen(5)
            print(f"Tracker started on {self.host}:{self.port}, waiting for peers...")

            while True:
                client_socket, addr = tracker_socket.accept()
                print(f"Peer {addr} connected.")
                data = client_socket.recv(1024).decode()

                # Handle peer requests
                if data == "REQUEST_PEERS":
                    self.send_peers_list(client_socket, addr)
                elif data.startswith("ADD_PEER"):
                    self.add_peer(client_socket, data)
                else:
                    print(f"Unknown request from {addr}: {data}")
                client_socket.close()
        except Exception as e:
            print(f"Error in tracker operation: {e}")
        finally:
            tracker_socket.close()

    def send_peers_list(self, client_socket, addr):
        """
        Sends the list of known peers to the client.
        """
        try:
            peer_list = "\n".join(self.peers) if self.peers else "NO_PEERS"
            print(f"Sending peer list to {addr}: {peer_list}")
            client_socket.send(peer_list.encode())
        except Exception as e:
            print(f"Error sending peer list to {addr}: {e}")

    def add_peer(self, client_socket, data):
        """
        Adds a peer to the peer list and sends a confirmation.
        """
        try:
            peer_ip = data.split(" ")[1]
            if peer_ip not in self.peers:
                self.peers.append(peer_ip)
                print(f"Peer {peer_ip} added.")
                client_socket.send("PEER_ADDED".encode())
            else:
                client_socket.send("PEER_ALREADY_EXISTS".encode())
            print(f"Current list of peers: {self.peers}")
        except Exception as e:
            print(f"Error adding peer: {e}")

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start()
