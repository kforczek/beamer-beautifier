from typing import List, Iterable


class TokenScanner:
    """Scans a string and divides it by a selected set of tokens. Parts of the string which match no known token
        are returned as one entire string."""
    def __init__(self, *known_tokens: str):
        if not all(token != "" for token in known_tokens):
            raise ValueError("Token cannot be an empty value")

        self._known_tokens = {token: count_containing_tokens(token, known_tokens) for token in known_tokens}

    def tokenize(self, in_str: str) -> List[str]:
        out_tokens = []
        buf = ""
        ignore_until = None
        for pos, char in enumerate(in_str):
            if ignore_until:
                if pos < ignore_until:
                    continue
                ignore_until = None

            buf += char

            for token, larger_cnt in self._known_tokens.items():
                if not buf.endswith(token):
                    continue

                # Is this <token>, or something larger that begins in the same way?
                actual_token = None if larger_cnt < 1 else get_largest_starting_token(in_str[pos-len(token)+1 :], self._known_tokens)

                buf_before_token = buf[:-len(token)]
                if buf_before_token != "":
                    out_tokens.append(buf[:-len(token)])
                buf = ""

                if larger_cnt < 1 or actual_token == token:
                    out_tokens.append(token)
                else:
                    out_tokens.append(actual_token)
                    ignore_until = pos + (len(actual_token) - len(token)) + 1

                break

        if buf != "":
            out_tokens.append(buf)

        return out_tokens


def count_containing_tokens(token: str, all_list: Iterable[str]) -> int:
    """Counts how many times a token appears in the beginning of any non-equal item in a given list."""
    return sum(1 if any_tkn != token and any_tkn.startswith(token) else 0 for any_tkn in all_list)


def get_largest_starting_token(in_str: str, tokens: dict[str, int]) -> str:
    """Returns the largest token found in the beginning of a string."""
    largest_size = 0
    largest_tkn = ""
    for token, larger_cnt in tokens.items():
        if in_str.startswith(token) and len(token) > largest_size:
            if larger_cnt == 0:
                return token  # no larger tokens - no need to look further

            largest_tkn = token
            largest_size = len(token)

    return largest_tkn
