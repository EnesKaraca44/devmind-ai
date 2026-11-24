FROM node:22-slim

WORKDIR /app

# Bağımlılık dosyaları önce: değişmedikçe `npm ci` katmanı önbellekten gelir.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_ değişkenleri build SIRASINDA koda gömülür (sonradan değiştirilemez).
# Bu adres TARAYICININ erişeceği adrestir, bu yüzden localhost:8000.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# root olmayan kullanıcı
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 3000
CMD ["npm", "run", "start", "--", "--port", "3000"]
