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

These two example files are tracked in Git. Other downloaded files in the
`blocks/` and `transactions/` folders are ignored.

## AI reply

[Input references](input_references.json) lists the 11 previous outputs in
the same order as the chosen transaction's inputs. Each entry contains
`txid`, `vout`, and the containing block's `block_hash`.

The transaction IDs and output indexes were checked against the saved
transaction. The block hashes were looked up on 29 October 2026 with the
[mempool.space transaction status API](https://mempool.space/docs/api/rest#get-transaction-status),
using `https://mempool.space/api/tx/{txid}/status` for each transaction ID.
These are explorer lookup results. We will check the transactions against
blocks from Bitcoin Core in a later step.

Five previous transactions are in
[block 144916](https://mempool.space/block/00000000000005c6aca89f188819553e63fe1d5deeea9722b43d1cd0974c7d58).
The other six are in
[block 144917](https://mempool.space/block/00000000000007fe3e6060ec0c6ddb6790c77a8dc06eea4575a2408eebbf07d0).
