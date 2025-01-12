# CodeBase Chunker

**CodeBase Chunker** is a Python script that converts an entire codebase into text chunks, staying within a specified character limit. These chunks are easy to copy and paste into Large Language Models (LLMs) like ChatGPT without exceeding the model’s context window. The script supports grouping multiple small files into a single chunk, while large files are automatically split into multiple sub-chunks.

---

## Table of Contents
1. [Features](#features)  
2. [How It Works](#how-it-works)  
3. [Installation](#installation)  
4. [Usage](#usage)  
5. [Configuration](#configuration)  
6. [Example Flow](#example-flow)  
7. [License](#license)  

---

## Features
1. **Automatic Chunking**  
   - Splits large files into multiple sub-chunks if they exceed the configured character limit.  
   - Groups multiple small files into a single chunk if possible, reducing the total number of output files.

2. **Exclusions**  
   - Allows you to **exclude certain file extensions** (e.g., `.png`, `.jpg`, `.exe`).  
   - Allows you to **exclude entire folders** (e.g., `node_modules`, `dist`, `venv`).

3. **Metadata Headers**  
   - Each file or sub-chunk is prefixed with a header comment (e.g., `# here is path/to/file.py`) so the LLM knows which file it’s reading.

4. **Easy to Integrate**  
   - Works on Python 3.x.  
   - You can run it as a standalone script or integrate it into your build pipeline.

---

## How It Works
1. **File Gathering**  
   - Recursively walks the codebase folder.  
   - Skips any file or folder you’ve defined as excluded.

2. **Splitting and Grouping**  
   - If a file exceeds the chunk size, it is split into several sub-chunks.  
   - Each sub-chunk (or entire small file) is appended to a “current chunk” if it fits. Otherwise, a new chunk is started.

3. **Output Files**  
   - Chunks are written out to an output directory.  
   - Files are named in a sequential manner, e.g., `chunk_1_of_5.txt`, `chunk_2_of_5.txt`, etc.

---

## Installation
1. Ensure **Python 3.x** is installed.
2. **Clone** or **download** this repository.
3. Navigate to the repository folder:
   ```bash
   cd codebase-chunker
   ```
4. (Optional) Create a **virtual environment** and install any dependencies if required.  
   *Currently, there are no external dependencies—only the Python standard library is used.*

---

## Usage
1. **Edit the Parameters**  
   Open `codebase_chunker.py` and adjust the parameters at the top of the file as needed:
   ```python
   context_length_for_chunks = 8000
   excluded_file_extensions = [".png", ".jpg", ".jpeg", ".gif", ".zip", ".exe"]
   excluded_folders = ["node_modules", "dist", "venv"]
   ```
2. **Run the Script**  
   ```bash
   python codebase_chunker.py <path_to_codebase> <path_to_output_folder>
   ```
   - Example:
     ```bash
     python codebase_chunker.py ~/my_project ./chunked_output
     ```

3. **Inspect Output**  
   Check the output folder to see `.txt` files like:
   ```
   chunk_1_of_3.txt
   chunk_2_of_3.txt
   chunk_3_of_3.txt
   ```
   Within each file, you’ll find one or more sections (sub-chunks), each starting with `# here is path/to/original_file`.

---

## Configuration
- **`context_length_for_chunks`** *(int)*  
  The approximate character limit for each output chunk file. Defaults to `8000`.

- **`excluded_file_extensions`** *(list of strings)*  
  Files with these extensions will not be included. Defaults to `[ ".png", ".jpg", ".jpeg", ".gif", ".zip", ".exe" ]`.

- **`excluded_folders`** *(list of strings)*  
  Folders with these names will be skipped in the traversal. Defaults to `[ "node_modules", "dist", "venv" ]`.

You can further customize how files are named, the chunk aggregation logic, or the header format to suit your specific needs.

---

## Example Flow
1. You have a project folder named `my_project`, containing:
   ```
   my_project/
   ├── src/
   │   ├── main.py
   │   └── utils.py
   ├── images/
   │   └── diagram.png
   └── README.md
   ```
2. You exclude `.png` files in your parameters.
3. Run the script:
   ```bash
   python codebase_chunker.py my_project chunked_output
   ```
4. The script creates a folder `chunked_output/` and places `chunk_1_of_N.txt`, `chunk_2_of_N.txt`, etc.  
   Each text file is within the configured character limit, and each file’s content starts with a header comment referencing the source file.

---

## License
This project is provided under the **MIT License**. Feel free to modify or distribute as you see fit.

---

**Happy Chunking!** If you have any questions or feedback, please open an issue or submit a pull request.
