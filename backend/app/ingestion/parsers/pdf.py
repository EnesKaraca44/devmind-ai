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
            pages = self._extract_pages(data)
        except ParserError:
            raise
        except Exception:
            # Kullanıcıdan gelen PDF GÜVENİLMEZ girdidir ve üçüncü parti kütüphane çok çeşitli
            # hatalar fırlatabilir (hata sınıfları tek bir ata sınıftan türemeyebilir: gerçek bir
            # PDF'te DependencyError PyPdfError'ın alt sınıfı çıkmadı ve API 500 verecekti).
            # Bu yüzden dışarıya yalnızca ParserError sızar. İç ayrıntıyı (dosya içeriği
            # barındırabilir) mesaja KOYMAYIZ.
            raise ParserError("PDF okunamadı (bozuk ya da desteklenmeyen bir PDF).") from None

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

    def _extract_pages(self, data: bytes) -> list[str]:
        try:
            reader = PdfReader(BytesIO(data))
        except PyPdfError:
            raise ParserError("Geçerli bir PDF dosyası değil ya da bozuk.") from None

        if reader.is_encrypted:
            # Çoğu "şifreli" PDF yalnızca izinleri kısıtlar ve BOŞ kullanıcı parolasıyla açılır.
            # Gerçekten parola isteyenleri reddederiz.
            if not reader.decrypt(""):
                raise ParserError("PDF parola korumalı.")

        return [(page.extract_text() or "").strip() for page in reader.pages]
