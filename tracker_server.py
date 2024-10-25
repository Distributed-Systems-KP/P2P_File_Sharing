import socket
import threading

class Tracker:
    def __init__(self, host='0.0.0.0', port=9090):
        self.host = host
        self.port = port
        self.peers = {}  # Dictionary to store peer addresses and the chunks they have
        self.peer_connections = {}  # Keep track of peer connections for broadcasting

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
                threading.Thread(target=self.handle_peer, args=(client_socket, addr)).start()
        except Exception as e:
            print(f"Error in tracker operation: {e}")
        finally:
            tracker_socket.close()

    def handle_peer(self, client_socket, addr):
        """
        Handles communication with a peer.
        """
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                if data == "REQUEST_PEERS":
                    self.send_peers_list(client_socket, addr)
                elif data.startswith("ADD_PEER"):
                    self.add_peer(client_socket, data)
                    self.broadcast_peer_list()
                elif data.startswith("REMOVE_PEER"):
                    self.remove_peer(client_socket, addr)
                    self.broadcast_peer_list()
                else:
                    print(f"Unknown request from {addr}: {data}")
        except Exception as e:
            print(f"Error handling peer {addr}: {e}")
        finally:
            client_socket.close()
            self.remove_peer(None, addr)

    def send_peers_list(self, client_socket, addr):
        """
        Sends the list of known peers and their chunks to the client.
        """
        try:
            if self.peers:
                # Format peer list with the chunks they have
                peer_list = "\n".join([f"{peer}: {','.join(map(str, chunks))}" for peer, chunks in self.peers.items()])
            else:
                peer_list = "NO_PEERS"  # If no peers available
            print(f"Sending peer list to {addr}: {peer_list}")
            client_socket.send(peer_list.encode())
        except Exception as e:
            print(f"Error sending peer list to {addr}: {e}")

    def add_peer(self, client_socket, data):
        """
        Adds a peer to the peer list and registers the chunks they have.
        """
        try:
            parts = data.split(" ")
            peer_ip = parts[1]
            chunks = list(map(int, parts[2:]))  # List of chunk numbers the peer has

            if peer_ip not in self.peers:
                self.peers[peer_ip] = chunks
                self.peer_connections[peer_ip] = client_socket
                print(f"Peer {peer_ip} with chunks {chunks} added.")
                client_socket.send("PEER_ADDED".encode())
            else:
                # Update peer's chunk list if they're already registered
                self.peers[peer_ip] = chunks
                client_socket.send("PEER_UPDATED".encode())
            print(f"Current list of peers: {self.peers}")
        except Exception as e:
            print(f"Error adding peer: {e}")
            client_socket.send("ERROR".encode())

    def remove_peer(self, client_socket, addr):
        """
        Removes a peer from the list when they disconnect or request removal.
        """
        try:
            peer_ip = addr[0]
            if peer_ip in self.peers:
                del self.peers[peer_ip]
                if peer_ip in self.peer_connections:
                    del self.peer_connections[peer_ip]
                print(f"Peer {peer_ip} removed.")
                if client_socket:
                    client_socket.send("PEER_REMOVED".encode())
            else:
                if client_socket:
                    client_socket.send("PEER_NOT_FOUND".encode())
        except Exception as e:
            print(f"Error removing peer {addr}: {e}")

    def broadcast_peer_list(self):
        """
        Broadcasts the updated peer list to all connected peers.
        """
        peer_list = "\n".join([f"{peer}: {','.join(map(str, chunks))}" for peer, chunks in self.peers.items()])
        for peer, connection in self.peer_connections.items():
            try:
                print(f"Broadcasting updated peer list to {peer}: {peer_list}")
                connection.send(peer_list.encode())
            except Exception as e:
                print(f"Error broadcasting to {peer}: {e}")

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start()
