from decimal import Decimal
from hashlib import sha256

from get_blockchain_info import load_transaction_hex


def read_compact_size(start: int, data: bytes) -> tuple[int, int]:
    """Return a CompactSize value and the total bytes used by its field."""
    min_limit = start + 1
    if start < 0 or len(data) < min_limit:
        raise ValueError("CompactSize value is missing.")

    # Format: https://developer.bitcoin.org/reference/transactions.html#compactsize-unsigned-integers
    first_byte = data[start]
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
    if len(data) < end:
        raise ValueError("Count bytes are incomplete.")

    value = int.from_bytes(data[min_limit:end], byteorder="little")
    if value < minimum_count:
        raise ValueError("Count uses more bytes than CompactSize permits.")
    return value, bytes_count


def read_transaction(start: int, data: bytes) -> tuple[dict, int]:
    """Read one old-format transaction and return its data and next byte index."""
    if start < 0 or start + 4 > len(data):
        raise ValueError("Transaction version bytes are incomplete.")
    position = start
    transaction_start = position
    txn_version_size = 4
    # print(f"Transaction version bytes: {txn_version_size}")
    position += txn_version_size
    # print(f"position: {position}")

    txn_input_count, txn_input_count_field_size = read_compact_size(position, data)
    txn_input_count_bytes = data[position:position + txn_input_count_field_size]
    # print(f"Transaction txn_input_count: {txn_input_count}")
    # print(f"Transaction txn_input_count_field_size: {txn_input_count_field_size}")
    position += txn_input_count_field_size
    if txn_input_count == 0:
        raise ValueError("Only the old transaction format with at least one input is supported.")
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

        script_length, script_length_field_size = read_compact_size(position, data)
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

    txn_output_count, txn_output_count_field_size = read_compact_size(position, data)
    txn_output_count_bytes = data[position:position + txn_output_count_field_size]
    # print(f"Transaction txn_output_count: {txn_output_count}")
    # print(f"Transaction txn_output_count_field_size: {txn_output_count_field_size}")
    position += txn_output_count_field_size
    # print(f"position: {position}")

    txn_output_amounts = []
    txn_output_scripts = []
    # print(f"Going thru all {txn_output_count} transaction outputs")
    for output_index in range(txn_output_count):
        txn_output_value_size = 8
        txn_output_value_bytes = data[position:position + txn_output_value_size]
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

        txn_output_pk_script_length, txn_output_pk_script_length_field_size = read_compact_size(position, data)
        # print(f"txn_output_pk_script_length_field_size: {txn_output_pk_script_length_field_size}")
        position += txn_output_pk_script_length_field_size
        # print(f"position: {position}")
        # print(f"txn_output_pk_script_length: {txn_output_pk_script_length}")
        txn_output_script = data[position:position + txn_output_pk_script_length]
        txn_output_scripts.append(txn_output_script)
        position += txn_output_pk_script_length
        # print(f"position: {position}")

    lock_time_size = 4
    # print(f"lock_time size: {lock_time_size}")
    position += lock_time_size
    # print(f"position: {position}")

    if position > len(data):
        raise ValueError("Transaction bytes are incomplete.")

    txn_bytes = data[transaction_start:position]
    first_hash = sha256(txn_bytes).digest()
    second_hash = sha256(first_hash).digest()
    txn_id = second_hash[::-1].hex()
    return {
        "txid": txn_id,
        "output_amounts": txn_output_amounts,
        "output_scripts": txn_output_scripts,
        "bytes": txn_bytes,
    }, position


if __name__ == "__main__":
    transaction_id = "3fd4cb75e272a5e68524d15df2d16a7b926d4998c2f1bc60a6f76083eeaba404"
    vout = 0
    transaction_hex = load_transaction_hex(transaction_id)
    if transaction_hex is None:
        raise FileNotFoundError(f"No saved transaction for {transaction_id}")

    transaction_bytes = bytes.fromhex(transaction_hex)
    transaction, position = read_transaction(0, transaction_bytes)
    if position != len(transaction_bytes):
        raise ValueError("Unexpected bytes after the saved transaction.")
    if transaction["txid"] != transaction_id:
        raise ValueError("Saved transaction ID does not match its filename.")
    if not 0 <= vout < len(transaction["output_scripts"]):
        raise ValueError(f"Output {vout} does not exist in transaction {transaction_id}")

    output_script = transaction["output_scripts"][vout]
    print(f"Transaction ID: {transaction_id}")
    print(f"Output {vout} script (hex): {output_script.hex()}")
