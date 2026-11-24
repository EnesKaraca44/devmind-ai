from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.ingestion.parsers.base import ParsedDocument, ParserError


class PdfParser:
    """PDF'ten sayfa sayfa metin çıkarır (OCR YOK).

    PDF "yazı" değil "sayfada harflerin koordinatları" saklar; pypdf bu harfleri
    kelime/satır olarak birleştirmeye çalışır. Sonuç her zaman kusursuz değildir
    (çok sütunlu sayfalarda sıra karışabilir, tablolar düzleşir).
    """

    def parse(self, data: bytes) -> ParsedDocument:
        try:
            reader = PdfReader(BytesIO(data))
        except (PyPdfError, ValueError, OSError):
            # Hata ayrıntısını (içerik parçası içerebilir) kullanıcıya/loga taşımıyoruz.
            raise ParserError("Geçerli bir PDF dosyası değil ya da bozuk.") from None

        if reader.is_encrypted:
            # Parola gerekmeden açılabiliyorsa (boş parola) devam, değilse reddet.
            try:
                if not reader.decrypt(""):
                    raise ParserError("PDF parola korumalı.")
            except PyPdfError:
                raise ParserError("PDF parola korumalı.") from None

        pages: list[str] = []
        try:
            for page in reader.pages:
                pages.append((page.extract_text() or "").strip())
        except (PyPdfError, ValueError, KeyError, OSError):
            raise ParserError("PDF içeriği okunamadı.") from None

        if not any(pages):
            # Metin yok: büyük ihtimalle taranmış (resim) PDF. OCR ileride düşünülecek.
            raise ParserError(
                "PDF'ten metin çıkarılamadı. Taranmış (resimli) bir PDF olabilir; OCR henüz desteklenmiyor."
            )

        warnings: list[str] = []
        empty_pages = [i + 1 for i, text in enumerate(pages) if not text]
        if empty_pages:
            warnings.append(
                f"{len(empty_pages)} sayfadan metin çıkarılamadı (sayfa: {empty_pages[:10]})."
            )

        return ParsedDocument(
            text="\n\n".join(text for text in pages if text),
            pages=pages,
            warnings=warnings,
        )
