import base64

# Vanderpoole's signature
vp_sig = "H4vQbVD0pLK7pkzPto8BHourzsBrHMB3Qf5oYVmr741pPwdU2m6FaZZmxh4ScHxFoDelFC9qG0PnAUl5qMFth8k="

def decode_sig(vp_sig):
    sig_bytes = base64.b64decode(vp_sig)
    sig_bytes = sig_bytes[1:]

    r = sig_bytes[0:32]
    s = sig_bytes[32:]

    return (int.from_bytes(r, "big"), int.from_bytes(s, "big"))
