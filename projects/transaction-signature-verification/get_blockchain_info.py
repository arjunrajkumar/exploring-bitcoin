# All imports below come from Python's standard library.
import base64  # Encode the login as text for HTTP Basic authentication.
import json  # Convert between Python objects and JSON text.
import sys  # Print errors to stderr, the terminal's error output.
import time  # Measure elapsed time and pause between checks.
from http.client import HTTPConnection, HTTPException
from pathlib import Path  # Build paths and read files.
from typing import Any, Optional  # Optional allows a return value of None.


# These are default connection settings, not credentials.
# HTTP is the request-and-response protocol also used by websites.
RPC_HOST = "127.0.0.1"  # This computer.
RPC_PORT = 8332  # Mainnet API port. Peer traffic uses a different port.
RPC_TIMEOUT_SECONDS = 30  # Limit socket waits.
BLOCK_WAIT_TIMEOUT_SECONDS = 60  # Limit the block request and checking loop.
BLOCK_POLL_INTERVAL_SECONDS = 2  # Pause between checks of local block data.

# Path.home() gives the home folder of the user running the program.
# The / operator joins Path objects and folder names.
COOKIE_PATH = Path.home() / "Library/Application Support/Bitcoin/.cookie"


class BitcoinRPCError(RuntimeError):
    """Keep the API error code and message so callers can handle known errors."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Bitcoin Core API error {code}: {message}")


def read_authorization_header(cookie_path: Path) -> str:
    """Prepare the HTTP login header from Bitcoin Core's cookie file."""
    # .cookie contains a temporary username and password, separated by a colon.
    # This is a local file. It is not a browser cookie.
    # strip() removes whitespace around the login text.
    cookie = cookie_path.read_text(encoding="utf-8").strip()

    # Encode the login bytes as Base64, then convert that result to text.
    # Base64 is an encoding. It does not encrypt the login.
    # Keep this value in memory. Do not print it or copy it into this script.
    encoded_login = base64.b64encode(cookie.encode("utf-8")).decode("ascii")
    return f"Basic {encoded_login}"


def build_request_body(method: str, params: list[Any]) -> bytes:
    """Build JSON request bytes for the supplied method and arguments."""
    # jsonrpc: the request format used by Bitcoin Core 24.0.1.
    #          This is not the Bitcoin network protocol version.
    # id: a label returned with the response to identify this API call.
    #     This is not a transaction ID or peer ID.
    #     We use the method name because this script makes one call at a time.
    # method: the Bitcoin Core command we want to call.
    # params: the arguments supplied by the calling function.
    request = {
        "jsonrpc": "1.0",
        "id": method,
        "method": method,
        "params": params,
    }

    # dumps() turns the dictionary into JSON text.
    # encode() turns that text into bytes for the HTTP request body.
    return json.dumps(request).encode("utf-8")


def parse_rpc_response(status: int, body: bytes) -> Any:
    """Return the API result, or raise an error describing the failure."""
    # HTTP 401 means authentication failed. HTTP 403 means access was refused.
    if status in (401, 403):
        raise RuntimeError(f"Bitcoin Core refused the login: HTTP {status}.")

    # loads() converts JSON bytes into Python objects. JSON null becomes None.
    # Some HTTP failures return plain text instead of JSON.
    try:
        reply = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError(
            f"Bitcoin Core returned HTTP {status} without valid JSON."
        ) from error

    if not isinstance(reply, dict):
        raise RuntimeError("Expected a JSON object from Bitcoin Core.")

    # An API error can arrive with an HTTP error status.
    # Read its details before checking the remaining HTTP status.
    error = reply.get("error")
    if error is not None:
        if (
            isinstance(error, dict)
            and isinstance(error.get("code"), int)
            and isinstance(error.get("message"), str)
        ):
            raise BitcoinRPCError(error["code"], error["message"])
        raise RuntimeError(f"Bitcoin Core API error: {error}")
    if status != 200:
        raise RuntimeError(f"Bitcoin Core returned HTTP {status}.")

    # The result type depends on the command we called.
    # Each command's function checks that type after this step.
    if "result" not in reply:
        raise RuntimeError("Bitcoin Core did not return a result.")
    return reply["result"]


def send_request(
    request_body: bytes, timeout_seconds: float = RPC_TIMEOUT_SECONDS
) -> Any:
    """Send a prepared request to the local node and return its result."""
    authorization = read_authorization_header(COOKIE_PATH)
    connection = HTTPConnection(
        RPC_HOST, RPC_PORT, timeout=timeout_seconds
    )

    # The network connection starts when request() runs.
    # POST sends our request body. / is the root API path.
    # HTTP headers describe the body format and provide the login.
    try:
        connection.request(
            "POST",
            "/",
            body=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": authorization,
            },
        )
        # getresponse() reads the HTTP status and headers.
        # read() reads the response body as bytes.
        response = connection.getresponse()
        return parse_rpc_response(response.status, response.read())
    finally:
        # Close the connection on success and on failure.
        connection.close()


def get_block_hash(block_height: int) -> str:
    """Return the block hash at the given height in the node's active chain."""
    # The height is an integer. JSON sends it as a number, without quotes.
    request_body = build_request_body(method="getblockhash", params=[block_height])
    result = send_request(request_body)

    # getblockhash returns a string, unlike getblockchaininfo's dictionary.
    if not isinstance(result, str):
        raise RuntimeError("Bitcoin Core did not return a block hash.")
    return result


def get_peer_info() -> list[dict[str, Any]]:
    """Return information about peers connected to our node."""
    # getpeerinfo needs no arguments, so params is an empty list.
    request_body = build_request_body(method="getpeerinfo", params=[])
    result = send_request(request_body)

    # A JSON array becomes a Python list. Each peer is a dictionary.
    # An empty list is valid: the node may have no connected peers.
    if not isinstance(result, list) or not all(
        isinstance(peer, dict) for peer in result
    ):
        raise RuntimeError("Bitcoin Core did not return a list of peer objects.")
    return result


def find_network_peer(peers: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Return the first peer that lists NETWORK, or None if no peer matches."""
    for peer in peers:
        # in checks for an exact list value. NETWORK_LIMITED alone will not match.
        # get() uses an empty list if the servicesnames key is absent.
        if "NETWORK" in peer.get("servicesnames", []):
            return peer

    # None means no match. It is similar to nil in Ruby.
    return None


def get_raw_block(
    block_hash: str, timeout_seconds: float = RPC_TIMEOUT_SECONDS
) -> Optional[str]:
    """Return the local block as hex text, or None if its data is unavailable."""
    # 0 asks for the complete block as hex, without decoding its transactions.
    request_body = build_request_body(method="getblock", params=[block_hash, 0])
    try:
        result = send_request(request_body, timeout_seconds=timeout_seconds)
    except BitcoinRPCError as error:
        # Core 24 uses -1 for these missing-data errors. Other errors must stop us.
        if error.code == -1 and error.message in (
            "Block not available (pruned data)",
            "Block not found on disk",
        ):
            return None
        raise

    if not isinstance(result, str):
        raise RuntimeError("Bitcoin Core did not return raw block hex text.")
    return result


def request_block_from_peer(
    block_hash: str, peer_id: int, timeout_seconds: float = RPC_TIMEOUT_SECONDS
) -> None:
    """Ask our node to fetch this block from the selected peer."""
    request_body = build_request_body(
        method="getblockfrompeer", params=[block_hash, peer_id]
    )
    try:
        result = send_request(request_body, timeout_seconds=timeout_seconds)
    except BitcoinRPCError as error:
        # A previous run may already have requested it, or it may have just arrived.
        # In either case, we still check local storage for the actual block.
        if error.code == -1 and error.message in (
            "Already requested from this peer",
            "Block already downloaded",
        ):
            return
        raise

    # {} means the request was scheduled. It does not confirm receipt of the block.
    if result != {}:
        raise RuntimeError("Bitcoin Core returned an unexpected block request result.")


def remaining_block_wait_seconds(deadline: float) -> float:
    """Return the remaining wait time, or stop when the deadline is reached."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Time limit reached while waiting for the block.")
    return remaining


def fetch_block_from_peer(
    block_hash: str,
    peer_id: int,
    timeout_seconds: float = BLOCK_WAIT_TIMEOUT_SECONDS,
    poll_interval_seconds: float = BLOCK_POLL_INTERVAL_SECONDS,
) -> str:
    """Request a missing block once, then wait for its local hex data."""
    if timeout_seconds <= 0 or poll_interval_seconds <= 0:
        raise ValueError("The timeout and check interval must be positive.")

    # monotonic() measures elapsed time without changes to the computer's clock.
    deadline = time.monotonic() + timeout_seconds
    requested = False
    while True:
        remaining = remaining_block_wait_seconds(deadline)
        block_hex = get_raw_block(
            block_hash, timeout_seconds=min(RPC_TIMEOUT_SECONDS, remaining)
        )
        remaining_block_wait_seconds(deadline)
        if block_hex is not None:
            return block_hex

        if not requested:
            remaining = remaining_block_wait_seconds(deadline)
            request_block_from_peer(
                block_hash, peer_id,
                timeout_seconds=min(RPC_TIMEOUT_SECONDS, remaining),
            )
            requested = True

        remaining = remaining_block_wait_seconds(deadline)
        time.sleep(min(poll_interval_seconds, remaining))


def main() -> int:
    """Print the result or an error, and return a command exit code."""
    # Only main() handles terminal output and the command's exit status.
    # Helper functions return data or raise errors for main() to handle.
    block_height = 153509
    try:
        block_hash = get_block_hash(block_height)
        block_hex = get_raw_block(block_hash)
        print(f"\nBlock hash at height {block_height}: {block_hash}")
        if block_hex is None:
            peers = get_peer_info()
            selected_peer = find_network_peer(peers)
            if selected_peer is None:
                print("No connected peer lists NETWORK.", file=sys.stderr)
                return 1
            print("\nSelected peer:")
            print(json.dumps(selected_peer, indent=2))
            print(
                f"\nChecking for the block for up to {BLOCK_WAIT_TIMEOUT_SECONDS} seconds."
                f" If missing, requesting it from peer {selected_peer['id']}.",
                flush=True,
            )
            block_hex = fetch_block_from_peer(block_hash, selected_peer["id"])
    except FileNotFoundError:
        print(
            "Login file not found. Check that Bitcoin Core is running.",
            file=sys.stderr,
        )
        return 1
    except (OSError, HTTPException, RuntimeError) as error:
        print(
            f"Bitcoin Core request failed: {error}",
            file=sys.stderr,
        )
        return 1
    print(f"\nBlock available locally ({len(block_hex) // 2} bytes).")
    print("\nRaw block (hex text):")
    print(block_hex)
    return 0


# Run main() only when this file is executed directly.
# Importing this file from another program will not call the node.
# Exit code 0 means success. Exit code 1 means failure.
if __name__ == "__main__":
    sys.exit(main())
