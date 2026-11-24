import pytest

from app.infrastructure.storage import LocalStorage, StorageError

KEY = "0123456789abcdef0123456789abcdef.txt"


def test_save_read_delete_roundtrip(tmp_path):
    storage = LocalStorage(tmp_path)

    storage.save(KEY, b"merhaba")
    assert storage.read(KEY) == b"merhaba"

    storage.delete(KEY)
    with pytest.raises(StorageError):
        storage.read(KEY)


def test_delete_is_idempotent(tmp_path):
    storage = LocalStorage(tmp_path)

    storage.delete(KEY)  # hiç var olmamış dosya: hata vermemeli
    storage.delete(KEY)


def test_save_leaves_no_temp_files(tmp_path):
    LocalStorage(tmp_path).save(KEY, b"x")

    assert [p.name for p in tmp_path.iterdir()] == [KEY]


@pytest.mark.parametrize(
    "key",
    [
        "../disari.txt",
        "..\\disari.txt",
        "/etc/passwd",
        "C:\\Windows\\x.txt",
        "kisa.txt",
        "0123456789abcdef0123456789abcdef.exe",
        "0123456789ABCDEF0123456789ABCDEF.txt",  # büyük harf: bizim biçimimiz değil
        "0123456789abcdef0123456789abcdef.txt/../x",
        "",
    ],
)
def test_rejects_keys_that_are_not_our_generated_names(tmp_path, key):
    storage = LocalStorage(tmp_path)

    for operation in (lambda: storage.save(key, b"x"), lambda: storage.read(key), lambda: storage.delete(key)):
        with pytest.raises(StorageError):
            operation()
