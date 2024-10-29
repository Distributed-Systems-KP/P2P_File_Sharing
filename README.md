# BatTorrent: P2P_File_Sharing_System
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Contributions](https://img.shields.io/badge/contributions-welcome-orange.svg)
![Stars](https://img.shields.io/github/stars/Prabhudatta3004/P2P_File_Sharing)
![Forks](https://img.shields.io/github/forks/Prabhudatta3004/P2P_File_Sharing)
![Issues](https://img.shields.io/github/issues/Prabhudatta3004/P2P_File_Sharing)


This project is a BitTorrent-inspired Peer-to-Peer (P2P) file sharing system that enables users to share files by dividing them into chunks and distributing these chunks across peers. The system leverages a tracker server to coordinate peers and manage chunk availability.

## Features

- **File Chunking**: Files are split into fixed-size chunks with SHA1 hashes for integrity.
- **Tracker Server**: Manages peer connections and keeps track of which peers have which chunks.
- **Peer-to-Peer Data Exchange**: Peers share missing chunks with each other, prioritizing rarest pieces.
- **Data Integrity Verification**: Ensures the received chunks match their expected hash for reliable transfers.
- **Optimistic Unchoking**: Supports equitable resource sharing among peers by maintaining a list of top peers and rotating connections.

## Project Structure

- `chunker_file.py`: Splits files into chunks and saves each chunk to disk.
- `hashing.py`: Calculates and verifies SHA1 hashes for data integrity.
- `torrent_metadata.py`: Generates and saves metadata for files, storing information like chunk hashes, file size, and tracker URL.
- `tracker_server.py`: Coordinates peers, maintaining connections and tracking chunk distribution.
- `peer.py`: Represents individual peers, handling chunk uploads, downloads, and communication with the tracker.
- `piece_manager.py`: Manages and prioritizes missing pieces, helping peers choose the rarest pieces first for download.

## Getting Started

### Prerequisites

- Python 3.8 or above
- Internet access to run a local tracker and connect peers (or use a network setup for local testing)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Prabhudatta3004/P2P_File_Sharing.git
   cd P2P_File_Sharing
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure the tracker and peer files are set up with the correct IP addresses and ports. Adjust `TRACKER_HOST` and `TRACKER_PORT` in `peer.py` if necessary.

### Usage

1. **Start the Tracker Server**:
   Run the tracker server to handle peer connections:
   ```bash
   python tracker_server.py
   ```

2. **Start a Peer**:
   Run a peer instance, providing the file to share:
   ```bash
   python peer.py
   ```

   - Modify `file_path` in `peer.py` with the file's path to be shared.
   - Each peer will share, request, and download chunks of the file based on availability in the network.

3. **Metadata Creation**:
   To generate a metadata file for any file you intend to share, use `torrent_metadata.py`:
   ```python
   python torrent_metadata.py
   ```

   Update the file path and tracker URL in the script for your specific setup.

### Example

To test the setup:

1. Start `tracker_server.py` to listen for peers.
2. Start multiple instances of `peer.py` on different terminals or systems, pointing to the same or different files.
3. Monitor the peer interactions in the console, where you’ll see chunk sharing and download progress.

## Contributing

We welcome contributions to improve the project! Here’s how to get started:

1. **Fork the Repository**: Click on the 'Fork' button at the top of this page to create a copy of this repository in your account.
2. **Create a New Branch**: For each feature or bug fix, create a new branch with a meaningful name:
   ```bash
   git checkout -b feature-name
   ```
3. **Make Changes and Commit**: Implement your changes and commit them with descriptive messages.
   ```bash
   git commit -m "Add a new feature"
   ```
4. **Push and Create a Pull Request**:
   ```bash
   git push origin feature-name
   ```
   Open a pull request on the main repository to merge your changes.

### Guidelines

- **Code Quality**: Follow PEP8 guidelines and document functions as necessary.
- **Testing**: Test new features or modifications to ensure stability.
- **Documentation**: Update this README or create additional documentation for major changes.

### Future Enhancements

- Implementing more robust error handling for network issues.
- Enhancing the peer selection logic for improved performance.
- Adding a graphical interface for user-friendly interactions.
- Adding Unit tests and system checks.
- Implementing DHT (Distributed Hashing tables) instead of tracker_server.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


