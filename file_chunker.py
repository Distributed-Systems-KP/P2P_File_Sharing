import hashlib
import os

CHUNK_SIZE = 256 * 1024  # 256KB per chunk

def divide_file_into_chunks(file_path, chunk_size=CHUNK_SIZE):
    """
    Divides a file into smaller chunks and returns an iterator of (chunk_data, chunk_hash).
    
    :param file_path: Path to the file to be divided
    :param chunk_size: Size of each chunk in bytes (default 256KB)
    :return: Iterator that yields tuples of (chunk_data, chunk_hash)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    with open(file_path, 'rb') as file:
        while chunk := file.read(chunk_size):
            chunk_hash = hashlib.sha1(chunk).hexdigest()
            yield chunk, chunk_hash

def write_chunk_to_file(chunk_data, chunk_hash, output_dir):
    """
    Writes a chunk to a file with the chunk's hash as the filename.
    
    :param chunk_data: The binary data of the chunk
    :param chunk_hash: The SHA-1 hash of the chunk (used as filename)
    :param output_dir: Directory to store the chunk files
    """
    os.makedirs(output_dir, exist_ok=True)
    chunk_file_path = os.path.join(output_dir, f"{chunk_hash}.chunk")
    with open(chunk_file_path, 'wb') as chunk_file:
        chunk_file.write(chunk_data)
    print(f"Chunk {chunk_hash} saved.")

# Example usage
if __name__ == "__main__":
    file_to_chunk = "example_file.txt"
    output_directory = "chunks"

    for chunk, chunk_hash in divide_file_into_chunks(file_to_chunk):
        write_chunk_to_file(chunk, chunk_hash, output_directory)
