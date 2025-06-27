@echo off
chcp 65001 > nul
cls
echo ========================================
echo   타르코프 한글화 번역 동기화 도구
echo   (드래그 앤 드롭 버전)
echo ========================================
echo.

if "%~1"=="" (
    echo 사용법: 새로운 kr.json 파일을 이 배치 파일 위에 드래그 앤 드롭하세요.
    echo.
    echo 또는 두 파일을 모두 선택해서 드래그 앤 드롭하세요:
    echo 1. 새로운 kr.json 파일
    echo 2. 기존 TSV 파일
    echo.
    pause
    exit /b 1
)

set "json_file=%~1"
set "script_dir=%~dp0"

echo JSON 파일: %json_file%

if "%~2"=="" (
    echo.
    echo TSV 파일을 찾는 중...
    
    REM 현재 디렉토리에서 TSV 파일 찾기
    for %%f in ("%script_dir%*.tsv") do (
        if not defined tsv_file set "tsv_file=%%f"
    )
    
    if not defined tsv_file (
        echo.
        echo TSV 파일을 찾을 수 없습니다.
        echo 두 파일을 모두 선택해서 드래그 앤 드롭하거나,
        echo TSV 파일을 같은 폴더에 두고 다시 시도하세요.
        echo.
        pause
        exit /b 1
    )
) else (
    set "tsv_file=%~2"
)

echo TSV 파일: %tsv_file%
echo.

if not exist "%json_file%" (
    echo 오류: JSON 파일을 찾을 수 없습니다: %json_file%
    pause
    exit /b 1
)

if not exist "%tsv_file%" (
    echo 오류: TSV 파일을 찾을 수 없습니다: %tsv_file%
    pause
    exit /b 1
)

cd /d "%script_dir%"

echo 동기화를 시작합니다...
echo.

python translation_sync.py "%json_file%" "%tsv_file%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   동기화가 성공적으로 완료되었습니다!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   오류가 발생했습니다!
    echo ========================================
)

echo.
pause