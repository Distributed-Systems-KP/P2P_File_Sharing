import os

CHUNK_SIZE = 256 * 1024  # 256KB per chunk

def divide_file_into_chunks(file_path, chunk_size=CHUNK_SIZE):
    """
    Divides a file into smaller chunks and returns an iterator of (chunk_data, chunk_number).
    
    :param file_path: Path to the file to be divided
    :param chunk_size: Size of each chunk in bytes (default 256KB)
    :return: Iterator that yields tuples of (chunk_data, chunk_number)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    chunk_number = 1
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunk_size):
            yield chunk, chunk_number
            chunk_number += 1

def write_chunk_to_file(chunk_data, chunk_number, output_dir):
    """
    Writes a chunk to a file with the chunk number as the filename.
    
    :param chunk_data: The binary data of the chunk
    :param chunk_number: The number of the chunk (used as filename)
    :param output_dir: Directory to store the chunk files
    """
    os.makedirs(output_dir, exist_ok=True)
    chunk_file_path = os.path.join(output_dir, f"chunk_{chunk_number}.chunk")
    with open(chunk_file_path, 'wb') as chunk_file:
        chunk_file.write(chunk_data)
    print(f"Chunk {chunk_number} saved.")
