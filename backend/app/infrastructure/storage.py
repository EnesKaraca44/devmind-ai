import re
from pathlib import Path
from typing import Protocol

# Bizim ürettiğimiz saklama adlarının biçimi (validation.py): 32 hex karakter + izinli uzantı.
# Bu desene uymayan hiçbir ad kabul edilmez: kullanıcıdan gelen bir şey sızsa bile diske ulaşamaz.
_STORAGE_KEY = re.compile(r"[0-9a-f]{32}\.(pdf|txt|md)")


class StorageError(Exception):
    pass


class Storage(Protocol):
    """Dosya depolama sözleşmesi.

    Kodun geri kalanı dosyanın NEREDE durduğunu bilmez: yerel klasör mü, bulut mu fark etmez.
    İleride S3 gibi bir depoya geçmek, bu sözleşmeye uyan yeni bir sınıf yazmak demektir.
    """

    def save(self, key: str, data: bytes) -> None: ...

    def read(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Savunma katmanı 1: ad beklenen biçimde mi?
        if not _STORAGE_KEY.fullmatch(key):
            raise StorageError("Geçersiz saklama adı.")
        path = (self.root / key).resolve()
        # Savunma katmanı 2: son yol gerçekten root'un içinde mi? (kemer + pantolon askısı)
        if path.parent != self.root:
            raise StorageError("Geçersiz saklama yolu.")
        return path

    def save(self, key: str, data: bytes) -> None:
        path = self._path(key)
        # Önce geçici dosyaya yaz, sonra yer değiştir: yazma yarıda kesilirse
        # diskte yarım kalmış bir "gerçek" dosya bırakmayız.
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(data)
        temp.replace(path)

    def read(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise StorageError("Dosya bulunamadı.")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        # Olmayan dosyayı silmek hata değil (idempotent): iki kez silmek zararsız olsun.
        self._path(key).unlink(missing_ok=True)
