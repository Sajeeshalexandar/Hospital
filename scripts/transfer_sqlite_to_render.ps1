$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $projectRoot

if (-not [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw 'Clear DATABASE_URL before running this script so the source is the local SQLite database.'
}

$pythonCommand = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
$python = $pythonCommand.Source
$sourceDatabase = Join-Path $projectRoot 'db.sqlite3'
if (-not (Test-Path -LiteralPath $sourceDatabase -PathType Leaf)) {
    throw "Local SQLite database not found: $sourceDatabase"
}

$sourceEngineOutput = & $python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
if ($LASTEXITCODE -ne 0) {
    throw 'Could not inspect the source database settings.'
}
$sourceEngine = $sourceEngineOutput | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 1
if ([string]$sourceEngine -ne 'django.db.backends.sqlite3') {
    throw 'The source database is not SQLite. Check your local settings and environment.'
}

$transferDirectory = Join-Path $projectRoot '.local-data-transfer'
New-Item -ItemType Directory -Path $transferDirectory -Force | Out-Null
$fixturePath = Join-Path $transferDirectory ("sqlite-export-{0}.json" -f [Guid]::NewGuid().ToString('N'))

& $python manage.py dumpdata --database default --natural-foreign --exclude contenttypes --exclude auth.permission --exclude sessions --indent 2 --output $fixturePath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $fixturePath -PathType Leaf)) {
    throw 'SQLite export failed. Check the command output; any partial export is in .local-data-transfer.'
}
if ((Get-Item -LiteralPath $fixturePath).Length -eq 0) {
    throw 'SQLite export is empty. The export file was kept in .local-data-transfer.'
}

$secureDatabaseUrl = $null
$urlPointer = [IntPtr]::Zero
$importSucceeded = $false

try {
    $secureDatabaseUrl = Read-Host -Prompt 'Paste the Render PostgreSQL External Database URL (input is hidden)' -AsSecureString
    if ($secureDatabaseUrl.Length -eq 0) {
        throw 'A Render PostgreSQL External Database URL is required.'
    }

    $urlPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDatabaseUrl)
    $env:DATABASE_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($urlPointer)

    $targetEngineOutput = & $python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not inspect the target database settings.'
    }
    $targetEngine = $targetEngineOutput | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 1
    if ([string]$targetEngine -ne 'django.db.backends.postgresql') {
        throw 'DATABASE_URL did not select PostgreSQL. No data was imported.'
    }

    & $python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not migrate the Render database. Check the connection and deployment logs.'
    }

    $countQuery = "from django.apps import apps; excluded = {('contenttypes', 'contenttype'), ('auth', 'permission'), ('sessions', 'session')}; models = [model for model in apps.get_models() if (model._meta.app_label, model._meta.model_name) not in excluded]; print(sum(model._base_manager.count() for model in models))"
    $existingRows = & $python manage.py shell -c $countQuery
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not verify that the Render database is empty.'
    }

    $existingRowCount = 0
    $countLine = $existingRows | Where-Object { $_ -match '^\s*\d+\s*$' } | Select-Object -Last 1
    if ($null -eq $countLine -or -not [int]::TryParse(([string]$countLine).Trim(), [ref]$existingRowCount)) {
        throw 'Could not read the Render database row count; no data was imported.'
    }
    if ($existingRowCount -ne 0) {
        throw 'The Render database already contains application data. Import stopped to avoid duplicates.'
    }

    & $python manage.py loaddata --database default $fixturePath
    if ($LASTEXITCODE -ne 0) {
        throw 'Data import failed. The export remains in .local-data-transfer for a controlled retry.'
    }
    $importSucceeded = $true
}
finally {
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    if ($urlPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($urlPointer)
    }
    if ($null -ne $secureDatabaseUrl) {
        $secureDatabaseUrl.Dispose()
    }
}

if ($importSucceeded) {
    Remove-Item -LiteralPath $fixturePath -Force
    Write-Host 'Import completed. The temporary fixture was removed. Verify key record counts before switching users to the deployed site.'
}
