from app.services.webhook_security import body_sha256, generate_signature, verify_signature

def test_hmac_signature_round_trip():
    body = b'{"event":"ping","value":1}'
    signature = generate_signature(body, "secret")
    assert signature.startswith("sha256=")
    assert verify_signature(body, signature, "secret")
    assert not verify_signature(body, signature, "wrong-secret")

def test_hmac_rejects_modified_body():
    signature = generate_signature(b'{"ok":true}', "secret")
    assert not verify_signature(b'{"ok":false}', signature, "secret")

def test_body_hash_is_stable():
    body = b"hello"
    assert body_sha256(body) == body_sha256(body)
