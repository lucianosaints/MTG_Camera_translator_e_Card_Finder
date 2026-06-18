Write-Host "Iniciando processo de build do Frontend..." -ForegroundColor Cyan

# Entra na pasta do frontend
Push-Location frontend

# Roda o npm run build
Write-Host "Executando 'npm run build'..." -ForegroundColor Yellow
npm run build

# Sai da pasta do frontend
Pop-Location

# Verifica se o build deu certo
if (Test-Path "frontend\dist") {
    Write-Host "Build concluído! Copiando a pasta 'dist' para o backend..." -ForegroundColor Yellow
    
    # Remove a pasta dist antiga no backend, se existir
    if (Test-Path "backend\dist") {
        Remove-Item -Recurse -Force "backend\dist"
    }

    # Copia a nova pasta dist para o backend
    Copy-Item -Path "frontend\dist" -Destination "backend\dist" -Recurse -Force

    Write-Host "Sucesso! A pasta 'dist' foi copiada para 'backend/dist'." -ForegroundColor Green
    Write-Host "Você já pode rodar 'fly deploy' (se estiver na raiz) ou 'fly deploy' dentro de /backend." -ForegroundColor Cyan
} else {
    Write-Host "Erro: A pasta 'dist' não foi gerada. Verifique os logs de build." -ForegroundColor Red
}
