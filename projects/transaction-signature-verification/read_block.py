from get_blockchain_info import load_block_hex, load_input_references, save_transaction_hex
from decimal import Decimal
from hashlib import sha256

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
    required_txids = {reference["txid"] for reference in input_references}
    block_hashes = {reference["block_hash"] for reference in input_references}
    block_headers = {}
    matched_transactions = {}

    for block_hash in sorted(block_hashes):
        print(f"NEW Block--------------------------------------------------")
        block_bytes = load_block_bytes(block_hash)
        # print(f"{block_bytes[:6].hex(' ')}.... {block_bytes[-6:].hex(' ')}")

        position = 0;
        # print(f"position: {position}")

        block_header_size = 80;
        position += block_header_size

        block_txn_count, block_txn_count_field_size = read_compact_size(position, block_bytes)
        block_txn_count_bytes = block_bytes[block_header_size:block_header_size + block_txn_count_field_size]

        # print(f"Block header bytes: {block_header_size}")
        # print(f"Block txn_count: {block_txn_count}")
        # print(f"Block txn_count bytes: {block_txn_count_field_size}")
        position += block_txn_count_field_size
        # print(f"position: {position}")

        print(f"Going thru all {block_txn_count} transactions in this block:")
        for transaction_index in range(block_txn_count):
            transaction_start = position
            txn_version_size = 4
            # print(f"Transaction version bytes: {txn_version_size}")
            position += txn_version_size
            # print(f"position: {position}")

            txn_input_count, txn_input_count_field_size = read_compact_size(position, block_bytes)
            txn_input_count_bytes = block_bytes[position:position + txn_input_count_field_size]
            # print(f"Transaction txn_input_count: {txn_input_count}")
            # print(f"Transaction txn_input_count_field_size: {txn_input_count_field_size}")
            position += txn_input_count_field_size
            # print(f"position: {position}")

            # print(f"Going thru all {txn_input_count} transaction inputs")
            for input_index in range(txn_input_count):
                previous_output_hash_size = 32
                previous_output_index_size = 4
                # print(f"previous_output_hash_size: {previous_output_hash_size}")
                position += previous_output_hash_size
                # print(f"position: {position}")
                # print(f"previous_output_index_size: {previous_output_index_size}")
                position += previous_output_index_size
                # print(f"position: {position}")

                script_length, script_length_field_size = read_compact_size(position, block_bytes)
                # print(f"script length field size: {script_length_field_size}")
                position += script_length_field_size
                # print(f"position: {position}")
                # print(f"script length: {script_length}")
                position += script_length
                # print(f"position: {position}")

                sequence_size = 4
                # print(f"sequence: {sequence_size}")
                position += sequence_size
                # print(f"position: {position}")

            txn_output_count, txn_output_count_field_size = read_compact_size(position, block_bytes)
            txn_output_count_bytes = block_bytes[position:position + txn_output_count_field_size]
            # print(f"Transaction txn_output_count: {txn_output_count}")
            # print(f"Transaction txn_output_count_field_size: {txn_output_count_field_size}")
            position += txn_output_count_field_size
            # print(f"position: {position}")

            txn_output_amounts = []
            # print(f"Going thru all {txn_output_count} transaction outputs")
            for output_index in range(txn_output_count):
                txn_output_value_size = 8
                txn_output_value_bytes = block_bytes[position:position + txn_output_value_size]
                txn_output_value_amount = int.from_bytes(
                    txn_output_value_bytes,
                    byteorder="little",
                    signed=True,
                )
                txn_output_amounts.append(txn_output_value_amount)
                txn_output_value_btc = Decimal(txn_output_value_amount) / Decimal(100_000_000)
                # print(f"Txn Output value size: {txn_output_value_size}")
                # print(f"Txn Output value bytes: {txn_output_value_bytes}")
                # print(f"Txn Output value amount in satoshis: {txn_output_value_amount}")
                # print(f"Txn Output value amount in bitcoin: {txn_output_value_btc}")
                position += txn_output_value_size
                # print(f"position: {position}")

                txn_output_pk_script_length, txn_output_pk_script_length_field_size = read_compact_size(position, block_bytes)
                # print(f"txn_output_pk_script_length_field_size: {txn_output_pk_script_length_field_size}")
                position += txn_output_pk_script_length_field_size
                # print(f"position: {position}")
                # print(f"txn_output_pk_script_length: {txn_output_pk_script_length}")
                position += txn_output_pk_script_length
                # print(f"position: {position}")

            lock_time_size = 4
            # print(f"lock_time size: {lock_time_size}")
            position += lock_time_size
            # print(f"position: {position}")

            txn_bytes = block_bytes[transaction_start:position]
            first_hash = sha256(txn_bytes).digest()
            second_hash = sha256(first_hash).digest()
            txn_id = second_hash[::-1].hex()
            if txn_id in required_txids:
                matched_transactions[txn_id] = {
                    "output_amounts": txn_output_amounts,
                    "bytes": txn_bytes,
                }
                print(f"Transaction ID: {txn_id}")
                print(f"Output amounts (satoshis): {txn_output_amounts}")
                print(f"position: {position}")

    referenced_outputs = []
    for input_index, reference in enumerate(input_references):
        txn_id = reference["txid"]
        vout = reference["vout"]
        if txn_id not in matched_transactions:
            raise ValueError(f"Referenced transaction not found: {txn_id}")

        output_amounts = matched_transactions[txn_id]["output_amounts"]
        if not 0 <= vout < len(output_amounts):
            raise ValueError(f"Output {vout} does not exist in transaction {txn_id}")
        amount = output_amounts[vout]
        referenced_outputs.append({
            "input_index": input_index,
            "txid": txn_id,
            "vout": vout,
            "amount": amount,
        })
        print(f"Input {input_index}: {txn_id}:{vout} = {amount} satoshis")

    largest_output = max(referenced_outputs, key=lambda output: output["amount"])
    largest_txid = largest_output["txid"]
    largest_txn_bytes = matched_transactions[largest_txid]["bytes"]
    saved_path = save_transaction_hex(largest_txid, largest_txn_bytes.hex())
    largest_amount_btc = Decimal(largest_output["amount"]) / Decimal(100_000_000)

    print("\nLargest referenced output:")
    print(f"Spending input index (starts at 0): {largest_output['input_index']}")
    print(f"Previous transaction ID: {largest_txid}")
    print(f"Previous output index (vout): {largest_output['vout']}")
    print(f"Amount: {largest_output['amount']} satoshis ({largest_amount_btc:.8f} BTC)")
    print(f"Raw transaction saved to: {saved_path}")
