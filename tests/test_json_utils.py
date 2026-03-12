from __future__ import annotations

import unittest

from utils.json_utils import LLMResponseParseError, parse_json_response


class TestJsonUtils(unittest.TestCase):
    def test_parse_plain_json(self) -> None:
        parsed = parse_json_response('{"items": []}', context="test")
        self.assertEqual(parsed, {"items": []})

    def test_parse_fenced_json(self) -> None:
        response = """```json
{"clusters": []}
```"""
        parsed = parse_json_response(response, context="test")
        self.assertEqual(parsed, {"clusters": []})

    def test_parse_invalid_json_raises(self) -> None:
        with self.assertRaises(LLMResponseParseError):
            parse_json_response("not json", context="test")


if __name__ == "__main__":
    unittest.main()
