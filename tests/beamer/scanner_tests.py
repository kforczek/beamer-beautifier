from src.beautifier.scanner import TokenScanner


def test_scanner_1_token():
    scanner = TokenScanner("tkn1")
    values = "something tkn1 abctkn1def"
    tokenized = scanner.tokenize(values)
    assert tokenized == ["something ", "tkn1", " abc", "tkn1", "def"]


def test_scanner_2_tokens():
    scanner = TokenScanner("tkn1", "tkn2")
    values = "something tkn1 ... tkn2tkn1 ....."
    tokenized = scanner.tokenize(values)
    assert tokenized == ["something ", "tkn1", " ... ", "tkn2", "tkn1", " ....."]


def test_scanner_only_1_token():
    scanner = TokenScanner("tkn1")
    values = "tkn1"
    tokenized = scanner.tokenize(values)
    assert tokenized == ["tkn1"]


def test_scanner_only_2_tokens():
    scanner = TokenScanner("tkn1", "tkn2")
    values = "tkn1tkn2"
    tokenized = scanner.tokenize(values)
    assert tokenized == ["tkn1", "tkn2"]


def test_scanner_nested_tokens():
    scanner = TokenScanner("123", "123456", "123456789")
    values = "something 1234 123456 12345678 \n 1234567890"
    tokenized = scanner.tokenize(values)
    assert tokenized == ["something ", "123", "4 ", "123456", " ", "123456", "78 \n ", "123456789", "0"]
