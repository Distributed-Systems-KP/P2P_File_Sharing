import socket
import threading
import random
from file_chunker import divide_file_into_chunks, CHUNK_SIZE
from torrent_metadata import TorrentMetadata
from time import sleep

TRACKER_HOST = '127.0.0.1'
TRACKER_PORT = 9090
MIN_PEERS_REQUIRED = 5  # Minimum number of peers required to start downloading chunks

class Peer:
    def __init__(self, peer_ip, file_to_share=None):
        self.peer_ip = peer_ip
        self.file_to_share = file_to_share
        self.peer_chunks = {}  # Store local chunks in memory
        self.received_chunks = set()  # Track downloaded chunks
        self.tracker_peers = {}  # Store other peers and their available chunks
        self.total_chunks = 0  # Total number of chunks in the file
        self.peer_port = None  # Dynamically assigned peer port
        self.uploaded_chunks = {}  # Track how many chunks each peer has received
        self.top_peers = []  # Store top 4 peers by upload contribution
        self.optimistic_peer = None  # Optimistically unchoked peer

    def start(self):
        # Start listening for chunk requests from other peers
        listen_thread = threading.Thread(target=self.listen_for_requests)
        listen_thread.start()

        if self.file_to_share:
            print(f"Sharing file: {self.file_to_share}")
            self.prepare_file_chunks()

        # Register with tracker and wait until enough peers are connected
        self.register_with_tracker()
        
        # Wait until the minimum number of peers are connected
        self.wait_for_peers()

        # Periodically update top peers and optimistic unchoking
        threading.Thread(target=self.refresh_top_peers_periodically).start()

        # Begin downloading chunks
        self.download_chunks()

    def prepare_file_chunks(self):
        """
        Prepares chunks for sharing if the peer has a file to share.
        """
        for chunk, chunk_hash, chunk_number in divide_file_into_chunks(self.file_to_share):
            self.peer_chunks[chunk_number] = chunk
            self.total_chunks += 1
            print(f"Prepared chunk {chunk_number} for sharing.")

    def register_with_tracker(self):
        """
        Registers the peer and its chunks with the tracker.
        """
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))

        # Send peer information and available chunks
        available_chunks = " ".join(map(str, self.peer_chunks.keys()))
        registration_msg = f"ADD_PEER {self.peer_ip}:{self.peer_port} {available_chunks}"
        tracker_socket.send(registration_msg.encode())

        response = tracker_socket.recv(1024).decode()
        print(f"Tracker response: {response}")

        # Request the list of peers from the tracker
        tracker_socket.send("REQUEST_PEERS".encode())
        peer_list = tracker_socket.recv(1024).decode().split("\n")
        tracker_socket.close()

        # Parse peer list and their available chunks
        for peer_info in peer_list:
            if peer_info:
                peer_addr, chunks = peer_info.split(": ")
                self.tracker_peers[peer_addr] = list(map(int, chunks.split(",")))
        print(f"Known peers and their chunks: {self.tracker_peers}")

    def wait_for_peers(self):
        """
        Wait until the minimum number of peers are connected before starting downloads.
        """
        print("Waiting for minimum peers to join...")
        while len(self.tracker_peers) < MIN_PEERS_REQUIRED:
            sleep(5)  # Check every 5 seconds
            self.register_with_tracker()  # Refresh peer list from the tracker
        print(f"Minimum peer threshold reached. Starting download process.")

    def download_chunks(self):
        """
        Downloads missing chunks from other peers.
        """
        while len(self.received_chunks) < self.total_chunks:
            # Request from top peers and optimistic peer
            peers_to_request_from = self.top_peers + ([self.optimistic_peer] if self.optimistic_peer else [])
            
            for peer_addr in peers_to_request_from:
                if peer_addr in self.tracker_peers:
                    for chunk_number in self.tracker_peers[peer_addr]:
                        if chunk_number not in self.received_chunks:
                            received_chunk = self.request_chunk_from_peer(peer_addr, chunk_number)
                            if received_chunk:
                                self.received_chunks.add(chunk_number)
                                print(f"Downloaded chunk {chunk_number} from {peer_addr}")
                                self.display_progress()

            # Check if all chunks are received
            if len(self.received_chunks) == self.total_chunks:
                print("Download complete! You are now a seeder.")
                break
            sleep(5)  # Wait before retrying

    def display_progress(self):
        """
        Displays download progress.
        """
        progress = (len(self.received_chunks) / self.total_chunks) * 100
        print(f"File download progress: {progress:.2f}%")

    def listen_for_requests(self):
        """
        Listens for incoming chunk requests from other peers.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 0))
        self.peer_port = server_socket.getsockname()[1]
        print(f"Listening for chunk requests on port {self.peer_port}...")

        server_socket.listen(5)
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_chunk_request, args=(conn,)).start()

    def handle_chunk_request(self, conn):
        """
        Handles incoming requests for chunks from other peers.
        """
        try:
            chunk_number = int(conn.recv(1024).decode())
            if chunk_number in self.peer_chunks:
                conn.send(self.peer_chunks[chunk_number])
                # Track upload contribution
                peer_ip = conn.getpeername()[0]
                self.uploaded_chunks[peer_ip] = self.uploaded_chunks.get(peer_ip, 0) + 1
                print(f"Uploaded chunk {chunk_number} to {peer_ip}")
            else:
                conn.send(b"CHUNK_NOT_FOUND")
        except Exception as e:
            print(f"Error handling chunk request: {e}")
        finally:
            conn.close()

    def request_chunk_from_peer(self, peer_addr, chunk_number):
        """
        Requests a chunk from a specific peer.
        """
        try:
            peer_ip, peer_port = peer_addr.split(":")
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, int(peer_port)))
            peer_socket.send(str(chunk_number).encode())
            chunk_data = peer_socket.recv(CHUNK_SIZE)
            peer_socket.close()

            if chunk_data == b"CHUNK_NOT_FOUND":
                print(f"Chunk {chunk_number} not found on peer {peer_addr}")
                return None
            return chunk_data
        except Exception as e:
            print(f"Error requesting chunk {chunk_number} from {peer_addr}: {e}")
            return None

    def update_top_peers(self):
        """
        Updates the top 4 peers based on upload contribution.
        """
        sorted_peers = sorted(self.uploaded_chunks.items(), key=lambda item: item[1], reverse=True)
        self.top_peers = [peer[0] for peer in sorted_peers[:4]]
        
        non_top_peers = [peer for peer in self.tracker_peers if peer not in self.top_peers]
        self.optimistic_peer = random.choice(non_top_peers) if non_top_peers else None

        print(f"Top 4 peers: {self.top_peers}")
        print(f"Optimistically unchoked peer: {self.optimistic_peer}")

    def refresh_top_peers_periodically(self, interval=30):
        """
        Refreshes the list of top peers at regular intervals.
        """
        while True:
            self.update_top_peers()
            sleep(interval)

if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with actual peer IP
    file_path = "dark_knight.txt"  # Replace with actual file path if sharing
    peer = Peer(peer_ip, file_path)
    peer.start()
