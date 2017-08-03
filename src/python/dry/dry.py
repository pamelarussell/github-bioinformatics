
# Get code chunks and put into data structure
def add_chunks(lines, chunks_dict, chunk_size, min_line_len):
    if(chunk_size < 1):
        raise ValueError("Chunk size must be positive")
    nlines = len(lines)
    for i in range(nlines - chunk_size + 1):
        chunk = lines[i:i+chunk_size]
        # Make sure all lines in the chunk are long enough
        if all(len(line) >= min_line_len for line in chunk):
            chunk_join = "\n".join(lines[i:i+chunk_size])
            if chunk_join in chunks_dict:
                prev_count = chunks_dict[chunk_join]
                chunks_dict[chunk_join] = prev_count + 1
            else:
                chunks_dict[chunk_join] = 1

# Create pushable records from dict of code chunks
def make_records(repo_name, chunks_dict):
    return [{'repo_name': repo_name, 'code_chunk': chunk, 'num_occurrences': n} for chunk, n in chunks_dict.items()]

# Split into list of lines
def split_into_lines(file_str):
    lines = file_str.split("\n")
    # Strip leading and trailing whitespace
    lines = map(lambda x: x.strip(), lines)
    # Remove empty lines
    lines = list(filter(lambda x: len(x) > 0, lines))
    return lines

