from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.ingestion.parsers.base import ParserError
from app.ingestion.parsers.pdf import PdfParser
from tests.pdf_factory import make_pdf

parser = PdfParser()


def test_extracts_text_page_by_page():
    pdf = make_pdf(
        [
            [(72, 700, "First page text")],
            [(72, 700, "Second page text")],
        ]
    )

    result = parser.parse(pdf)

    assert result.pages == ["First page text", "Second page text"]
    assert "First page text" in result.text and "Second page text" in result.text
    assert result.encoding is None  # PDF'te kodlama kavramı yok
    assert result.warnings == []


def test_page_numbers_are_preserved_with_blank_page_in_the_middle():
    pdf = make_pdf([[(72, 700, "Page one")], [], [(72, 700, "Page three")]])

    result = parser.parse(pdf)

    assert result.pages == ["Page one", "", "Page three"]  # 3. sayfa 3. sırada kalır
    assert len(result.warnings) == 1  # boş sayfa bildirildi


def test_pdf_without_text_is_rejected_like_a_scanned_pdf():
    pdf = make_pdf([[], []])  # iki sayfa var ama hiç yazı yok (taranmış PDF benzeri)

    with pytest.raises(ParserError) as error:
        parser.parse(pdf)

    assert "OCR" in str(error.value)


@pytest.mark.parametrize("data", [b"", b"bu bir pdf degil", b"%PDF-1.4\nbozuk icerik"])
def test_rejects_invalid_or_corrupt_pdf(data):
    with pytest.raises(ParserError):
        parser.parse(data)


def test_rejects_password_protected_pdf():
    writer = PdfWriter()
    for page in PdfReader(BytesIO(make_pdf([[(72, 700, "secret")]]))).pages:
        writer.add_page(page)
    writer.encrypt("gizli", algorithm="RC4-128")
    buffer = BytesIO()
    writer.write(buffer)

    with pytest.raises(ParserError) as error:
        parser.parse(buffer.getvalue())

    assert "parola" in str(error.value)


def test_known_limitation_text_follows_drawing_order_not_reading_order():
    # Bilinen sınır (hata değil): PDF'te "okuma sırası" yok, yalnızca çizim sırası ve koordinat var.
    # Ekranda 1-2-3 görünen satırlar, çizim sırasıyla 3-1-2 çıkar. Bu testi, davranışı
    # BELGELEMEK için tutuyoruz; ileride sıralamayı iyileştirirsek bilinçli olarak güncelleriz.
    pdf = make_pdf([[(72, 650, "3. Third"), (72, 750, "1. First"), (72, 700, "2. Second")]])

    assert parser.parse(pdf).text == "3. Third\n1. First\n2. Second"


def test_error_message_does_not_leak_content():
    with pytest.raises(ParserError) as error:
        parser.parse(b"GIZLI-PAROLA-123 pdf degil")

    assert "GIZLI" not in str(error.value)
