# Public Bitcoin example data

These files contain public Bitcoin mainnet data for this exercise.
The source is the raw block data Arjun supplied from Bitcoin Core through
`bitcoin-cli getblock` with verbosity `0`. The transaction was copied from
that block and its transaction ID was checked.

- [Block 153509](blocks/00000000000000fb62bbadc0a9dcda556925b2d0c1ad8634253ac2e83ab8382f.hex): 18,577 bytes, stored as hex text.
- [Chosen transaction](transactions/29a3efd3ef04f9153d47a990bd7b048a4b2d213daaa5fb8ed670fb85f13bdbcf.hex): 2,055 bytes, stored as hex text.

The block header hash and transaction ID match the file names.
These checks do not perform the signature verification that this exercise
will implement.

The program reads the saved transaction before looking for its block.
Bitcoin Core must still be running for `decoderawtransaction`.
Pruning in Bitcoin Core does not delete these separate files.

These two example files and the selected previous transaction below are
tracked in Git. Other downloaded files in the `blocks/` and `transactions/`
folders are ignored.

## AI reply

[Input references](input_references.json) lists the 11 previous outputs in
the same order as the chosen transaction's inputs. Each entry contains
`txid`, `vout`, and the containing block's `block_hash`.

The transaction IDs and output indexes were checked against the saved
transaction. The block hashes were looked up on 29 October 2026 with the
[mempool.space transaction status API](https://mempool.space/docs/api/rest#get-transaction-status),
using `https://mempool.space/api/tx/{txid}/status` for each transaction ID.
These are explorer lookup results. Arjun later reported five matching
transaction IDs in the first saved block and six in the second.

Five previous transactions are in
[block 144916](https://mempool.space/block/00000000000005c6aca89f188819553e63fe1d5deeea9722b43d1cd0974c7d58).
The other six are in
[block 144917](https://mempool.space/block/00000000000007fe3e6060ec0c6ddb6790c77a8dc06eea4575a2408eebbf07d0).

### Selected previous transaction

The [selected previous transaction](transactions/3fd4cb75e272a5e68524d15df2d16a7b926d4998c2f1bc60a6f76083eeaba404.hex)
contains 225 bytes, stored as hex text. Its source is block 144917, downloaded
by Bitcoin Core from peers and saved locally. `read_block.py` selects the
largest referenced output and saves the whole transaction that contains it.

Input `0` of the chosen spending transaction references output `0`
(`vout = 0`) of this previous transaction. Both indexes start at `0`.
This file is kept so we can read that output's spending conditions and
verify the signature from the input that spends it.

The saved transaction ID matches its filename. The transaction bytes also
match the saved source block. Signature verification is still to do.
