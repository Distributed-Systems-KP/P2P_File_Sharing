import socket
import threading
import random
from file_chunker import divide_file_to_chunks, CHUNK_SIZE
from torrent_metadata import TorrentMetadata
from time import sleep

TRACKER_HOST = '127.0.0.1' # the host ip for the tracker server
TRACKER_PORT = 9090 # the port on which the tracker server is listening(I prefer 9090, you can use any port of your liking)
MIN_PEERS_REQUIRED = 5 ## I have set minimum number of peers required to start downloading the chunks

class Peer:
    def __init__(self, peer_ip, file_to_share=None):
        """
        Just initializes the peer with the Ip and the file to share
        PARAMETERS:
        peer_ip: the IP address of the peer
        file_to_share: Path to the file that this peer is sharing"""

        self.peer_ip = peer_ip
        self.file_to_share= file_to_share
        self.peer_chunks = {} # Dictionary to store local chunks of the file in memory
        self.received_chunks= set() # using a set to track which chunks have been downloaded so far
        self.tracker_peers={} # Dictionary to store other peers and the chunks they have
        self.total_chunks =0 # the total number of chunks in the file
        self.peer_port = None # the port number on which the peer listens for the requests
        self.uploaded_chunks={} # Dictionary to track how many chunks each peer has uploaded
        self.top_peers= [] # list of the top 4 peers sorted by upload contribution
        self.optimistic_peer = None # randomly selecting peer for optimistic unchoking
    
    def start(self):
        """
        Now I am starting the peer's operations:
        -> listening for incoming requests
        -> Registers with the tracker
        -> Waits for sufficient peers to connect
        -> Begins downloading chunks
        """
        #starting a new thread to listen for incoming chunk requests
        listening_thread = threading.Thread(target=self.listen_for_requests)
        listening_thread.start()

        if self.file_to_share:
            print(f"Sharing file: {self.file_to_share}")
            self.prepare_file_chunks()  # Prepare the chunks for sharing if there is a file

        # Register with the tracker server
        self.register_with_tracker()
        
        # Wait for the minimum number of peers to connect before starting downloads
        self.wait_for_peers()

        # Periodically refresh the list of top peers and optimistically unchoked peers
        threading.Thread(target=self.refresh_top_peers_periodically).start()

        # Start downloading the missing chunks
        self.download_chunks()

    
    def prepare_file_chunks(self):
        """
        Prepares chunks for sharing if peer has a file to share
        Splits the file into chunks and storing them in memory"""

        for chunk, chunk_hash, chunk_number in divide_file_to_chunks(self.file_to_share):
            self.peer_chunks[chunk_number] = chunk ## storing each chunk with it's number
            self.total_chunks +=1 ## Increment the total chunk count
            print(f"Prepared chunk {chunk_number} for sharing")
    
    def register_with_tracker(self):
        """
        This function registes the peer and its available chunks with the tracker
        """
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT)) # Connect to the tracker server

        # sending a messag to the tracker server with the peer's IP, port and available chunks
        available_chunks = " ".join(map(str, self.peer_chunks.keys())) # List of chunks the peer has already
        registration_msg = f"ADD_PEER {self.peer_ip}:{self.peer_port} {available_chunks}"
        tracker_socket.send(registration_msg.encode()) ## Sending the registration message

        response = tracker_socket.recv(1024).decode()  # Receiving a response from the tracker
        print(f"Tracker response: {response}")

        # Request the list of peers from the tracker
        tracker_socket.send("REQUEST_PEERS".encode())
        peer_list = tracker_socket.recv(1024).decode().split("\n")
        tracker_socket.close()

        # Parse the list of peers and their available chunks
        for peer_info in peer_list:
            if peer_info:
                peer_addr, chunks = peer_info.split(": ")
                self.tracker_peers[peer_addr] = list(map(int, chunks.split(",")))  # Store peer info
        print(f"Known peers and their chunks: {self.tracker_peers}")
    
    def wait_for_peers(self):
        """
        Waits until the minimum number of peers have connected before starting the downloads"""

        print("Waiting for minimum peers to join...")
        while len(self.tracker_peers) < MIN_PEERS_REQUIRED:
            sleep(5) ## waiting for 5 seconds before checking again
            self.register_with_tracker() ## Refresh the list of peers from the tracker
        print ("Minimum peer threshold has been reached, starting download process")

    def download_chunks(self):
        """
        Downloads missing chunks from other peers"""
        while len(self.received_chunks)< self.total_chunks:
            # Creating a list of peers to request chunks from (top peers + optimistic peer)
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

            # Checking if all chunks have been downloaded
            if len(self.received_chunks) == self.total_chunks:
                print("Download complete! You are now a seeder")
                break
            sleep(5) ## wait before retrying
    
    def display_progress(self):
        """ 
        Displays the download progress as a percentage.
        """
        progress = (len(self.received_chunks) / self.total_chunks) * 100
        print(f"File download progress: {progress:.2f}%")

    def listen_for_requests(self):
        """
        Listening for incoming requests from other peers
        asking for chunks."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 0)) # Binding to an available port
        self.peer_port = server_socket.getsockname()[1] # Store the assigned port
        print(f"Listening for chunk requests on port {self.peer_port}...")

        server_socket.listen(5)
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_chunk_request, args=(conn,)).start()
    
    def handle_chunk_request(self, conn):
        """
        Handles requests for chunks from other peers.
        """
        try:
            chunk_number = int(conn.recv(1024).decode())  # Reading the requested chunk number
            if chunk_number in self.peer_chunks:
                conn.send(self.peer_chunks[chunk_number])  # Sending the requested chunk
                # Update the upload contribution for the requesting peer
                peer_ip = conn.getpeername()[0]
                self.uploaded_chunks[peer_ip] = self.uploaded_chunks.get(peer_ip, 0) + 1
                print(f"Uploaded chunk {chunk_number} to {peer_ip}")
            else:
                conn.send(b"CHUNK_NOT_FOUND")  # Inform if the chunk is not available
        except Exception as e:
            print(f"Error handling chunk request: {e}")
        finally:
            conn.close()

    def request_chunk_from_peer(self, peer_addr, chunk_number):
    """
    Requests a specific chunk from another peer.
    PARAMETERS:
    peer_addr: The address of the peer to request from.
    chunk_number: The number of the chunk to request.
    """
    try:
        peer_ip, peer_port = peer_addr.split(":")
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((peer_ip, int(peer_port)))
        peer_socket.send(str(chunk_number).encode())  # Send the chunk request
        
        # Receive the chunk data
        chunk_data = peer_socket.recv(CHUNK_SIZE)
        peer_socket.close()

        # Check if the chunk was not found
        if chunk_data == b"CHUNK_NOT_FOUND":
            print(f"Chunk {chunk_number} not found on peer {peer_addr}")
            return False, f"Chunk {chunk_number} not found on peer {peer_addr}"
        
        # Return the successfully retrieved chunk data
        return True, chunk_data

    except Exception as e:
        print(f"Error requesting chunk {chunk_number} from {peer_addr}: {e}")
        # Return False with the error message
        return False, f"Error requesting chunk {chunk_number} from {peer_addr}: {e}"


    def update_top_peers(self):
        """
        Updates the list of top 4 peers based on the number of chunks they've uploaded.
        """
        sorted_peers = sorted(self.uploaded_chunks.items(), key=lambda item: item[1], reverse=True)
        self.top_peers = [peer[0] for peer in sorted_peers[:4]]  # Top 4 peers by upload contribution
        
        # Select a random peer outside the top 4 for optimistic unchoking
        non_top_peers = [peer for peer in self.tracker_peers if peer not in self.top_peers]
        self.optimistic_peer = random.choice(non_top_peers) if non_top_peers else None

        print(f"Top 4 peers: {self.top_peers}")
        print(f"Optimistically unchoked peer: {self.optimistic_peer}")

    def refresh_top_peers_periodically(self, interval=30):
        """
        Periodically refreshes the list of top peers every given interval.
        PARAMETERS:
        interval: Time in seconds between each refresh.
        """
        while True:
            self.update_top_peers()  # Update the top peers
            sleep(interval)

if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with the actual peer IP
    file_path = "dark_knight.txt"  # Replace with the actual file path
    peer = Peer(peer_ip, file_path)
    peer.start()

