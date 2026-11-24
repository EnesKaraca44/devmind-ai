"""Testler için küçük PDF'ler üretir (dış kütüphane gerekmez).

Bir PDF sayfasının içeriği "komut listesi"dir. Örnek:
    BT /F1 12 Tf 72 700 Td (Merhaba) Tj ET
Anlamı: metin bloğu başlat (BT), yazı tipi F1 12 punto, imleci (72,700)'e götür (Td),
"Merhaba" yaz (Tj), bitir (ET). Paragraf/başlık kavramı YOKTUR, yalnızca koordinatlar vardır.
"""


def make_pdf(pages: list[list[tuple[int, int, str]]]) -> bytes:
    """pages[i] = o sayfadaki (x, y, metin) parçaları, ÇİZİM SIRASIYLA.

    Metin yalnızca ASCII olmalı (standart yazı tipiyle Türkçe harf için ek kodlama gerekir).
    """
    objects: list[bytes] = []

    def add(body: str | bytes) -> int:
        objects.append(body.encode("latin-1") if isinstance(body, str) else body)
        return len(objects)  # nesne numarası (1'den başlar)

    catalog_id = add("")  # yer tutucu, sonra doldurulacak
    pages_id = add("")  # yer tutucu
    font_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for items in pages:
        commands = "".join(
            f"BT /F1 12 Tf {x} {y} Td ({text}) Tj ET\n" for x, y, text in items
        )
        stream = commands.encode("latin-1")
        content_id = add(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream"
        )
        page_ids.append(
            add(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            )
        )

    kids = " ".join(f"{i} 0 R" for i in page_ids)
    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode()
    return bytes(out)
