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
from datetime import datetime


def load_json_file(json_path):
    """JSON 파일을 로드하고 키 순서를 유지"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON 파일 로드 오류: {e}")
        return None


def load_tsv_file(tsv_path):
    """TSV 파일을 로드하고 번역 데이터를 딕셔너리로 변환"""
    translations = {}
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            
            # 헤더 찾기 (번역 ID가 있는 행)
            data_start_row = 0
            for i, row in enumerate(rows):
                if len(row) > 0 and ('번역 ID' in row[0] or '아이템 ID' in row[0]):
                    data_start_row = i + 1
                    break
            
            # 데이터 행들 처리
            for row in rows[data_start_row:]:
                if len(row) >= 5 and row[0].strip():  # 빈 행 건너뛰기
                    item_id = row[0].strip().replace('"', '').replace(':', '')
                    if item_id:
                        translations[item_id] = {
                            '한글_원문': row[1] if len(row) > 1 else '',
                            '아이템코드': row[2] if len(row) > 2 else '',
                            '번역문': row[3] if len(row) > 3 else '',
                            '번역_입력문': row[4] if len(row) > 4 else '',
                            '카테고리': row[5] if len(row) > 5 else '',
                            '비고': row[6] if len(row) > 6 else '',
                            '영문_원문': row[7] if len(row) > 7 else '',
                            '영문_아이템_ID': row[8] if len(row) > 8 else ''
                        }
        
        return translations, rows[:data_start_row]  # 헤더도 함께 반환
        
    except Exception as e:
        print(f"TSV 파일 로드 오류: {e}")
        return {}, []


def create_updated_tsv(json_data, existing_translations, header_rows, output_path):
    """새로운 순서로 TSV 파일 생성"""
    
    # 백업 파일 생성
    backup_path = output_path.replace('.tsv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tsv')
    if os.path.exists(output_path):
        os.rename(output_path, backup_path)
        print(f"기존 파일을 백업했습니다: {backup_path}")
    
    new_entries = []
    updated_entries = []
    
    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # 헤더 행들 작성
            for header_row in header_rows:
                writer.writerow(header_row)
            
            # JSON의 키 순서대로 데이터 작성
            for key, value in json_data.items():
                if key in existing_translations:
                    # 기존 번역이 있는 경우
                    trans_data = existing_translations[key]
                    row = [
                        f'"{key}":',
                        trans_data['한글_원문'],
                        f'"{key}":',
                        trans_data['번역문'],
                        trans_data['번역_입력문'],
                        trans_data['카테고리'],
                        trans_data['비고'],
                        trans_data['영문_원문'],
                        trans_data['영문_아이템_ID']
                    ]
                    updated_entries.append(key)
                else:
                    # 새로운 항목인 경우
                    row = [
                        f'"{key}":',
                        value,  # JSON의 값을 한글 원문으로
                        f'"{key}":',
                        f'"{value}",',  # 기본 번역문
                        value,  # 번역 입력문은 비워둠
                        '',  # 카테고리
                        f'새로 추가됨 ({datetime.now().strftime("%Y-%m-%d")})',  # 비고에 날짜 포함
                        '',  # 영문 원문
                        ''   # 영문 아이템 ID
                    ]
                    new_entries.append(key)
                
                writer.writerow(row)
        
        return new_entries, updated_entries
        
    except Exception as e:
        print(f"TSV 파일 생성 오류: {e}")
        return [], []


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
    
    if len(sys.argv) != 3:
        print("사용법: python translation_sync.py <새로운_kr.json_경로> <기존_TSV_파일_경로>")
        print("예시: python translation_sync.py new_kr.json \"SPT 타르코프 한글화 프로젝트 - 메인 번역 작업.tsv\"")
        sys.exit(1)
    
    json_path = sys.argv[1]
    tsv_path = sys.argv[2]
    
    # 파일 존재 확인
    if not os.path.exists(json_path):
        print(f"JSON 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)
    
    if not os.path.exists(tsv_path):
        print(f"TSV 파일을 찾을 수 없습니다: {tsv_path}")
        sys.exit(1)
    
    print("번역 동기화를 시작합니다...")
    
    # 파일 로드
    print("1. JSON 파일 로드 중...")
    json_data = load_json_file(json_path)
    if json_data is None:
        sys.exit(1)
    
    print("2. TSV 파일 로드 중...")
    existing_translations, header_rows = load_tsv_file(tsv_path)
    
    print(f"   - 기존 번역 항목 수: {len(existing_translations)}")
    print(f"   - 새 JSON 항목 수: {len(json_data)}")
    
    # TSV 업데이트
    print("3. TSV 파일 업데이트 중...")
    new_entries, updated_entries = create_updated_tsv(
        json_data, existing_translations, header_rows, tsv_path
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
    
    # 누락된 항목 확인
    missing_entries = set(existing_translations.keys()) - set(json_data.keys())
    if missing_entries:
        print(f"\n주의: 새 JSON에서 제거된 항목들: {len(missing_entries)}개")
        for entry in list(missing_entries)[:5]:
            print(f"  - {entry}")
        if len(missing_entries) > 5:
            print(f"  ... 및 {len(missing_entries) - 5}개 더")
    
    print(f"\n업데이트된 TSV 파일: {tsv_path}")
    print("번역 작업을 계속 진행하세요!")


if __name__ == "__main__":
    main()