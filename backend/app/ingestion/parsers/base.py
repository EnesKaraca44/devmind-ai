from dataclasses import dataclass, field
from typing import Protocol


class ParserError(Exception):
    """Dosya okunamadığında fırlatılır. Mesaj kullanıcıya gösterilebilecek kadar temiz olmalı;
    dosya içeriğini mesaja KOYMAYIZ (hassas veri loglara sızmasın)."""


@dataclass(frozen=True)
class ParsedDocument:
    """Her parser'ın aynı biçimde döndürdüğü sonuç."""

    text: str
    # Hangi kodlamayla okuduk? Hata ayıklarken ve kullanıcıya bilgi verirken lazım.
    encoding: str
    # Sorun sayılmayan ama bilinmesi gereken şeyler (ör. "kodlama tahmin edildi").
    warnings: list[str] = field(default_factory=list)


class Parser(Protocol):
    """Parser sözleşmesi: ham byte'ları al, ParsedDocument döndür.

    PDF, TXT, MD parser'ları hep aynı şekle uyar; böylece yükleme kodu
    "hangi parser?" ayrıntısını bilmeden hepsini aynı şekilde çağırabilir.
    """

    def parse(self, data: bytes) -> ParsedDocument: ...
