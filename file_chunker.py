import os
import hashlib

CHUNK_SIZE = 64 * 1024  # 256 KB per chunk

def divide_file_into_chunks(file_path, chunk_size=CHUNK_SIZE):
    """
    Splits a file into smaller chunks, calculates a SHA1 hash for each, and yields 
    the chunk data along with its hash and sequential chunk number.

    :param file_path: Path to the file to be divided
    :param chunk_size: Size of each chunk in bytes (default 256 KB)
    :yield: Tuple containing chunk data, SHA1 hash, and the chunk number
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")
    
    chunk_number = 1
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunk_size):
            chunk_hash = hashlib.sha1(chunk).hexdigest()
            yield chunk, chunk_hash, chunk_number
            chunk_number += 1

def write_chunk_to_file(chunk_data, chunk_number, output_dir="chunks"):
    """
    Saves a chunk to a file in the specified output directory.

    :param chunk_data: The binary data of the chunk
    :param chunk_number: The number of the chunk (used as filename)
    :param output_dir: Directory to store the chunk files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    chunk_file_path = os.path.join(output_dir, f"chunk_{chunk_number}.chunk")
    with open(chunk_file_path, 'wb') as chunk_file:
        chunk_file.write(chunk_data)
    print(f"Chunk {chunk_number} saved to {chunk_file_path}")

def print_chunk_data(file_path, chunk_number_to_display=1):
    """
    Prints data of a specific chunk for demonstration purposes, including the hash.

    :param file_path: Path to the file to be divided into chunks
    :param chunk_number_to_display: The specific chunk number to display data for
    """
    for chunk, chunk_hash, chunk_number in divide_file_into_chunks(file_path):
        if chunk_number == chunk_number_to_display:
            print(f"Chunk {chunk_number} hash: {chunk_hash}")
            print(f"Chunk {chunk_number} data:\n{chunk.decode(errors='replace')[:100]}...")  # Print first 100 characters
            break

# Example usage for testing
if __name__ == "__main__":
    file_path = "/Users/prabhudattamishra/Desktop/P2P/dark_knight.txt"  # Replace with actual file path

    # Print specific chunk data for demonstration
    print_chunk_data(file_path, chunk_number_to_display=1)

    # Example: Save chunks to disk with their hashes
    output_directory = "/Users/prabhudattamishra/Desktop/P2P/chunks"  # Modify as needed
    for chunk, chunk_hash, chunk_number in divide_file_into_chunks(file_path):
        write_chunk_to_file(chunk, chunk_number, output_dir=output_directory)
        print(f"Chunk {chunk_number} hash: {chunk_hash}")
