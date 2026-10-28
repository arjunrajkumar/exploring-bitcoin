import secp256k1py.secp256k1 as SECP256K1

# View the library source code
# https://github.com/saving-satoshi/secp256k1py/blob/main/secp256k1py/secp256k1.py

GE = SECP256K1.GE
G = SECP256K1.G

# Message digest from the "Hash the message" lesson:
msg = 0x7a05c6145f10101e9d6325494245adf1297d80f8f38d4d576d57cdba220bcb19

# Signature values from the "Decode the signature" lesson:
sig_r = 0x4e45e16932b8af514961a1d3a1a25fdf3f4f7732e9d624c6c61548ab5fb8cd41
sig_s = 0x181522ec8eca07de4860a4acdd12909d831cc56cbbac4622082221a8768d1d09

# Public key values from the "Decode the public key" lesson:
pubkey_x = 0x11db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c
pubkey_y = 0xb2e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3

def verify(sig_r, sig_s, pubkey_x, pubkey_y, msg):
    # Verify an ECDSA signature given a public key and a message.
    # All input values will be 32-byte integers.

    # Start by creating a curve point representation of the public key
    # this returns a point (x, y) that lies on the secp256k1 elliptic curve.
    key = GE(pubkey_x, pubkey_y)

    # check the range limits of the signature values (Both must be between 1 and n-1)
    n = GE.ORDER
    if sig_r == 0 or sig_r >= n:
        print("invalid r value")
        return False
    if sig_s == 0 or sig_s >= n:
        print("invalid s value")
        return False

    # Implement ECDSA and return a boolean
    # The Math:
    #   u1 = m / s mod n
    #   u2 = r / s mod n
    #   R = G * u1 + A * u2
    #   r == x(R) mod n
    # Hints:
    #   n = the order of the curve GE.ORDER
    #   s, r = sig_s and sig_r, the two components of an ECDSA signature
    #   m = msg, the message to sign
    #   A = key, a key point constructed from pubkey_x and pubkey_y
    #   Use the python's built-in pow() function to invert s and turn division into multiplication!

    # from n, find its bit length. Call it length L
    L = n.bit_length()

    # check msg hash with L. Keep the first L bits of the hash if the hash is longer. Otherwise, keep the whole hash.
    # msg is already an integer. Integers do not remember their original byte length.
    # but the instructions specify 32-byte inputs.
    hashlen = 32
    hash_bits = hashlen * 8  # 256 bits
    z = msg
    if hash_bits > L:
        z = msg >> (hash_bits - L)

    # Calculate the multipliers u_1 and u_2. u_1 tells us how many copies of the genrator to add. u_2 tells us how many copies of the key to add.
    s_inv = pow(sig_s, -1, n)
    u1 = (z * s_inv) % n
    u2 = (sig_r * s_inv) % n

    # Calculate the point R
    R = u1 * G + u2 * key

    # If R = O (special point at infintiy), reject
    if R.infinity: return False

    # Compare the remainder with sig_r using R's x cordinate and n as inputs
    # Return true if they match, else false.
    return int(R.x) % n == sig_r
