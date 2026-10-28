# Saving Satoshi — Chapter 5: Prepare the message

[Mastering Bitcoin](../../README.md) · [Original exercise](https://savingsatoshi.com/en/chapters/chapter-5/validate-signature-1)

## AI reply

### Problem

Complete `encode_message()` to prepare Vanderpoole's message for signature
verification. Encode the supplied prefix and message as bytes in this order:

```text
[size of prefix][prefix][size of message][message]
```

Apply SHA-256 twice to those bytes. Return the final 32-byte hash as
a 64-character hexadecimal string.

The message text is public example data supplied by Saving Satoshi.

### Submitted code

[Arjun's final Python code](encode_message.py), completed with AI guidance.

The starter text, function comments and prefix come from the exercise.
The submitted code and comments are preserved.

### Recorded run

Arjun ran the code in the Saving Satoshi Python editor.
The screenshot shared on 28 October 2026 at 12:00 (Asia/Kolkata) shows:

```text
Result
73a16290e005b119b9ce0ceea52949f0bd4f925e808b5a54c631702d3fea1242

Evaluation
Nicely Done
```

This is the result of the learner's browser run.
