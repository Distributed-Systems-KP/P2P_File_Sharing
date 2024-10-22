import socket
import threading
import random
from file_chunker import divide_file_into_chunks, write_chunk_to_file, CHUNK_SIZE
from time import sleep

TRACKER_HOST = '127.0.0.1'  # Replace with the actual tracker server IP
TRACKER_PORT = 9090

peer_chunks = {}  # Dictionary to store chunks in-memory
peer_port = None  # Global variable to store the dynamically assigned port
uploaded_chunks = {}  # Track how many chunks each peer has uploaded
received_chunks = set()  # Track chunks that have been downloaded
top_peers = []  # List to store top 4 peers
optimistic_peer = None  # Peer selected for optimistic unchoking

def handle_chunk_request(conn):
    """
    Handle requests for file chunks from other peers.
    """
    chunk_number = conn.recv(1024).decode()
    chunk_number = int(chunk_number)  # Convert the chunk number to an integer

    if chunk_number in peer_chunks:
        print(f"Sending chunk {chunk_number}")
        conn.send(peer_chunks[chunk_number])
        # Track the number of chunks uploaded to this peer
        addr = conn.getpeername()[0]  # Get the requesting peer's IP address
        uploaded_chunks[addr] = uploaded_chunks.get(addr, 0) + 1
    else:
        conn.send(b"CHUNK_NOT_FOUND")
    conn.close()

def listen_for_requests():
    """
    Starts a peer's server to listen for chunk requests from other peers.
    """
    global peer_port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 0))  # Bind to an available port
    peer_port = server_socket.getsockname()[1]  # Get the dynamically assigned port
    print(f"Listening for chunk requests on port {peer_port}...")

    server_socket.listen(5)
    while True:
        conn, addr = server_socket.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_chunk_request, args=(conn,)).start()

def request_chunk_from_peer(peer_ip, chunk_number, peer_port):
    """
    Request a file chunk from another peer by chunk number.
    
    :param peer_ip: IP address of the peer to request the chunk from
    :param chunk_number: The number of the chunk to request
    :param peer_port: Port on which the peer is listening
    :return: The chunk data if found, None otherwise
    """
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

def connect_to_tracker(peer_ip, peer_port):
    """
    Connects to the tracker and registers the peer, then gets the list of other peers.
    
    :param peer_ip: The IP address of the peer.
    :param peer_port: The port that the peer is listening on.
    :return: List of other peers from the tracker.
    """
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))

    # Register this peer with the tracker
    tracker_socket.send(f"ADD_PEER {peer_ip}:{peer_port}".encode())
    response = tracker_socket.recv(1024).decode()
    print(f"Tracker response: {response}")

    # Request list of peers
    tracker_socket.send("REQUEST_PEERS".encode())
    peers_list = tracker_socket.recv(1024).decode().split("\n")
    tracker_socket.close()

    print(f"Known peers: {peers_list}")
    return peers_list

def update_top_peers(peers):
    """
    Periodically updates the top 4 peers based on upload contribution and selects one optimistic peer.
    """
    global top_peers, optimistic_peer

    # Sort peers by the number of chunks they've uploaded (highest first)
    sorted_peers = sorted(uploaded_chunks.items(), key=lambda item: item[1], reverse=True)
    
    # Get the top 4 peers by bandwidth
    top_peers = [peer[0] for peer in sorted_peers[:4]]

    # Optimistic unchoking: Select a random peer outside the top 4
    non_top_peers = [peer for peer in peers if peer not in top_peers]
    optimistic_peer = random.choice(non_top_peers) if non_top_peers else None

    print(f"Top 4 peers: {top_peers}")
    print(f"Optimistic unchoking peer: {optimistic_peer}")

def refresh_top_peers_periodically(peers, interval=30):
    """
    Refresh the list of top peers every `interval` seconds.
    """
    while True:
        update_top_peers(peers)
        sleep(interval)

def check_if_all_chunks_received(total_chunks):
    """
    Check if the peer has received all the chunks by comparing the number of received chunks.
    """
    if len(received_chunks) == total_chunks:
        print(f"Peer has received all {total_chunks} chunks!")
        return True
    return False

def start_peer(peer_ip, file_to_share=None):
    """
    Starts the peer node, connects to the tracker, and begins sharing chunks with other peers.
    
    :param peer_ip: The IP address of this peer.
    :param file_to_share: Optional file to share with other peers (will be divided into chunks).
    """
    # Start listening for incoming chunk requests in a separate thread
    listen_thread = threading.Thread(target=listen_for_requests)
    listen_thread.start()

    if file_to_share:
        print(f"Sharing file: {file_to_share}")
        # Divide file into chunks and store them in-memory with chunk numbers
        total_chunks = 0
        for chunk, chunk_number in divide_file_into_chunks(file_to_share):
            peer_chunks[chunk_number] = chunk
            total_chunks += 1
            print(f"Chunk {chunk_number} ready for sharing.")

    # Register this peer with the tracker and get a list of peers
    peers = connect_to_tracker(peer_ip, peer_port)

    # Start refreshing the top peers every 30 seconds in a background thread
    threading.Thread(target=refresh_top_peers_periodically, args=(peers,)).start()

    # Example of requesting a chunk from another peer
    if peers and peers[0]:  # Ensure there are peers to request from
        peer_to_request_from = peers[0].split(":")[0]
        example_chunk_number = 1  # Request chunk 1 from another peer for demonstration
        received_chunk = request_chunk_from_peer(peer_to_request_from, example_chunk_number, peer_port)

        if received_chunk:
            received_chunks.add(example_chunk_number)  # Track the received chunk
            print(f"Chunk {example_chunk_number} received successfully!")
            # Optionally, save the received chunk to a file
            write_chunk_to_file(received_chunk, example_chunk_number, "received_chunks")

    # Check if the peer has received all chunks (this is simplified; adapt as needed)
    check_if_all_chunks_received(total_chunks)

if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with the actual peer IP
    file_to_share = "example_file.txt"  # Replace with the file you want to share
    start_peer(peer_ip, file_to_share)
