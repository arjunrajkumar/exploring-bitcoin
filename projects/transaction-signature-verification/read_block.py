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


def read_compact_size(start: int, block_bytes: bytes) -> tuple[int, int]:
    """Return the transaction count and the total bytes used by its field."""
    min_limit = start + 1
    if len(block_bytes) < min_limit:
        raise ValueError("Count is missing after the block header.")

    # Format: https://developer.bitcoin.org/reference/transactions.html#compactsize-unsigned-integers
    first_byte = block_bytes[start]
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

    end = start + bytes_count
    if len(block_bytes) < end:
        raise ValueError("Count bytes are incomplete.")

    value = int.from_bytes(block_bytes[min_limit:end], byteorder="little")
    if value < minimum_count:
        raise ValueError("Count uses more bytes than CompactSize permits.")
    return value, bytes_count


if __name__ == "__main__":
    input_references = load_input_references()
    block_hashes = {reference["block_hash"] for reference in input_references}
    block_headers = {}

    for block_hash in sorted(block_hashes):
        block_header_size = 80;
        position = 0
        print(f"position: {position}")
        position += block_header_size

        block_bytes = load_block_bytes(block_hash)
        block_txn_count, block_txn_count_field_size = read_compact_size(position, block_bytes)
        block_txn_count_bytes = block_bytes[block_header_size:block_header_size + block_txn_count_field_size]
        print(f"NEW Block--------------------------------------------------")
        print(f"Block header bytes: {block_header_size}")
        print(f"Block txn_count: {block_txn_count}")
        print(f"Block txn_count bytes: {block_txn_count_field_size}")
        position += block_txn_count_field_size
        print(f"position: {position}")

        print(f"Transactions:")
        first_transaction_start = position
        txn_version_size = 4
        print(f"Transaction version bytes: {txn_version_size}")
        position += txn_version_size
        print(f"position: {position}")

        txn_input_count, txn_input_count_field_size = read_compact_size(position, block_bytes)
        txn_input_count_bytes = block_bytes[position:position + txn_input_count_field_size]
        print(f"Transaction txn_input_count: {txn_input_count}")
        print(f"Transaction txn_input_count_field_size: {txn_input_count_field_size}")
        position += txn_input_count_field_size
        print(f"position: {position}")

        previous_output_hash_size = 32
        previous_output_index_size = 4
        print(f"previous_output_hash_size: {previous_output_hash_size}")
        position += previous_output_hash_size
        print(f"position: {position}")
        print(f"previous_output_index_size: {previous_output_index_size}")
        position += previous_output_index_size
        print(f"position: {position}")

        coinbase_script_length, coinbase_script_length_field_size = read_compact_size(position, block_bytes)
        print(f"Coinbase script length: {coinbase_script_length}")
        position += coinbase_script_length_field_size
        print(f"position: {position}")

        print(f"Coinbase script length field size: {coinbase_script_length_field_size}")
        position += coinbase_script_length
        print(f"position: {position}")

        coinbase_sequence_size = 4
        print(f"Coinbase sequence: {coinbase_sequence_size}")
        position += coinbase_sequence_size
        print(f"position: {position}")

        txn_output_count, txn_output_count_field_size = read_compact_size(position, block_bytes)
        txn_output_count_bytes = block_bytes[position:position + txn_output_count_field_size]
        print(f"Transaction txn_output_count: {txn_output_count}")
        print(f"Transaction txn_output_count_field_size: {txn_output_count_field_size}")
        position += txn_output_count_field_size
        print(f"position: {position}")
