from pynput import mouse, keyboard
from tkinter import Tk, messagebox
import time
import threading
import tkinter as tk
import pyttsx3  # 파일 상단에 추가

class EyeProtector:
    def __init__(self):
        self.last_activity = time.time()
        self.warning_shown = False
        self.CONTINUOUS_USE_LIMIT = 180  # 3분 (초 단위)
        self.IDLE_RESET_TIME = 60    # 1분 (초 단위)
        self.REST_TIME = 30          # 30초 휴식 시간 추가
        self.start_time = time.time()
        self.warning_time = 0        # 경고가 발생한 시간 추가
        
        # 마우스 리스너 설정
        self.mouse_listener = mouse.Listener(
            on_move=self.on_activity,
            on_click=self.on_activity,
            on_scroll=self.on_activity
        )
        
        # 키보드 리스너 설정
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_activity
        )
        
        # 시간 체크 쓰레드 시작
        self.check_thread = threading.Thread(target=self.check_time, daemon=True)
        
        self.engine = pyttsx3.init()  # TTS 엔진 초기화
        self.engine.setProperty('rate', 150)  # 말하기 속도 설정
        
    def on_activity(self, *args):
        current_time = time.time()
        # 10초 이상 활동이 없었다면 타이머 리셋
        if current_time - self.last_activity > self.IDLE_RESET_TIME:
            self.warning_shown = False
            self.start_time = current_time  # 연속 사용 시작 시간 리셋
        self.last_activity = current_time
        
    def show_warning(self):
        # 경고 시간 기록
        self.warning_time = time.time()
        
        # 경고 창 생성
        warning_window = tk.Tk()
        warning_window.title("눈 건강 경고")
        
        # 화면 크기 가져오기
        screen_width = warning_window.winfo_screenwidth()
        screen_height = warning_window.winfo_screenheight()
        
        # 경고창 크기 설정 (화면의 1/3 크기)
        window_width = screen_width // 3
        window_height = screen_height // 3
        
        # 경고창 위치 계산 (화면 중앙)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 경고창 크기와 위치 설정
        warning_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 항상 최상위에 표시
        warning_window.attributes('-topmost', True)
        warning_window.lift()
        warning_window.focus_force()
        
        # 음성 경고 재생
        self.engine.say("컴퓨터 연속 사용시간 초과")
        self.engine.runAndWait()
        
        # 경고 메시지 레이블
        message = tk.Label(
            warning_window,
            text="3분 동안 연속으로\n컴퓨터를 사용하셨습니다!\n\n잠시 휴식을 취하는 것은\n어떨까요?",
            font=("Arial", 20, "bold"),
            pady=30
        )
        message.pack(expand=True)
        
        # 카운트다운 레이블
        countdown_label = tk.Label(
            warning_window,
            text="남은 휴식 시간: 30초",
            font=("Arial", 16),
            pady=10
        )
        countdown_label.pack()
        
        # 경고음 재생
        warning_window.bell()
        
        # 카운트다운 함수
        def update_countdown():
            remaining = self.REST_TIME - (time.time() - self.warning_time)
            if remaining <= 0:
                warning_window.destroy()
            else:
                countdown_label.config(text=f"남은 휴식 시간: {int(remaining)}초")
                warning_window.after(1000, update_countdown)
        
        # 카운트다운 시작
        update_countdown()
        
        # 창이 닫힐 때까지 대기
        warning_window.mainloop()
        
    def check_time(self):
        while True:
            current_time = time.time()
            
            # 경고 후 30초 휴식 시간이 지났는지 확인
            if self.warning_shown and current_time - self.last_activity >= self.REST_TIME:
                self.warning_shown = False
                self.start_time = current_time
                print("\n휴식 완료! 다시 시작합니다.")
                # 휴식 완료 음성 알림
                self.engine.say("휴식 완료. 다시 시작하세요")
                self.engine.runAndWait()
            
            # 마지막 활동으로부터 1분 이상 지났는지 확인
            if current_time - self.last_activity > self.IDLE_RESET_TIME:
                self.start_time = current_time
                self.warning_shown = False
            
            # 현재 연속 사용 시간 계산
            usage_time = current_time - self.start_time
            
            # 연속 사용 시간 출력 (분:초 형식)
            minutes = int(usage_time // 60)
            seconds = int(usage_time % 60)
            print(f"\r현재 연속 사용 시간: {minutes:02d}:{seconds:02d}", end="")
            
            # 3분 이상 연속 사용했고, 아직 경고를 보여주지 않았다면
            if (usage_time >= self.CONTINUOUS_USE_LIMIT and 
                not self.warning_shown and 
                current_time - self.last_activity < self.IDLE_RESET_TIME):
                self.show_warning()
                self.warning_shown = True
            
            time.sleep(1)
            
    def start(self):
        self.mouse_listener.start()
        self.keyboard_listener.start()
        self.check_thread.start()
        
        # 프로그램이 계속 실행되도록 유지
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    protector = EyeProtector()
    protector.start()
