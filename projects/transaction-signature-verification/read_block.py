from get_blockchain_info import load_block_hex, load_input_references


def load_block_bytes(block_hash: str) -> bytes:
    """Read a saved block's hex text and convert it to bytes."""
    block_hex = load_block_hex(block_hash)
    if block_hex is None:
        raise FileNotFoundError(f"No saved block for {block_hash}")
    return bytes.fromhex(block_hex)


if __name__ == "__main__":
    input_references = load_input_references()
    block_hashes = {reference["block_hash"] for reference in input_references}

    for block_hash in sorted(block_hashes):
        block_bytes = load_block_bytes(block_hash)
        print(f"Block {block_hash}: {len(block_bytes)} bytes")
