# Saving Satoshi — Chapter 5: Prepare the signature

[Mastering Bitcoin](../../README.md) · [Original exercise](https://savingsatoshi.com/en/chapters/chapter-5/validate-signature-2)

## AI reply

### Problem

Complete `decode_sig()` to prepare Vanderpoole's signature for verification.
Decode the Base64 signature into 65 bytes.
Discard the first byte of metadata for this exercise.
The next 32 bytes contain `r`, and the final 32 bytes contain `s`.
Return `(r, s)` as a tuple of integers.

The signature is public example data supplied by Saving Satoshi.

### Submitted code

[Arjun's final Python code](decode_sig.py), completed with AI guidance.

The signature value comes from the exercise.
The submitted code and comment are preserved.

### Recorded run

Arjun ran the code in the Saving Satoshi Python editor.
The screenshot shared on 28 October 2026 at 12:16 (Asia/Kolkata) shows:

```text
Result
(63239744615459417534795088953002824328865520877888079618399827727977035042153, 28508663025799969786676261677335521233963265910413171955666154169583931328457)

Evaluation
Nicely Done
```

This is the result of the learner's browser run.
