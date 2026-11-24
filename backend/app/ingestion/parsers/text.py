import unicodedata

from app.ingestion.parsers.base import ParsedDocument, ParserError

# Dosyanın en başındaki "ben UTF-16'yım" işaretleri (BOM).
_UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")


def _decode(data: bytes) -> tuple[str, str, list[str]]:
    """Byte'ları metne çevirir. (metin, kullanılan_kodlama, uyarılar) döndürür."""
    if data.startswith(_UTF16_BOMS):
        try:
            return data.decode("utf-16"), "utf-16", []
        except UnicodeDecodeError:
            raise ParserError("UTF-16 olarak okunamadı.") from None

    try:
        # utf-8-sig: dosyanın başında BOM varsa onu atar, yoksa normal UTF-8 gibi davranır.
        return data.decode("utf-8-sig"), "utf-8", []
    except UnicodeDecodeError:
        pass

    # UTF-8 değil. Türkçe eski Windows dosyaları genelde cp1254'tür.
    # Bu bir TAHMİN; bunu kullanıcıya açıkça söylüyoruz.
    try:
        text = data.decode("cp1254")
    except UnicodeDecodeError:
        raise ParserError("Dosyanın karakter kodlaması anlaşılamadı.") from None
    return text, "cp1254", ["UTF-8 değil; Windows-1254 (Türkçe) olarak tahmin edildi."]


class TextParser:
    """TXT ve Markdown için ortak parser.

    Markdown'ı şimdilik düz metin gibi okuyoruz. Başlık yapısı (# ## ###) gibi
    bilgileri chunking aşamasında (Sprint 3) kullanacağız; ham metni değiştirmiyoruz.
    """

    def parse(self, data: bytes) -> ParsedDocument:
        # NUL byte (0x00) düz metinde olmaz; varsa dosya büyük ihtimalle ikili (resim, exe...).
        # UTF-16 dosyalarda NUL doğaldır, o yüzden kontrolü UTF-16 BOM'u olmayanlara uyguluyoruz.
        if b"\x00" in data and not data.startswith(_UTF16_BOMS):
            raise ParserError("Dosya metin değil gibi görünüyor (ikili içerik).")

        text, encoding, warnings = _decode(data)

        # Satır sonlarını tek biçime getir: Windows \r\n ve eski Mac \r -> \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # NFC: aynı harfin farklı yazım biçimlerini tek biçime getirir (ç = tek karakter).
        # Aksi halde görünüşte aynı kelimeler aramada eşleşmez.
        text = unicodedata.normalize("NFC", text)

        if not text.strip():
            raise ParserError("Dosya boş ya da yalnızca boşluk içeriyor.")

        return ParsedDocument(text=text, encoding=encoding, warnings=warnings)
