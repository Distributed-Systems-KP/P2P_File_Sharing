import socket
import threading
import random
from file_chunker import divide_file_into_chunks, write_chunk_to_file, CHUNK_SIZE
from time import sleep
from concurrent.futures import ThreadPoolExecutor

class Peer:
    def __init__(self, tracker_host='127.0.0.1', tracker_port=9090):
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.peer_chunks = {}  # Store chunks in memory
        self.received_chunks = set()  # Track downloaded chunks
        self.uploaded_chunks = {}  # Track uploads per peer
        self.peer_port = None  # Dynamically assigned port for the peer
        self.top_peers = []  # Top 4 peers by upload contribution
        self.optimistic_peer = None  # Optimistically unchoked peer
        self.peers = []  # List of all available peers

    def start(self, peer_ip, file_to_share=None):
        """
        Starts the peer, registers with the tracker, and begins chunk sharing.
        """
        self.peer_ip = peer_ip

        # Start listening for chunk requests in a thread pool for better scalability
        threading.Thread(target=self.listen_for_requests).start()

        if file_to_share:
            self.share_file(file_to_share)

        # Register this peer with the tracker and get the list of peers
        self.peers = self.connect_to_tracker()

        # Start refreshing the top peers every 30 seconds
        threading.Thread(target=self.refresh_top_peers_periodically).start()

    def listen_for_requests(self):
        """
        Listens for incoming chunk requests from other peers using a thread pool.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 0))
        self.peer_port = server_socket.getsockname()[1]
        print(f"Listening for chunk requests on port {self.peer_port}...")

        server_socket.listen(5)

        with ThreadPoolExecutor(max_workers=10) as executor:  # Use thread pool to handle requests
            while True:
                conn, addr = server_socket.accept()
                print(f"Connection from {addr}")
                executor.submit(self.handle_chunk_request, conn)  # Submit to thread pool

    def handle_chunk_request(self, conn):
        """
        Handles requests for file chunks from other peers.
        """
        try:
            chunk_number = int(conn.recv(1024).decode())
            if chunk_number in self.peer_chunks:
                print(f"Sending chunk {chunk_number}")
                conn.send(self.peer_chunks[chunk_number])
                self.track_upload(conn, chunk_number)
            else:
                conn.send(b"CHUNK_NOT_FOUND")
        except Exception as e:
            print(f"Error handling chunk request: {e}")
        finally:
            conn.close()

    def track_upload(self, conn, chunk_number):
        """
        Tracks the number of chunks uploaded to each peer for optimistic unchoking.
        """
        addr = conn.getpeername()[0]
        self.uploaded_chunks[addr] = self.uploaded_chunks.get(addr, 0) + 1
        print(f"Uploaded chunk {chunk_number} to {addr}. Total uploads: {self.uploaded_chunks[addr]}")

    def share_file(self, file_to_share):
        """
        Splits a file into chunks and prepares them for sharing.
        """
        total_chunks = 0
        for chunk, chunk_number in divide_file_into_chunks(file_to_share):
            self.peer_chunks[chunk_number] = chunk
            total_chunks += 1
            print(f"Chunk {chunk_number} ready for sharing.")
        self.total_chunks = total_chunks

    def request_chunk(self, peer_ip, chunk_number, peer_port):
        """
        Requests a chunk from another peer.
        """
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, peer_port))
            peer_socket.send(str(chunk_number).encode())
            chunk_data = peer_socket.recv(CHUNK_SIZE)
            peer_socket.close()

            if chunk_data == b"CHUNK_NOT_FOUND":
                print(f"Chunk {chunk_number} not found on {peer_ip}")
                return None
            else:
                print(f"Received chunk {chunk_number} from {peer_ip}")
                return chunk_data
        except Exception as e:
            print(f"Error requesting chunk from {peer_ip}: {e}")
            return None

    def connect_to_tracker(self):
        """
        Connects to the tracker, registers the peer, and retrieves a list of other peers.
        """
        try:
            tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tracker_socket.connect((self.tracker_host, self.tracker_port))

            # Register this peer with the tracker
            tracker_socket.send(f"ADD_PEER {self.peer_ip}:{self.peer_port}".encode())
            response = tracker_socket.recv(1024).decode()
            print(f"Tracker response: {response}")

            # Request the list of peers
            tracker_socket.send("REQUEST_PEERS".encode())
            peers_list = tracker_socket.recv(1024).decode().split("\n")
            tracker_socket.close()

            print(f"Known peers: {peers_list}")
            return peers_list
        except Exception as e:
            print(f"Error connecting to tracker: {e}")
            return []

    def update_top_peers(self):
        """
        Updates the top 4 peers based on upload contribution and selects one for optimistic unchoking.
        """
        sorted_peers = sorted(self.uploaded_chunks.items(), key=lambda item: item[1], reverse=True)
        self.top_peers = [peer[0] for peer in sorted_peers[:4]]

        non_top_peers = [peer for peer in self.peers if peer not in self.top_peers]
        self.optimistic_peer = random.choice(non_top_peers) if non_top_peers else None

        print(f"Top 4 peers: {self.top_peers}")
        print(f"Optimistically unchoked peer: {self.optimistic_peer}")

    def refresh_top_peers_periodically(self, interval=30):
        """
        Refreshes the list of top peers every 30 seconds.
        """
        while True:
            self.update_top_peers()
            sleep(interval)

    def check_if_all_chunks_received(self):
        """
        Checks if the peer has received all the chunks.
        """
        if len(self.received_chunks) == self.total_chunks:
            print(f"All {self.total_chunks} chunks received!")
            return True
        return False

    def download_chunks(self):
        """
        Example method to request chunks from peers and save them to disk.
        """
        if self.peers and self.peers[0]:
            peer_to_request_from = self.peers[0].split(":")[0]
            chunk_number = 1  # Example chunk number to request
            received_chunk = self.request_chunk(peer_to_request_from, chunk_number, self.peer_port)

            if received_chunk:
                self.received_chunks.add(chunk_number)
                write_chunk_to_file(received_chunk, chunk_number, "received_chunks")
                print(f"Chunk {chunk_number} received and saved.")

        self.check_if_all_chunks_received()

if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with actual peer IP
    file_to_share = "example_file.txt"  # Replace with actual file
    peer = Peer() 
    peer.start(peer_ip, file_to_share)
