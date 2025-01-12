import os
import sys

# -----------------------------------------------
# User-configurable parameters
# -----------------------------------------------
context_length_for_chunks = 8000

# Exclude files by extension
excluded_file_extensions = [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".zip",
    ".exe",
    ".db"
]

# Exclude files by exact filename
excluded_filenames = [
    ".DS_Store",
    "Dockerfile",
    ".gitignore"
]

# Exclude folders by name
excluded_folders = [
    ".git",
    ".github",
    ".idea",
    "node_modules",
    "dist",
    "venv",
    ".venv"
]


def should_exclude_file(file_path):
    """
    Checks if the file should be excluded based on:
      - Exact filename
      - File extension
    """
    file_name = os.path.basename(file_path)
    # Check exact filename
    if file_name in excluded_filenames:
        return True

    # Check extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() in excluded_file_extensions:
        return True

    return False


def should_exclude_folder(folder_path):
    """
    Checks if the folder should be excluded if it contains any
    of the folder names in 'excluded_folders' as a path segment.
    """
    parts = folder_path.split(os.sep)
    for excluded_folder in excluded_folders:
        if excluded_folder in parts:
            return True
    return False


def chunk_text(text, chunk_size):
    """
    Splits a single string into sub-chunks of size `chunk_size`.
    Returns a list of sub-chunks (strings).
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# -----------------------------------------------------------------------------
# 1) Build a "tree" output that mirrors the 'tree' command, excluding ignored items
# -----------------------------------------------------------------------------
def build_tree_output(base_path):
    """
    Recursively builds a textual 'tree' view of the directory,
    skipping excluded files and folders.
    Returns a single string that can be chunked later if needed.
    """
    lines = []
    _build_tree_lines(base_path, lines, prefix="", is_last=True, is_root=True)
    return "\n".join(lines)


def _build_tree_lines(current_path, lines, prefix="", is_last=False, is_root=False):
    """
    Helper for 'build_tree_output' that appends lines to the 'lines' list.
    Uses box-drawing characters (├──, └──, etc.) to simulate a tree view.
    """
    if is_root:
        # Print the root folder name
        lines.append(os.path.basename(current_path.rstrip(os.sep)))
    else:
        # Determine the correct branch symbol
        branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{branch}{os.path.basename(current_path.rstrip(os.sep))}")

    # If it's a directory, recursively process its children
    if os.path.isdir(current_path) and not should_exclude_folder(current_path):
        # Gather children, exclude those that shouldn't be visible
        items = sorted(os.listdir(current_path))
        # Filter out excluded items
        visible_items = []
        for item in items:
            full_path = os.path.join(current_path, item)
            # If it's a directory, exclude if in excluded_folders
            # If it's a file, exclude if in excluded_filenames/extensions
            if os.path.isdir(full_path):
                if not should_exclude_folder(full_path):
                    visible_items.append(item)
            else:
                if not should_exclude_file(full_path):
                    visible_items.append(item)

        # For each child, recurse
        for i, child in enumerate(visible_items):
            child_path = os.path.join(current_path, child)
            # Determine if last item
            child_is_last = (i == len(visible_items) - 1)
            # Update prefix for children
            new_prefix = prefix + ("    " if is_last else "│   ")
            _build_tree_lines(child_path, lines, prefix=new_prefix, is_last=child_is_last)


# -----------------------------------------------------------------------------
# 2) Convert each eligible file into sub-chunks with file headers
# -----------------------------------------------------------------------------
def get_file_chunks(file_path):
    """
    Reads a file and returns a list of sub-chunks, each prefixed with
    a metadata header to identify the file.

    If the file content is larger than `context_length_for_chunks`,
    it will be split into multiple sub-chunks.
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

    # -------------------------------------------------------------------------
    # 1) Build the tree output for the entire codebase (excluding ignored items)
    # -------------------------------------------------------------------------
    tree_string = build_tree_output(os.path.abspath(codebase_root))
    tree_header = "# Here is the tree of the project (excluded items omitted):\n\n"
    tree_full_output = tree_header + tree_string

    # Possibly chunk the tree output if it's very large
    tree_subchunks = chunk_text(tree_full_output, context_length_for_chunks)

    # -------------------------------------------------------------------------
    # 2) Gather all eligible file chunks
    # -------------------------------------------------------------------------
    all_file_chunks = []  # Will hold strings, each is "header + sub-chunk"
    for root, dirs, files in os.walk(codebase_root):
        # Exclude folders
        if should_exclude_folder(root):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            # Exclude specific files
            if not should_exclude_file(file_path):
                # Convert this file into one or more sub-chunks
                file_chunks = get_file_chunks(file_path)
                all_file_chunks.extend(file_chunks)

    # -------------------------------------------------------------------------
    # 3) Aggregate all sub-chunks (first the tree, then the code) into final chunks
    # -------------------------------------------------------------------------
    # We'll create a function that tries to group sub-chunks under the limit
    def aggregate_chunks(subchunks):
        """
        Given a list of sub-chunks (strings), group them so each group
        is within the context_length_for_chunks. Return a list of grouped strings.
        """
        current_chunk_content = ""
        grouped = []
        for sc in subchunks:
            if len(current_chunk_content) + len(sc) > context_length_for_chunks:
                if current_chunk_content:
                    grouped.append(current_chunk_content)
                current_chunk_content = sc
            else:
                if current_chunk_content:
                    current_chunk_content += "\n\n" + sc
                else:
                    current_chunk_content = sc
        if current_chunk_content:
            grouped.append(current_chunk_content)
        return grouped

    # First, gather the tree sub-chunks
    tree_chunks = aggregate_chunks(tree_subchunks)
    # Then gather the file sub-chunks
    code_chunks = aggregate_chunks(all_file_chunks)

    # Combine them: tree chunks first, then code
    final_chunks = tree_chunks + code_chunks

    # -------------------------------------------------------------------------
    # 4) Write out the chunks to separate files
    # -------------------------------------------------------------------------
    total_chunks = len(final_chunks)
    for i, chunk in enumerate(final_chunks, start=1):
        output_filename = f"chunk_{i}_of_{total_chunks}.txt"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk)

    print(f"Finished generating {total_chunks} chunk(s) in '{output_dir}'.")


if __name__ == "__main__":
    main()
