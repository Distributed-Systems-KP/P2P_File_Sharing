import socket
import threading
import hashlib
from file_chunker import divide_file_into_chunks, write_chunk_to_file, CHUNK_SIZE

TRACKER_HOST = '127.0.0.1'  # Replace with the actual tracker server IP
TRACKER_PORT = 5000

peer_chunks = {}  # Dictionary to store chunks in-memory

def verify_chunk_integrity(chunk_data, expected_hash):
    """
    Verifies the integrity of a chunk by comparing its hash to the expected hash.
    
    :param chunk_data: The binary data of the chunk to verify
    :param expected_hash: The expected SHA-1 hash of the chunk
    :return: True if the hash matches, False otherwise
    """
    calculated_hash = hashlib.sha1(chunk_data).hexdigest()
    return calculated_hash == expected_hash

def handle_chunk_request(conn):
    """
    Handle requests for file chunks from other peers.
    """
    chunk_hash = conn.recv(1024).decode()
    if chunk_hash in peer_chunks:
        print(f"Sending chunk {chunk_hash}")
        conn.send(peer_chunks[chunk_hash])
    else:
        conn.send(b"CHUNK_NOT_FOUND")
    conn.close()

def listen_for_requests():
    """
    Starts a peer's server to listen for chunk requests from other peers.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 0))  # Bind to an available port
    peer_port = server_socket.getsockname()[1]  # Get the dynamically assigned port
    print(f"Listening for chunk requests on port {peer_port}...")

    server_socket.listen(5)
    while True:
        conn, addr = server_socket.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_chunk_request, args=(conn,)).start()

def request_chunk_from_peer(peer_ip, chunk_hash, peer_port):
    """
    Request a file chunk from another peer.
    
    :param peer_ip: IP address of the peer to request the chunk from
    :param chunk_hash: The hash of the chunk to request
    :param peer_port: Port on which the peer is listening
    :return: The chunk data if found, None otherwise
    """
    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_socket.connect((peer_ip, peer_port))
    peer_socket.send(chunk_hash.encode())

    chunk_data = peer_socket.recv(CHUNK_SIZE)
    peer_socket.close()

    if chunk_data == b"CHUNK_NOT_FOUND":
        print(f"Chunk {chunk_hash} not found on {peer_ip}")
        return None
    else:
        print(f"Received chunk {chunk_hash} from {peer_ip}")
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

def start_peer(peer_ip, file_to_share=None):
    """
    Starts the peer node, connects to the tracker, and begins sharing chunks with other peers.
    
    :param peer_ip: The IP address of this peer.
    :param file_to_share: Optional file to share with other peers (will be divided into chunks).
    """
    # Start listening for incoming chunk requests in a separate thread
    listen_thread = threading.Thread(target=listen_for_requests)
    listen_thread.start()

    # Wait for the thread to start and bind to a port before continuing
    listen_thread.join()

    if file_to_share:
        print(f"Sharing file: {file_to_share}")
        # Divide file into chunks and store them in-memory (for this demo)
        for chunk, chunk_hash in divide_file_into_chunks(file_to_share):
            peer_chunks[chunk_hash] = chunk
            print(f"Chunk {chunk_hash} ready for sharing.")

    # Register this peer with the tracker and get a list of peers
    peers = connect_to_tracker(peer_ip, listen_thread.peer_port)

    # Example of requesting a chunk from another peer
    if peers:
        peer_to_request_from = peers[0].split(":")[0]
        example_chunk_hash = list(peer_chunks.keys())[0]  # Request one of your own chunks as a demo
        received_chunk = request_chunk_from_peer(peer_to_request_from, example_chunk_hash, listen_thread.peer_port)

        if received_chunk:
            # Verify the integrity of the received chunk
            if verify_chunk_integrity(received_chunk, example_chunk_hash):
                print(f"Chunk {example_chunk_hash} verified successfully!")
                # Optionally, save the verified chunk to a file
                write_chunk_to_file(received_chunk, example_chunk_hash, "received_chunks")
            else:
                print(f"Chunk {example_chunk_hash} is corrupted!")
    
if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with the actual peer IP
    file_to_share = "example_file.txt"  # Replace with the file you want to share
    start_peer(peer_ip, file_to_share)
