"""Before running
--------------
1. Bitcoin Core must be running on this computer.
2. This example uses its default macOS data directory.
3. It uses the default mainnet command port, 8332.
4. It uses the temporary login file that Bitcoin Core creates.
5. Use Python 3.9 or newer. No package install is needed.

Run from the repository root
----------------------------
python3 projects/transaction-signature-verification/get_blockchain_info.py

File structure
--------------
This is one small program, so its functions stay in one file.
Read main() first to see the entry point.
Then follow get_blockchain_info() and the helper functions it calls.
Each function has one purpose: login, request, response, API call, or output.
Function names use snake_case. Constants use UPPER_CASE.
The type hints describe the expected arguments and return values.
For example, -> bytes means that a function returns bytes.

References
----------
API: https://bitcoincore.org/en/doc/24.0.0/rpc/blockchain/getblockchaininfo/
Python style: https://peps.python.org/pep-0008/
Entry point: https://docs.python.org/3/library/__main__.html
"""

# All imports below come from Python's standard library.
import base64  # Encode the login as text for HTTP Basic authentication.
import json  # Convert between Python objects and JSON text.
import sys  # Print errors to stderr, the terminal's error output.
from http.client import HTTPConnection, HTTPException
from pathlib import Path  # Build paths and read files.
from typing import Any  # A JSON result can contain several value types.


# These are default connection settings, not credentials.
# HTTP is the request-and-response protocol also used by websites.
RPC_HOST = "127.0.0.1"  # This computer.
RPC_PORT = 8332  # Mainnet API port. Peer traffic uses a different port.
RPC_TIMEOUT_SECONDS = 30  # Limit socket waits.

# Path.home() gives the home folder of the user running the program.
# The / operator joins Path objects and folder names.
COOKIE_PATH = Path.home() / "Library/Application Support/Bitcoin/.cookie"


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


def parse_rpc_response(status: int, body: bytes) -> dict[str, Any]:
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
        raise RuntimeError(f"Bitcoin Core API error: {error}")
    if status != 200:
        raise RuntimeError(f"Bitcoin Core returned HTTP {status}.")

    # A successful getblockchaininfo result must be a dictionary.
    result = reply.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(
            "Bitcoin Core did not return blockchain information."
        )
    return result


def get_blockchain_info() -> dict[str, Any]:
    """Request blockchain information from the local node."""
    authorization = read_authorization_header(COOKIE_PATH)
    # This function chooses the command. getblockchaininfo takes no arguments.
    request_body = build_request_body(method="getblockchaininfo", params=[])
    connection = HTTPConnection(
        RPC_HOST, RPC_PORT, timeout=RPC_TIMEOUT_SECONDS
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


def main() -> int:
    """Print the result or an error, and return a command exit code."""
    # Only main() handles terminal output and the command's exit status.
    # Helper functions return data or raise errors for main() to handle.
    try:
        info = get_blockchain_info()
    except FileNotFoundError:
        print(
            "Login file not found. Check that Bitcoin Core is running.",
            file=sys.stderr,
        )
        return 1
    except (OSError, HTTPException, RuntimeError) as error:
        print(
            f"Could not get blockchain information: {error}",
            file=sys.stderr,
        )
        return 1

    # indent=2 makes the JSON output easier to read.
    print(json.dumps(info, indent=2))
    return 0


# Run main() only when this file is executed directly.
# Importing this file from another program will not call the node.
# Exit code 0 means success. Exit code 1 means failure.
if __name__ == "__main__":
    sys.exit(main())
