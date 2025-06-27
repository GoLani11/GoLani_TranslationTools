@echo off
chcp 65001 > nul
cls
echo ========================================
echo   타르코프 한글화 번역 동기화 도구
echo ========================================
echo.

set "script_dir=%~dp0"
cd /d "%script_dir%"

echo 현재 디렉토리의 파일들:
echo.
dir /b *.json *.tsv 2>nul
echo.

:input_json
set /p "json_file=새로운 kr.json 파일명을 입력하세요 (예: new_kr.json): "
if not exist "%json_file%" (
    echo.
    echo 오류: 파일 '%json_file%'을 찾을 수 없습니다.
    echo.
    goto input_json
)

:input_tsv
set /p "tsv_file=TSV 파일명을 입력하세요 (예: SPT 타르코프 한글화 프로젝트 - 메인 번역 작업.tsv): "
if not exist "%tsv_file%" (
    echo.
    echo 오류: 파일 '%tsv_file%'을 찾을 수 없습니다.
    echo.
    goto input_tsv
)

echo.
echo 동기화를 시작합니다...
echo JSON 파일: %json_file%
echo TSV 파일: %tsv_file%
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