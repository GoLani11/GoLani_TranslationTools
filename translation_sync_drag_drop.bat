@echo off
chcp 65001 > nul
cls
echo ========================================
echo   타르코프 한글화 번역 동기화 도구
echo   (드래그 앤 드롭 버전)
echo ========================================
echo.

if "%~1"=="" (
    echo 사용법: 파일들을 이 배치 파일 위에 드래그 앤 드롭하세요.
    echo.
    echo 세 파일을 모두 선택해서 드래그 앤 드롭하세요:
    echo 1. 새로운 kr.json 파일
    echo 2. 새로운 en.json 파일  
    echo 3. 기존 TSV 파일
    echo.
    echo 또는 kr.json 파일만 드래그하면 자동으로 en.json과 TSV 파일을 찾습니다.
    echo.
    pause
    exit /b 1
)

set "script_dir=%~dp0"

REM 첫 번째 파일이 kr.json인지 확인
set "first_file=%~1"
if /i "%first_file:~-7%"==".json" if /i "%first_file%"=="%first_file:kr.json=%" (
    set "json_file=%~1"
) else (
    echo 오류: 첫 번째 파일은 kr.json이어야 합니다.
    pause
    exit /b 1
)

echo kr.json 파일: %json_file%

REM en.json 파일 찾기
if "%~2"=="" (
    echo.
    echo en.json 파일을 찾는 중...
    
    REM 현재 디렉토리에서 en.json 파일 찾기
    for %%f in ("%script_dir%en.json") do (
        if exist "%%f" set "en_json_file=%%f"
    )
    
    if not defined en_json_file (
        echo.
        echo en.json 파일을 찾을 수 없습니다.
        echo 세 파일을 모두 선택해서 드래그 앤 드롭하거나,
        echo en.json 파일을 같은 폴더에 두고 다시 시도하세요.
        echo.
        pause
        exit /b 1
    )
) else (
    set "en_json_file=%~2"
)

echo en.json 파일: %en_json_file%

REM TSV 파일 찾기
if "%~3"=="" (
    echo.
    echo TSV 파일을 찾는 중...
    
    REM 현재 디렉토리에서 TSV 파일 찾기
    for %%f in ("%script_dir%*.tsv") do (
        if not defined tsv_file set "tsv_file=%%f"
    )
    
    if not defined tsv_file (
        echo.
        echo TSV 파일을 찾을 수 없습니다.
        echo 세 파일을 모두 선택해서 드래그 앤 드롭하거나,
        echo TSV 파일을 같은 폴더에 두고 다시 시도하세요.
        echo.
        pause
        exit /b 1
    )
) else (
    set "tsv_file=%~3"
)

echo TSV 파일: %tsv_file%
echo.

if not exist "%json_file%" (
    echo 오류: kr.json 파일을 찾을 수 없습니다: %json_file%
    pause
    exit /b 1
)

if not exist "%en_json_file%" (
    echo 오류: en.json 파일을 찾을 수 없습니다: %en_json_file%
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

python translation_sync.py "%json_file%" "%en_json_file%" "%tsv_file%"

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