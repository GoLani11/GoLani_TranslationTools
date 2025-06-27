#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
타르코프 한글화 번역 동기화 도구 - GUI 버전
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import subprocess
from datetime import datetime


class TranslationSyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("타르코프 한글화 번역 동기화 도구")
        self.root.geometry("600x500")
        
        # 파일 경로 변수
        self.json_path = tk.StringVar()
        self.tsv_path = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="타르코프 한글화 번역 동기화 도구", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # JSON 파일 선택
        ttk.Label(main_frame, text="새로운 kr.json 파일:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.json_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="찾기", command=self.select_json_file).grid(row=1, column=2, pady=5)
        
        # TSV 파일 선택
        ttk.Label(main_frame, text="기존 TSV 파일:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.tsv_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="찾기", command=self.select_tsv_file).grid(row=2, column=2, pady=5)
        
        # 실행 버튼
        run_button = ttk.Button(main_frame, text="동기화 실행", command=self.run_sync)
        run_button.grid(row=3, column=0, columnspan=3, pady=20)
        
        # 진행 상태 표시
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 상태 레이블
        self.status_label = ttk.Label(main_frame, text="파일을 선택하고 동기화 실행을 클릭하세요.")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)
        
        # 로그 출력 영역
        ttk.Label(main_frame, text="실행 로그:").grid(row=6, column=0, sticky=tk.W, pady=(20, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, width=70, height=15)
        self.log_text.grid(row=7, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # 자동으로 파일 찾기
        self.auto_find_files()
        
    def auto_find_files(self):
        """현재 디렉토리에서 파일 자동 찾기"""
        current_dir = os.getcwd()
        
        # JSON 파일 찾기
        for file in os.listdir(current_dir):
            if file.endswith('.json') and ('kr' in file.lower() or 'new' in file.lower()):
                self.json_path.set(os.path.join(current_dir, file))
                break
        
        # TSV 파일 찾기
        for file in os.listdir(current_dir):
            if file.endswith('.tsv') and '번역' in file:
                self.tsv_path.set(os.path.join(current_dir, file))
                break
                
    def select_json_file(self):
        filename = filedialog.askopenfilename(
            title="새로운 kr.json 파일 선택",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.json_path.set(filename)
            
    def select_tsv_file(self):
        filename = filedialog.askopenfilename(
            title="기존 TSV 파일 선택",
            filetypes=[("TSV files", "*.tsv"), ("All files", "*.*")]
        )
        if filename:
            self.tsv_path.set(filename)
            
    def log_message(self, message):
        """로그 영역에 메시지 추가"""
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def run_sync(self):
        """동기화 실행"""
        json_file = self.json_path.get()
        tsv_file = self.tsv_path.get()
        
        if not json_file or not tsv_file:
            messagebox.showerror("오류", "JSON 파일과 TSV 파일을 모두 선택해주세요.")
            return
            
        if not os.path.exists(json_file):
            messagebox.showerror("오류", f"JSON 파일을 찾을 수 없습니다: {json_file}")
            return
            
        if not os.path.exists(tsv_file):
            messagebox.showerror("오류", f"TSV 파일을 찾을 수 없습니다: {tsv_file}")
            return
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self._run_sync_thread, args=(json_file, tsv_file))
        thread.daemon = True
        thread.start()
        
    def _run_sync_thread(self, json_file, tsv_file):
        """동기화를 별도 스레드에서 실행"""
        try:
            self.status_label.config(text="동기화 실행 중...")
            self.progress.start()
            self.log_text.delete(1.0, tk.END)
            
            self.log_message("동기화를 시작합니다...")
            self.log_message(f"JSON 파일: {os.path.basename(json_file)}")
            self.log_message(f"TSV 파일: {os.path.basename(tsv_file)}")
            
            # Python 스크립트를 직접 호출하는 대신 임포트해서 실행
            try:
                # 스크립트 디렉토리를 sys.path에 추가
                script_dir = os.path.dirname(__file__)
                if script_dir not in sys.path:
                    sys.path.insert(0, script_dir)
                
                # 직접 함수 호출로 변경
                import translation_sync
                
                # sys.argv 임시 설정
                old_argv = sys.argv
                sys.argv = ['translation_sync.py', json_file, tsv_file]
                
                # 메인 함수 실행
                translation_sync.main()
                
                # sys.argv 복원
                sys.argv = old_argv
                
                # 성공으로 처리
                result_success = True
                result_output = "동기화가 성공적으로 완료되었습니다."
                
            except SystemExit as e:
                # 정상 종료인 경우
                result_success = (e.code == 0 or e.code is None)
                result_output = "동기화가 완료되었습니다."
                sys.argv = old_argv
            except Exception as e:
                result_success = False
                result_output = f"오류 발생: {str(e)}"
                sys.argv = old_argv
            
            self.progress.stop()
            
            if result_success:
                self.status_label.config(text="동기화가 성공적으로 완료되었습니다!")
                self.log_message("=== 동기화 완료 ===")
                self.log_message(result_output)
                messagebox.showinfo("완료", "동기화가 성공적으로 완료되었습니다!")
            else:
                self.status_label.config(text="동기화 중 오류가 발생했습니다.")
                self.log_message("=== 오류 발생 ===")
                self.log_message(result_output)
                messagebox.showerror("오류", f"동기화 중 오류가 발생했습니다:\n{result_output}")
                
        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="오류가 발생했습니다.")
            self.log_message(f"예외 발생: {str(e)}")
            messagebox.showerror("오류", f"예외가 발생했습니다:\n{str(e)}")


def main():
    root = tk.Tk()
    app = TranslationSyncGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()