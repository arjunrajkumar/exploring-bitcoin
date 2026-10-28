import hashlib
# Defined by Bitcoin message signing protocol
# Provided by Vanderpoole
text = "I am Vanderpoole and I have control of the private key Satoshi\n"
text += "used to sign the first-ever Bitcoin transaction confirmed in block #170.\n"
text += "This message is signed with the same private key."

def encode_message(text):
    # Given an ascii-encoded text message, serialize a byte array
    # with the Bitcoin protocol prefix string followed by the text
    # and both components preceded by a length byte.
    # Returns a 32-byte hex value.
    prefix = "Bitcoin Signed Message:\n"

    prefix_bytes = prefix.encode("ascii")
    msg_bytes = text.encode("ascii")

    prefix_length = bytes([len(prefix_bytes)])
    msg_length = bytes([len(msg_bytes)])

    encoded_msg = prefix_length + prefix_bytes + msg_length + msg_bytes

    first_hash = hashlib.sha256(encoded_msg).digest()
    second_hash = hashlib.sha256(first_hash).digest()

    return second_hash.hex()
