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
