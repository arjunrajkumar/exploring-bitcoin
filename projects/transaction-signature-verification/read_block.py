from get_blockchain_info import load_block_hex, load_input_references, save_transaction_hex
from decimal import Decimal
from read_transaction import read_compact_size, read_transaction

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
            transaction, position = read_transaction(position, block_bytes)
            txn_id = transaction["txid"]
            txn_output_amounts = transaction["output_amounts"]
            if txn_id in required_txids:
                matched_transactions[txn_id] = transaction
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
