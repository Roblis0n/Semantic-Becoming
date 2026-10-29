"""Strict JSON decoding with JSON-pointer and line/column provenance."""
from __future__ import annotations
import json
import math
from pathlib import Path
from .types import CompilationError, Diagnostic, SourceLocation

def pointer(parent: str, key: object) -> str:
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')

class SourceDocument:
    def __init__(self, text: str, source: str = '<recipe>'):
        self.text, self.source, self.positions = text, source, {}
        self.decoder = json.JSONDecoder(parse_constant=self._constant, parse_float=self._finite_float)
        if len(text) > 2_000_000: self.fail('RecipeTooLarge', 'recipe exceeds 2 MB', '', 0)
        self.value, end = self._value(0, '', 0)
        if self._space(end) != len(text): self.fail('InvalidJSON', 'trailing content', '', end)
        if not isinstance(self.value, dict): self.fail('InvalidSchema', 'recipe must be an object', '', 0)
    @staticmethod
    def _constant(value: str):
        raise ValueError('nonfinite JSON number: ' + value)
    @staticmethod
    def _finite_float(value: str):
        parsed=float(value)
        if not math.isfinite(parsed):raise ValueError('nonfinite JSON exponent: '+value)
        return parsed
    def _space(self, index: int) -> int:
        while index < len(self.text) and self.text[index].isspace(): index += 1
        return index
    def location(self, path: str) -> SourceLocation:
        requested_path = path
        at = self.positions.get(path)
        while at is None and path:
            path = path.rsplit('/', 1)[0]; at = self.positions.get(path)
        pos = at or 0
        return SourceLocation(self.source, requested_path, self.text.count('\n', 0, pos) + 1, pos - self.text.rfind('\n', 0, pos))
    def fail(self, code: str, message: str, path: str, at: int):
        self.positions[path] = at
        raise CompilationError((Diagnostic(code, message, self.location(path), 1),))
    def _value(self, index: int, path: str, depth: int):
        index = self._space(index); self.positions[path] = index
        if depth > 64: self.fail('RecipeDepth', 'JSON nesting exceeds 64', path, index)
        if index >= len(self.text): self.fail('InvalidJSON', 'unexpected end', path, index)
        char = self.text[index]
        if char in '[{':
            obj = {} if char == '{' else []; closing = '}' if char == '{' else ']'; index = self._space(index + 1)
            if index < len(self.text) and self.text[index] == closing: return obj, index + 1
            while index < len(self.text):
                if char == '{':
                    try: key, stop = self.decoder.raw_decode(self.text, index)
                    except ValueError as error: self.fail('InvalidJSON', str(error), path, index)
                    if not isinstance(key, str): self.fail('InvalidJSON', 'object key must be a string', path, index)
                    if key in obj: self.fail('DuplicateKey', key, pointer(path, key), index)
                    index = self._space(stop)
                    if index >= len(self.text) or self.text[index] != ':': self.fail('InvalidJSON', 'expected colon', path, index)
                    value, index = self._value(index + 1, pointer(path, key), depth + 1); obj[key] = value
                else:
                    value, index = self._value(index, pointer(path, len(obj)), depth + 1); obj.append(value)
                index = self._space(index)
                if index < len(self.text) and self.text[index] == closing: return obj, index + 1
                if index >= len(self.text) or self.text[index] != ',': self.fail('InvalidJSON', 'expected comma or close', path, index)
                index = self._space(index + 1)
            self.fail('InvalidJSON', 'unterminated container', path, index)
        try: return self.decoder.raw_decode(self.text, index)
        except ValueError as error: self.fail('InvalidJSON', str(error), path, index)
    @classmethod
    def from_value(cls, value: dict, source: str = '<mapping>'):
        return cls(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), source)
    @classmethod
    def from_path(cls, path: str | Path):
        path = Path(path)
        return cls(path.read_text(encoding='utf-8'), str(path))
