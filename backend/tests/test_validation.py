import re

import pytest

from app.ingestion import validation
from app.ingestion.validation import (
    UploadValidationError,
    get_extension,
    sanitize_filename,
    validate_upload,
)

PDF_BYTES = b"%PDF-1.4\n...icerik..."
TEXT_BYTES = "merhaba d\u00fcnya".encode("utf-8")


# ---------- dosya adı temizleme (path traversal) ----------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("../../etc/passwd.txt", "passwd.txt"),
        ("..\\..\\Windows\\sistem.txt", "sistem.txt"),
        ("C:\\Users\\ENES\\not.md", "not.md"),
        ("/etc/shadow.txt", "shadow.txt"),
        ("normal.pdf", "normal.pdf"),
        ("  bo\u015fluklu ad.txt  ", "bo\u015fluklu ad.txt"),
        (".gizli.txt", "gizli.txt"),
    ],
)
def test_sanitize_strips_directories_and_junk(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_removes_control_and_direction_override_characters():
    # NUL (\x00) ve U+202E (sağdan-sola geçersiz kılma) görünmez ama tehlikelidir
    assert sanitize_filename("a\x00b\u202etxt.txt") == "abtxt.txt"


def test_sanitize_keeps_turkish_letters_in_nfc():
    decomposed = "c\u0327al\u0131\u015fma.txt"  # c + birleşen çengel
    assert sanitize_filename(decomposed) == "\u00e7al\u0131\u015fma.txt"


@pytest.mark.parametrize("raw", ["", "   ", "...", "../", "\x00", "\\"])
def test_sanitize_rejects_names_that_become_empty(raw):
    with pytest.raises(UploadValidationError):
        sanitize_filename(raw)


def test_sanitize_truncates_long_names_but_keeps_extension():
    name = sanitize_filename("a" * 500 + ".pdf")

    assert len(name) <= validation.MAX_DISPLAY_NAME_LENGTH
    assert name.endswith(".pdf")


# ---------- uzantı ----------


def test_extension_uses_only_the_last_part():
    assert get_extension("rapor.pdf.exe") == ".exe"
    assert get_extension("RAPOR.PDF") == ".pdf"
    assert get_extension("uzantisiz") == ""


# ---------- tam doğrulama ----------


def test_valid_pdf_is_accepted():
    result = validate_upload("Rapor.PDF", PDF_BYTES)

    assert result.display_name == "Rapor.PDF"
    assert result.extension == ".pdf"
    assert result.size == len(PDF_BYTES)
    assert len(result.checksum) == 64  # SHA-256 = 64 hex karakter


def test_storage_name_contains_nothing_from_the_user():
    result = validate_upload("../../etc/passwd.txt", TEXT_BYTES)

    assert re.fullmatch(r"[0-9a-f]{32}\.txt", result.storage_name)
    assert "passwd" not in result.storage_name and ".." not in result.storage_name


def test_storage_names_are_unique_for_same_upload():
    first = validate_upload("a.txt", TEXT_BYTES)
    second = validate_upload("a.txt", TEXT_BYTES)

    assert first.storage_name != second.storage_name
    assert first.checksum == second.checksum  # aynı içerik = aynı parmak izi


def test_checksum_changes_when_one_byte_changes():
    assert validate_upload("a.txt", b"abc").checksum != validate_upload("a.txt", b"abd").checksum


@pytest.mark.parametrize("name", ["virus.exe", "rapor.pdf.exe", "resim.png", "uzantisiz", "a.docx"])
def test_rejects_unsupported_extensions(name):
    with pytest.raises(UploadValidationError):
        validate_upload(name, TEXT_BYTES)


def test_rejects_empty_file():
    with pytest.raises(UploadValidationError):
        validate_upload("a.txt", b"")


def test_rejects_too_large_file(monkeypatch):
    monkeypatch.setattr(validation, "MAX_UPLOAD_BYTES", 10)

    with pytest.raises(UploadValidationError):
        validate_upload("a.txt", b"x" * 11)
    assert validate_upload("a.txt", b"x" * 10).size == 10  # sınırın tam kendisi kabul


def test_rejects_fake_pdf():
    with pytest.raises(UploadValidationError):
        validate_upload("sahte.pdf", b"bu aslinda duz metin")


@pytest.mark.parametrize(
    "signature",
    [b"%PDF-1.4", b"PK\x03\x04zip", b"\x89PNG\r\n", b"\xff\xd8\xff\xe0", b"GIF89a", b"\x7fELF\x02"],
)
def test_rejects_other_file_types_disguised_as_text(signature):
    with pytest.raises(UploadValidationError):
        validate_upload("not.txt", signature + b"....")


def test_error_messages_do_not_leak_content_or_name():
    with pytest.raises(UploadValidationError) as error:
        validate_upload("GIZLI-AD.exe", b"GIZLI-ICERIK")

    assert "GIZLI" not in str(error.value)
