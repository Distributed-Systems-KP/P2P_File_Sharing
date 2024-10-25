from peer import Peer
from torrent_metadata import TorrentMetadata
from piece_manager import PieceManager
import os

class TorrentClient:
    def __init__(self, peer_ip, file_path, tracker_url):
        self.peer_ip = peer_ip
        self.file_path = file_path
        self.tracker_url = tracker_url
        self.metadata = TorrentMetadata(file_path, tracker_url)
        self.piece_manager = PieceManager(self.metadata.total_chunks)
        self.peers = []

    def start(self):
        """
        Starts the client by registering the peer, downloading pieces, and reassembling the file.
        """
        # Load metadata and prepare peer
        self.metadata.load_metadata()
        peer = Peer(self.peer_ip, self.file_path)
        self.peers.append(peer)

        # Start downloading and track progress
        peer.start()
        while not self.piece_manager.is_complete():
            self.download_missing_pieces()
        self.reassemble_file()

    def download_missing_pieces(self):
        """
        Requests missing pieces based on rarest-first prioritization.
        """
        for peer in self.peers:
            rarest_piece = self.piece_manager.get_rarest_piece()
            if rarest_piece:
                chunk = peer.request_chunk_from_peer(rarest_piece)
                if chunk and peer.verify_chunk(chunk):
                    self.piece_manager.mark_piece_complete(rarest_piece)
                    print(f"Downloaded piece {rarest_piece} successfully")

    def reassemble_file(self):
        """
        Reassembles downloaded pieces into the original file once all pieces are complete.
        """
        with open(f"reassembled_{os.path.basename(self.file_path)}", 'wb') as final_file:
            for i in range(1, self.metadata.total_chunks + 1):
                with open(f"chunks/chunk_{i}.chunk", 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
        print("File reassembly complete.")

if __name__ == "__main__":
    peer_ip = "127.0.0.1"  # Replace with actual IP
    file_path = "dark_knight.txt"  # Replace with the actual file
    tracker_url = "http://127.0.0.1:9090/announce"  # Replace with tracker URL

    client = TorrentClient(peer_ip, file_path, tracker_url)
    client.start()
