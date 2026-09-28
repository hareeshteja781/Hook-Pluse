import hashlib
import hmac
import json

def canonical_json(payload: object) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")

def generate_signature(raw_body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    expected = generate_signature(raw_body, secret)
    return hmac.compare_digest(expected, signature.strip())

def body_sha256(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()
