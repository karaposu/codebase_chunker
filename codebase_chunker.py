import os
import sys

# User-configurable parameters
context_length_for_chunks = 8000
excluded_file_extensions = [".png", ".jpg", ".jpeg", ".gif", ".zip", ".exe"]
excluded_folders = ["node_modules", "dist", "venv"]

def should_exclude_file(file_path):
    """
    Checks if the file should be excluded based on its extension.
    """
    _, ext = os.path.splitext(file_path)
    if ext.lower() in excluded_file_extensions:
        return True
    return False

def should_exclude_folder(folder_path):
    """
    Checks if the folder should be excluded based on folder name.
    """
    for excluded_folder in excluded_folders:
        # A match if the folder name is directly in the path segments
        if excluded_folder in folder_path.split(os.sep):
            return True
    return False

def chunk_text(text, chunk_size):
    """
    Splits a single file's content into sub-chunks of size `chunk_size`.
    Returns a list of sub-chunks.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_file_chunks(file_path):
    """
    Reads a file and returns a list of sub-chunks, each prefixed with
    a metadata header.
    
    If the file content is larger than chunk_size, it will be split up.
    If smaller, it's just one chunk. This function returns them as a list
    so the aggregator can attempt to group multiple small files in one chunk.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split if content is larger than chunk_size
    sub_chunks = chunk_text(content, context_length_for_chunks)

    # Build final list of strings, each prefixed with header
    file_chunks = []
    for sub_chunk in sub_chunks:
        header = f"# here is {file_path}\n\n"
        file_chunks.append(header + sub_chunk)

    return file_chunks

def main():
    if len(sys.argv) < 3:
        print("Usage: python codebase_chunker.py <codebase_root_dir> <output_dir>")
        sys.exit(1)

    codebase_root = sys.argv[1]
    output_dir = sys.argv[2]

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # ----------------------------------------------------
    # 1) Gather all eligible file chunks in a list
    #    (some files become multiple 'sub-chunks' if large)
    # ----------------------------------------------------
    all_file_chunks = []  # will hold strings, each is "header + sub-chunk"

    for root, dirs, files in os.walk(codebase_root):
        # Exclude folders
        if should_exclude_folder(root):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            # Exclude specific file extensions
            if not should_exclude_file(file_path):
                # Convert this file into one or more sub-chunks
                file_chunks = get_file_chunks(file_path)
                all_file_chunks.extend(file_chunks)

    # ----------------------------------------------------
    # 2) Aggregate these sub-chunks into .txt files
    #    as long as they stay under context_length_for_chunks
    # ----------------------------------------------------
    # Note: Each sub-chunk might already be close to chunk_size if it's from a large file.
    # We'll try to group multiple small sub-chunks into a single chunk if possible.
    current_chunk_content = ""
    chunks = []
    for sub_chunk in all_file_chunks:
        # If sub_chunk doesn't fit in current_chunk, start a new chunk
        if len(current_chunk_content) + len(sub_chunk) > context_length_for_chunks:
            if current_chunk_content:
                chunks.append(current_chunk_content)
            current_chunk_content = sub_chunk
        else:
            # Append sub_chunk to current chunk
            current_chunk_content += "\n\n" + sub_chunk if current_chunk_content else sub_chunk

    # If there's leftover content in current_chunk_content, finalize it
    if current_chunk_content:
        chunks.append(current_chunk_content)

    # ----------------------------------------------------
    # 3) Write out the chunks
    # ----------------------------------------------------
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        output_filename = f"chunk_{i}_of_{total_chunks}.txt"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk)

    print(f"Finished generating {total_chunks} chunk(s) in '{output_dir}'.")

if __name__ == "__main__":
    main()

