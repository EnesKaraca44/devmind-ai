"""Kullanıcının yüklediği dosyaya GÜVENMEYEN kontroller.

Bu dosya yalnızca saf fonksiyonlar içerir (web, veritabanı ve dosya sistemi yok):
girdi ver, kabul et ya da UploadValidationError al. Bu yüzden test etmesi kolay.
"""

import hashlib
import unicodedata
import uuid
from dataclasses import dataclass

from app.core.config import MAX_UPLOAD_BYTES

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_DISPLAY_NAME_LENGTH = 150

# Bilinen "sihirli sayılar": dosyanın ilk byte'ları gerçek türünü ele verir.
# Metin (txt/md) olduğunu iddia eden dosya bunlardan biriyle başlıyorsa metin değildir.
_BINARY_SIGNATURES = (
    b"%PDF-",  # PDF
    b"PK\x03\x04",  # ZIP, docx, xlsx, jar...
    b"\x89PNG",  # PNG
    b"\xff\xd8\xff",  # JPEG
    b"GIF8",  # GIF
    b"\x7fELF",  # Linux çalıştırılabilir
)


class UploadValidationError(Exception):
    """Yükleme reddedildi. Mesaj kullanıcıya gösterilebilir (dosya içeriği içermez)."""


class FileTooLargeError(UploadValidationError):
    """Boyut sınırı aşıldı. Ayrı sınıf: API bunu 400 yerine 413 (Payload Too Large) olarak döner."""


@dataclass(frozen=True)
class ValidatedUpload:
    display_name: str  # Temizlenmiş orijinal ad: sadece ETİKET, diske yazılmaz
    extension: str  # ".pdf" | ".txt" | ".md"
    size: int
    checksum: str  # SHA-256 (içeriğin parmak izi)
    storage_name: str  # Diske yazılacak ad: kullanıcıdan HİÇBİR şey içermez


def sanitize_filename(raw_name: str) -> str:
    """Kullanıcının verdiği adı güvenli bir etikete çevirir.

    Bu çıktı diske YAZILMAZ (diske rastgele ad yazarız); yalnızca ekranda gösterilir
    ve veritabanında etiket olarak saklanır. Yine de temizliyoruz.
    """
    # Klasör kısımlarını at: hem "/" hem "\" ile böl, son parçayı al.
    # ("../../etc/passwd" -> "passwd", "C:\\Windows\\x.txt" -> "x.txt")
    name = raw_name.replace("\\", "/").split("/")[-1]

    # Aynı harfin farklı yazımlarını tek biçime getir (ç = tek karakter).
    name = unicodedata.normalize("NFC", name)

    # Görünmez/tehlikeli karakterleri at: NUL gibi kontrol karakterleri (Cc) ve
    # yön değiştirenler gibi biçim karakterleri (Cf, ör. U+202E: "gnp.exe"yi "exe.png" gibi gösterir).
    name = "".join(ch for ch in name if unicodedata.category(ch) not in ("Cc", "Cf"))

    # Baştaki/sondaki boşluk ve nokta (gizli dosya ".bashrc", "adı." gibi şeyler) at.
    name = name.strip().strip(".").strip()

    if not name:
        raise UploadValidationError("Dosya adı geçersiz.")

    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        # Uzantıyı koruyarak kısalt: "çok-uzun-ad....pdf"
        stem, dot, ext = name.rpartition(".")
        if dot and 0 < len(ext) <= 10:
            name = stem[: MAX_DISPLAY_NAME_LENGTH - len(ext) - 1] + "." + ext
        else:
            name = name[:MAX_DISPLAY_NAME_LENGTH]
    return name


def get_extension(name: str) -> str:
    """Yalnızca SON uzantıyı döndürür ("a.pdf.exe" -> ".exe"). Küçük harfe çevirir."""
    dot = name.rfind(".")
    return name[dot:].lower() if dot > 0 else ""


def validate_upload(raw_name: str, data: bytes) -> ValidatedUpload:
    display_name = sanitize_filename(raw_name)
    extension = get_extension(display_name)

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise UploadValidationError(f"Desteklenmeyen dosya türü. İzin verilenler: {allowed}")

    if len(data) == 0:
        raise UploadValidationError("Dosya boş.")
    if len(data) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise FileTooLargeError(f"Dosya çok büyük (en fazla {limit_mb} MB).")

    _check_content_matches_extension(extension, data)

    return ValidatedUpload(
        display_name=display_name,
        extension=extension,
        size=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        # uuid4: tahmin edilemeyen rastgele kimlik. Kullanıcıdan gelen hiçbir parça yok,
        # bu yüzden path traversal mümkün değil.
        storage_name=f"{uuid.uuid4().hex}{extension}",
    )


def _check_content_matches_extension(extension: str, data: bytes) -> None:
    """Uzantı bir iddiadır; içerik gerçeği söyler. İkisi uyuşmalı."""
    if extension == ".pdf":
        # PDF şartnamesi başlığın ilk 1024 byte içinde olmasına izin verir.
        if b"%PDF-" not in data[:1024]:
            raise UploadValidationError("Dosya içeriği PDF değil.")
        return

    # .txt / .md: başka türden bir dosya olmamalı.
    if data.startswith(_BINARY_SIGNATURES):
        raise UploadValidationError("Dosya içeriği uzantısıyla uyuşmuyor (metin değil).")
