from app.auth.security import hash_password, verify_password


def test_hash_password_round_trip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_is_not_plaintext():
    hashed = hash_password("secret")
    assert hashed != "secret"
