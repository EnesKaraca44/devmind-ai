import pytest

from app.ingestion.parsers.base import ParserError
from app.ingestion.parsers.text import TextParser

parser = TextParser()

# Türkçe'ye özgü harfler: ç ğ ı ö ş ü İ
TURKISH = "çğıöşü İstanbul"


def test_reads_utf8():
    result = parser.parse(TURKISH.encode("utf-8"))

    assert result.text == TURKISH
    assert result.encoding == "utf-8"
    assert result.warnings == []


def test_strips_utf8_bom():
    # BOM = dosyanın başındaki gizli işaret; metnin parçası olmamalı
    result = parser.parse(b"\xef\xbb\xbf" + TURKISH.encode("utf-8"))

    assert result.text == TURKISH
    assert not result.text.startswith("﻿")


def test_reads_utf16_with_bom():
    result = parser.parse(TURKISH.encode("utf-16"))  # Python BOM'u kendisi ekler

    assert result.text == TURKISH
    assert result.encoding == "utf-16"


def test_falls_back_to_cp1254_and_warns():
    result = parser.parse(TURKISH.encode("cp1254"))

    assert result.text == TURKISH
    assert result.encoding == "cp1254"
    assert len(result.warnings) == 1  # tahmin ettiğimizi söylüyoruz


def test_normalizes_line_endings():
    result = parser.parse(b"a\r\nb\rc\nd")

    assert result.text == "a\nb\nc\nd"


def test_normalizes_unicode_to_nfc():
    decomposed = "ç"  # "c" + birleşen çengel; ekranda "ç" gibi görünür
    result = parser.parse(decomposed.encode("utf-8"))

    assert result.text == "ç"  # tek karakterli ç


def test_markdown_is_kept_as_is():
    md = "# Başlık\n\n- madde **kalın**\n"
    result = parser.parse(md.encode("utf-8"))

    assert result.text == md  # Markdown işaretlerine dokunmuyoruz


@pytest.mark.parametrize("data", [b"", b"   \n\t  ", b"\xef\xbb\xbf"])
def test_rejects_empty_content(data):
    with pytest.raises(ParserError):
        parser.parse(data)


def test_rejects_binary_content():
    # PNG dosyalarının başlığı: içinde NUL byte var, metin değil
    with pytest.raises(ParserError):
        parser.parse(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")


def test_error_message_does_not_leak_content():
    secret = "ÇOK-GİZLİ-PAROLA".encode("utf-8") + b"\x00"
    with pytest.raises(ParserError) as error:
        parser.parse(secret)

    assert "GİZLİ" not in str(error.value)
