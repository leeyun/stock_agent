# backend\.env 의 키 설정 상태를 출력한다 (manager.bat 메뉴 4). 비밀 값은 길이만 보여준다.
param([string]$EnvFile)

$values = @{}
if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile -Encoding UTF8) {
        if ($line -match '^\s*([A-Z_]+)\s*=(.*)$') { $values[$Matches[1]] = $Matches[2].Trim() }
    }
} else {
    Write-Host "[ERROR] $EnvFile 이 없습니다. scripts\setup.bat 을 먼저 실행하세요."
    exit 1
}

# 공개해도 되는 값은 그대로, 비밀 값은 가려서 출력
$keys = @(
    @{ Name = 'DJANGO_SECRET_KEY';   Secret = $true;  Use = '필수. 서버 서명 키' },
    @{ Name = 'NAVER_CLIENT_ID';     Secret = $true;  Use = '뉴스 검색' },
    @{ Name = 'NAVER_CLIENT_SECRET'; Secret = $true;  Use = '뉴스 검색' },
    @{ Name = 'GEMINI_API_KEY';      Secret = $true;  Use = '뉴스 분석' },
    @{ Name = 'GOOGLE_CLIENT_ID';    Secret = $false; Use = 'Google 로그인' },
    @{ Name = 'NGROK_AUTHTOKEN';     Secret = $true;  Use = 'ngrok. 비어 있으면 ngrok.yml 사용' },
    @{ Name = 'NGROK_DOMAIN';        Secret = $false; Use = 'ngrok 도메인. 비어 있으면 계정 기본 dev 도메인' }
)

Write-Host "==================================================="
Write-Host "  backend\.env 키 상태"
Write-Host "==================================================="
foreach ($k in $keys) {
    $v = $values[$k.Name]
    if ([string]::IsNullOrEmpty($v) -or $v -eq 'change-me') {
        $shown = '(비어 있음)'
    } elseif ($k.Secret) {
        $shown = '설정됨 (' + $v.Length + '자)'
    } else {
        $shown = $v
    }
    Write-Host ("  {0,-20} {1,-28} {2}" -f $k.Name, $shown, $k.Use)
}

Write-Host ""
Write-Host "==================================================="
Write-Host "  ngrok 설정"
Write-Host "==================================================="
$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Host "  ngrok이 설치되어 있지 않습니다."
} else {
    $config = Join-Path $env:LOCALAPPDATA 'ngrok\ngrok.yml'
    $hasToken = (Test-Path $config) -and (Select-String -Path $config -Pattern '^\s*authtoken\s*:\s*\S+' -Quiet)
    Write-Host ("  설정 파일 : {0}" -f $config)
    Write-Host ("  authtoken : {0}" -f $(if ($hasToken) { '설정됨' } else { '없음' }))
    Write-Host "  토큰 확인 : https://dashboard.ngrok.com/get-started/your-authtoken"
    Write-Host "  토큰 등록 : ngrok config add-authtoken <토큰>"
}
