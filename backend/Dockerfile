FROM python:3.11-slim

# Konteyner içindeki çalışma klasörü
WORKDIR /app

# Önce SADECE bağımlılık listesi: requirements.txt değişmedikçe bu katman önbellekten gelir.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod en sona: sık değişen şey ne kadar sonda olursa build o kadar hızlı olur.
COPY app ./app

# root olmayan kullanıcı: konteyner ele geçirilirse verilen yetki daha az olur.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# 0.0.0.0: konteynerin DIŞINDAN gelen bağlantıları da dinle (127.0.0.1 olsaydı yalnızca içeriden).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
