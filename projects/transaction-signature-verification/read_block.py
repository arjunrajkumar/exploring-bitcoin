from get_blockchain_info import load_block_hex, load_input_references


def load_block_bytes(block_hash: str) -> bytes:
    """Read a saved block's hex text and convert it to bytes."""
    block_hex = load_block_hex(block_hash)
    if block_hex is None:
        raise FileNotFoundError(f"No saved block for {block_hash}")
    return bytes.fromhex(block_hex)


def parse_block_header(block_bytes: bytes) -> list[dict]:
    """Split the first 80 bytes into the six header fields."""
    if len(block_bytes) < 80:
        raise ValueError("A block header needs 80 bytes.")

    # Field order and sizes: https://developer.bitcoin.org/reference/block_chain.html#block-headers
    field_layout = [
        (4, "version"),
        (32, "previous block header hash"),
        (32, "merkle root hash"),
        (4, "time"),
        (4, "nBits"),
        (4, "nonce"),
    ]

    header_fields = []
    start = 0
    for bytes_count, name in field_layout:
        end = start + bytes_count
        header_fields.append({
            "bytes_count": bytes_count,
            "name": name,
            "bytes": block_bytes[start:end],
        })
        start = end

    return header_fields


def read_transaction_count(block_bytes: bytes) -> tuple[int, int]:
    """Return the transaction count and the total bytes used by its field."""
    if len(block_bytes) < 81:
        raise ValueError("Transaction count is missing after the block header.")

    # Format: https://developer.bitcoin.org/reference/transactions.html#compactsize-unsigned-integers
    first_byte = block_bytes[80]
    if first_byte < 253:
        return first_byte, 1

    if first_byte == 253:
        bytes_count = 3
        minimum_count = 253
    elif first_byte == 254:
        bytes_count = 5
        minimum_count = 65536
    else:
        bytes_count = 9
        minimum_count = 4294967296

    end = 80 + bytes_count
    if len(block_bytes) < end:
        raise ValueError("Transaction count bytes are incomplete.")

    txn_count = int.from_bytes(block_bytes[81:end], byteorder="little")
    if txn_count < minimum_count:
        raise ValueError("Transaction count uses more bytes than CompactSize permits.")
    return txn_count, bytes_count


if __name__ == "__main__":
    input_references = load_input_references()
    block_hashes = {reference["block_hash"] for reference in input_references}
    block_headers = {}

    for block_hash in sorted(block_hashes):
        block_bytes = load_block_bytes(block_hash)
        txn_count, txn_count_bytes_count = read_transaction_count(block_bytes)
        txn_count_bytes = block_bytes[80:80 + txn_count_bytes_count]
        print(f"Block length: {block_hash}: {len(block_bytes)} bytes")
        print(f"Block header in hex: {block_bytes[:80].hex(' ')}")
        print(f"txn_count compactSize uint as bytes: {txn_count_bytes}")
        print(f"txn_count compactSize uint in hex: {txn_count_bytes.hex(' ')}")
        print(f"txn_count compactSize uint as integer: {txn_count}")
        print(f"txn_count field length: {txn_count_bytes_count} bytes")

        header_fields = parse_block_header(block_bytes)
        block_headers[block_hash] = header_fields
        for field in header_fields:
            print(
                f"{field['name']} ({field['bytes_count']} bytes): "
                f"{field['bytes'].hex(' ')}"
            )
