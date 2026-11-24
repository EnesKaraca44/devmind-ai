# Kendi bilgisayarından (konteyner dışından) çalıştırılan komutlar için DATABASE_URL üretir.
# Kullanım (nokta ile "dot-source": değişken mevcut oturuma yüklensin diye):
#   . .\scripts\dev-env.ps1
#
# Konteyner dışından veritabanına YAYINLANAN port (localhost:5433) ile bağlanılır.
# Konteyner içindeki backend ise "db:5432" kullanır (docker-compose.yml'de verilir).

$envFile = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envFile)) { throw ".env bulunamadı. Önce: Copy-Item .env.example .env" }

$vars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)\s*$') { $vars[$Matches[1]] = $Matches[2] }
}

# "localhost" DEĞİL "127.0.0.1": localhost önce IPv6'ya (::1) çözülür, Docker portu yalnızca IPv4'e
# açtığı için o deneme sessizce düşer ve her bağlantı saniyelerce beklerdi.
$env:DATABASE_URL = "postgresql+psycopg://$($vars['POSTGRES_USER']):$($vars['POSTGRES_PASSWORD'])@127.0.0.1:$($vars['POSTGRES_HOST_PORT'])/$($vars['POSTGRES_DB'])"
Write-Host "DATABASE_URL ayarlandı (parola gösterilmiyor): 127.0.0.1:$($vars['POSTGRES_HOST_PORT'])/$($vars['POSTGRES_DB'])"
