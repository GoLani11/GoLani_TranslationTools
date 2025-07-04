#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
타르코프 한글화 번역 동기화 도구
새로운 kr.json 파일의 순서에 맞게 TSV 파일을 업데이트하고 새로운 항목들을 추가합니다.
"""

import json
import csv
import sys
import os
import re
from datetime import datetime


def load_json_file(json_path):
    """JSON 파일을 로드하고 키 순서를 유지"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON 파일 로드 오류: {e}")
        return None


def escape_special_chars(text):
    """특수문자를 JSON에 안전하게 저장할 수 있도록 이스케이프 처리 (중복 방지)"""
    if not isinstance(text, str):
        return text
    
    # 이미 이스케이프된 문자들은 건드리지 않도록 순서 조정
    # 백슬래시를 먼저 처리하되, 이미 이스케이프된 것은 제외
    
    # 1. 이미 이스케이프되지 않은 백슬래시만 처리
    # \\n, \\r, \\t, \\", \\\\ 등을 제외한 단독 백슬래시만 이스케이프
    text = re.sub(r'\\(?![\\nrt"])', r'\\\\', text)
    
    # 2. 이미 이스케이프되지 않은 따옴표만 처리
    text = re.sub(r'(?<!\\)"', r'\\"', text)
    
    # 3. 이미 이스케이프되지 않은 개행문자만 처리
    text = re.sub(r'(?<!\\)\n', r'\\n', text)
    
    # 4. 이미 이스케이프되지 않은 캐리지 리턴만 처리
    text = re.sub(r'(?<!\\)\r', r'\\r', text)
    
    # 5. 이미 이스케이프되지 않은 탭만 처리 (번역 입력문에서는 공백으로 변환되므로 여기서는 제외)
    # text = re.sub(r'(?<!\\)\t', r'\\t', text)
    
    return text


def unescape_special_chars(text):
    """이스케이프된 특수문자를 원래대로 복원"""
    if not isinstance(text, str):
        return text
    
    # 이스케이프된 문자들을 원래대로 복원
    text = text.replace('\\"', '"')     # 따옴표
    text = text.replace('\\n', '\n')    # 줄바꿈
    text = text.replace('\\r', '\r')    # 캐리지 리턴
    text = text.replace('\\t', '\t')    # 탭
    text = text.replace('\\\\', '\\')  # 백슬래시 (마지막에 처리)
    
    return text


def clean_tsv_field(text):
    """TSV 파일에 안전하게 저장할 수 있도록 필드 정리 (구글 스프레드시트 친화적)"""
    if not isinstance(text, str):
        return str(text) if text is not None else ''
    
    # TSV에서 문제가 될 수 있는 문자들 처리
    # 탭 문자는 공백으로 대체 (TSV 구조 깨짐 방지)
    text = text.replace('\t', ' ')
    
    # 실제 개행문자는 \n으로 이스케이프 (TSV 구조 깨짐 방지)
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    
    return text


def prepare_translation_input(text):
    """번역 입력문용 텍스트 처리 - JSON 특수문자 이스케이프 적용"""
    if not isinstance(text, str):
        return str(text) if text is not None else ''
    
    # 1. JSON 이스케이프 처리 (JSON 호환성을 위해 따옴표는 \\"로 유지)
    text = escape_special_chars(text)
    
    # 2. TSV 안전 처리 (탭 문자만 공백으로 변환)
    text = text.replace('\t', ' ')
    
    return text


def generate_translation_formula():
    """번역문 컬럼에 사용할 스프레드시트 자동입력 함수 생성"""
    # 번역 입력문(5번째 컬럼, RC[1])을 참조하여 자동으로 따옴표와 쉼표 추가
    return '=IF(INDIRECT("RC[1]", FALSE)<>"", CHAR(34) & INDIRECT("RC[1]", FALSE) & CHAR(34) & ",", CHAR(34) & CHAR(34) & ",")'


def should_use_formula(trans_data):
    """모든 번역문에 함수를 적용할지 판단 - 이제 항상 True 반환"""
    # 모든 항목에 대해 자동입력 함수를 강제로 적용
    return True


def load_tsv_file(tsv_path):
    """TSV 파일을 로드하고 번역 데이터를 딕셔너리로 변환"""
    translations = {}
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE, quotechar=None)
            rows = list(reader)
            
            # 헤더 찾기 (원문 ID가 있는 행)
            data_start_row = 0
            for i, row in enumerate(rows):
                if len(row) > 0 and '원문 ID' in str(row[0]):
                    data_start_row = i + 1
                    break
            
            # 데이터 행들 처리
            for row in rows[data_start_row:]:
                if len(row) >= 5 and row[0].strip():  # 빈 행 건너뛰기
                    # TSV의 ID 형태: "MOD_HANDGUARD": -> MOD_HANDGUARD로 변환
                    raw_id = row[0].strip()
                    # 앞뒤 따옴표 제거하고 끝의 콜론 제거
                    if raw_id.startswith('"') and raw_id.endswith('":'):
                        item_id = raw_id[1:-2]  # 앞의 " 와 뒤의 ": 제거
                    elif raw_id.startswith('"') and raw_id.endswith('"'):
                        item_id = raw_id[1:-1]  # 앞뒤 " 제거
                    elif raw_id.endswith(':'):
                        item_id = raw_id[:-1]   # 뒤의 : 제거
                    else:
                        item_id = raw_id
                        
                    if item_id:
                        translations[item_id] = {
                            '한글_원문': unescape_special_chars(row[1]) if len(row) > 1 else '',
                            '번역문_ID': row[2] if len(row) > 2 else '',
                            '번역문': unescape_special_chars(row[3]) if len(row) > 3 else '',
                            '번역_입력문': unescape_special_chars(row[4]) if len(row) > 4 else '',
                            '카테고리': row[5] if len(row) > 5 else '',
                            '번역_상태': row[6] if len(row) > 6 else '',
                            '비고': row[7] if len(row) > 7 else '',
                            '영문_원문': unescape_special_chars(row[8]) if len(row) > 8 else '',
                            '영문_아이템_ID': row[9] if len(row) > 9 else ''
                        }
        
        return translations, rows[:data_start_row]  # 헤더도 함께 반환
        
    except Exception as e:
        print(f"TSV 파일 로드 오류: {e}")
        return {}, []


def create_updated_tsv(json_data, en_json_data, existing_translations, header_rows, output_path):
    """새로운 순서로 TSV 파일 생성"""
    
    # 백업 파일 생성
    backup_path = output_path.replace('.tsv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tsv')
    if os.path.exists(output_path):
        os.rename(output_path, backup_path)
        print(f"기존 파일을 백업했습니다: {backup_path}")
    
    new_entries = []
    updated_entries = []
    deleted_entries = []
    
    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            
            # 헤더 행들 작성
            for header_row in header_rows:
                writer.writerow(header_row)
            
            # JSON의 키 순서대로 데이터 작성
            for key, value in json_data.items():
                # en.json에서 동일한 키로 영문 데이터 찾기
                en_value = en_json_data.get(key, '') if en_json_data else ''
                
                if key in existing_translations:
                    # 기존 번역이 있는 경우
                    trans_data = existing_translations[key]
                    
                    # 번역문 처리: 함수 사용 여부 결정
                    if should_use_formula(trans_data):
                        translation_field = generate_translation_formula()
                    else:
                        translation_field = clean_tsv_field(trans_data['번역문'])
                    
                    row = [
                        f'"{key}":',
                        clean_tsv_field(trans_data['한글_원문']),
                        f'"{key}":',
                        translation_field,
                        prepare_translation_input(trans_data['번역_입력문']),
                        clean_tsv_field(trans_data['카테고리']),
                        clean_tsv_field(trans_data['번역_상태']),
                        clean_tsv_field(trans_data['비고']),
                        clean_tsv_field(en_value),  # en.json 값을 영문 원문으로
                        clean_tsv_field(key)        # 키를 영문 아이템 ID로
                    ]
                    updated_entries.append(key)
                else:
                    # 새로운 항목인 경우 - 자동입력 함수 사용
                    clean_value = clean_tsv_field(value)
                    row = [
                        f'"{key}":',
                        clean_value,  # JSON의 값을 한글 원문으로
                        f'"{key}":',
                        generate_translation_formula(),  # 자동입력 함수
                        prepare_translation_input(value),  # 번역 입력문 (JSON 이스케이프 적용)
                        '',  # 카테고리
                        '미번역',  # 번역 상태
                        f'새로 추가됨 ({datetime.now().strftime("%Y-%m-%d")})',  # 비고에 날짜 포함
                        clean_tsv_field(en_value),  # en.json 값을 영문 원문으로
                        clean_tsv_field(key)        # 키를 영문 아이템 ID로
                    ]
                    new_entries.append(key)
                
                writer.writerow(row)
        
        # 삭제된 항목들 찾기
        deleted_entries = list(set(existing_translations.keys()) - set(json_data.keys()))
        
        return new_entries, updated_entries, deleted_entries
        
    except Exception as e:
        print(f"TSV 파일 생성 오류: {e}")
        return [], [], []


def save_deleted_items_to_file(deleted_entries, existing_translations, output_path):
    """삭제된 항목들을 텍스트 파일로 저장"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"삭제된 번역 항목들 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"총 삭제된 항목 수: {len(deleted_entries)}\n\n")
            
            for i, item_id in enumerate(deleted_entries, 1):
                trans_data = existing_translations.get(item_id, {})
                f.write(f"{i}. 아이템 ID: {item_id}\n")
                f.write(f"   한글 원문: {trans_data.get('한글_원문', '')}\n")
                f.write(f"   번역문: {trans_data.get('번역문', '')}\n")
                f.write(f"   번역 입력문: {trans_data.get('번역_입력문', '')}\n")
                f.write(f"   카테고리: {trans_data.get('카테고리', '')}\n")
                f.write(f"   번역 상태: {trans_data.get('번역_상태', '')}\n")
                f.write(f"   비고: {trans_data.get('비고', '')}\n")
                f.write(f"   영문 원문: {trans_data.get('영문_원문', '')}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"삭제된 항목들이 성공적으로 저장되었습니다: {output_path}")
        
    except Exception as e:
        print(f"삭제된 항목 파일 저장 오류: {e}")


def main():
    # Windows 콘솔 인코딩 설정
    if sys.platform == 'win32':
        import locale
        try:
            # Windows에서 UTF-8 출력을 위한 설정
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    if len(sys.argv) != 4:
        print("사용법: python translation_sync.py <새로운_kr.json_경로> <새로운_en.json_경로> <기존_TSV_파일_경로>")
        print("예시: python translation_sync.py kr.json en.json \"SPT 타르코프 한글화 프로젝트 - 메인 번역 작업.tsv\"")
        sys.exit(1)
    
    json_path = sys.argv[1]
    en_json_path = sys.argv[2]
    tsv_path = sys.argv[3]
    
    # 파일 존재 확인
    if not os.path.exists(json_path):
        print(f"kr.json 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)
    
    if not os.path.exists(en_json_path):
        print(f"en.json 파일을 찾을 수 없습니다: {en_json_path}")
        sys.exit(1)
    
    if not os.path.exists(tsv_path):
        print(f"TSV 파일을 찾을 수 없습니다: {tsv_path}")
        sys.exit(1)
    
    print("번역 동기화를 시작합니다...")
    
    # 파일 로드
    print("1. kr.json 파일 로드 중...")
    json_data = load_json_file(json_path)
    if json_data is None:
        sys.exit(1)
    
    print("2. en.json 파일 로드 중...")
    en_json_data = load_json_file(en_json_path)
    if en_json_data is None:
        sys.exit(1)
    
    print("3. TSV 파일 로드 중...")
    existing_translations, header_rows = load_tsv_file(tsv_path)
    
    print(f"   - 기존 번역 항목 수: {len(existing_translations)}")
    print(f"   - 새 kr.json 항목 수: {len(json_data)}")
    print(f"   - 새 en.json 항목 수: {len(en_json_data)}")
    
    # ID 매칭 확인을 위한 디버깅 (처음 5개만 출력)
    print("\n[ ID 매칭 확인 ]")
    json_keys = list(json_data.keys())[:5]
    en_json_keys = list(en_json_data.keys())[:5]
    tsv_keys = list(existing_translations.keys())[:5]
    
    print("kr.json 첫 5개 키:")
    for key in json_keys:
        print(f"  '{key}'")
    
    print("en.json 첫 5개 키:")
    for key in en_json_keys:
        print(f"  '{key}'")
    
    print("TSV 첫 5개 키:")
    for key in tsv_keys:
        print(f"  '{key}'")
    
    # 매칭되는 키 확인
    matches = set(json_data.keys()) & set(existing_translations.keys())
    en_matches = set(json_data.keys()) & set(en_json_data.keys())
    print(f"kr.json-TSV 매칭되는 키 수: {len(matches)}")
    print(f"kr.json-en.json 매칭되는 키 수: {len(en_matches)}")
    
    # TSV 업데이트
    print("4. TSV 파일 업데이트 중...")
    new_entries, updated_entries, deleted_entries = create_updated_tsv(
        json_data, en_json_data, existing_translations, header_rows, tsv_path
    )
    
    # 결과 보고
    print("\n=== 동기화 완료 ===")
    print(f"총 항목 수: {len(json_data)}")
    print(f"기존 번역 유지: {len(updated_entries)}")
    print(f"새로 추가된 항목: {len(new_entries)}")
    
    if new_entries:
        print(f"\n새로 추가된 항목들 (처음 10개):")
        for i, entry in enumerate(new_entries[:10]):
            print(f"  - {entry}")
        if len(new_entries) > 10:
            print(f"  ... 및 {len(new_entries) - 10}개 더")
    
    # 삭제된 항목 확인 및 파일 저장
    if deleted_entries:
        print(f"\n주의: 새 JSON에서 제거된 항목들: {len(deleted_entries)}개")
        for entry in deleted_entries[:5]:
            print(f"  - {entry}")
        if len(deleted_entries) > 5:
            print(f"  ... 및 {len(deleted_entries) - 5}개 더")
        
        # 삭제된 항목들을 텍스트 파일로 저장
        deleted_file_path = tsv_path.replace('.tsv', f'_deleted_items_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        save_deleted_items_to_file(deleted_entries, existing_translations, deleted_file_path)
        print(f"삭제된 항목들이 저장되었습니다: {deleted_file_path}")
    
    print(f"\n업데이트된 TSV 파일: {tsv_path}")
    print("번역 작업을 계속 진행하세요!")


if __name__ == "__main__":
    main()