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
    
    try:
        chunk_number = 1
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                yield chunk, chunk_number
                chunk_number += 1
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

def write_chunk_to_file(chunk_data, chunk_number, output_dir):
    """
    Writes a chunk to a file with the chunk number as the filename.
    
    :param chunk_data: The binary data of the chunk
    :param chunk_number: The number of the chunk (used as filename)
    :param output_dir: Directory to store the chunk files
    :return: Boolean indicating success or failure
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        chunk_file_path = os.path.join(output_dir, f"chunk_{chunk_number}.chunk")
        with open(chunk_file_path, 'wb') as chunk_file:
            chunk_file.write(chunk_data)
        print(f"Chunk {chunk_number} saved.")
        return True
    except Exception as e:
        print(f"Failed to write chunk {chunk_number}: {e}")
        return False

def divide_and_save_chunks(file_path, output_dir, chunk_size=CHUNK_SIZE):
    """
    Divides a file into chunks and writes each chunk to an output directory.
    
    :param file_path: Path to the file to be divided
    :param output_dir: Directory to store the chunk files
    :param chunk_size: Size of each chunk in bytes (default 256KB)
    """
    try:
        for chunk_data, chunk_number in divide_file_into_chunks(file_path, chunk_size):
            success = write_chunk_to_file(chunk_data, chunk_number, output_dir)
            if not success:
                print(f"Error writing chunk {chunk_number}. Aborting further processing.")
                break
    except Exception as e:
        print(f"Error during file chunking: {e}")

if __name__ == "__main__":
    # Example Usage:
    file_path = "path_to_your_file"  # Replace with the file you want to chunk
    output_directory = "output_chunks_directory"  # Replace with the desired output directory

    divide_and_save_chunks(file_path, output_directory)
