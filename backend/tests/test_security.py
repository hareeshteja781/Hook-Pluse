from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

def test_password_hash_round_trip():
    password = "StrongPass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass123!", hashed)

def test_access_token_round_trip():
    token = create_access_token("user@example.com")
    assert decode_access_token(token) == "user@example.com"

def test_invalid_token_returns_none():
    assert decode_access_token("not-a-token") is None
