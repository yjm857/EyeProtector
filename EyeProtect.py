from pynput import mouse, keyboard
import time
import threading
import pyttsx3
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import sys

# 경고 시그널을 위한 클래스 추가
class SignalEmitter(QObject):
    warning_signal = pyqtSignal()

class EyeProtector:
    def __init__(self):
        # QApplication 인스턴스 생성
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
            
        # 시그널 이미터 생성
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.warning_signal.connect(self.show_warning)
        
        self.last_activity = time.time()
        self.warning_shown = False
        self.CONTINUOUS_USE_LIMIT = 1800  # 30분 (초 단위)
        self.IDLE_RESET_TIME = 60    # 1분 (초 단위)
        self.REST_TIME = 600         # 10분 휴식 시간 (초 단위)
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
        self.is_speaking = False  # 음성 출력 상태 추적을 위한 변수 추가
        
    def on_activity(self, *args):
        current_time = time.time()
        # 10초 이상 활동이 없었다면 타이머 리셋
        if current_time - self.last_activity > self.IDLE_RESET_TIME:
            self.warning_shown = False
            self.start_time = current_time  # 연속 사용 시작 시간 리셋
        self.last_activity = current_time
        
    def speak(self, text):
        """음성 출력을 전하게 처리하는 메서드"""
        if not self.is_speaking:
            try:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
            finally:
                self.is_speaking = False
        
    def show_warning(self):
        # 경고 시간 기록
        self.warning_time = time.time()
        
        # 음성 경고 재생
        self.speak("컴퓨터 속 사용시간 초과")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("눈 보호 알림")
        msg.setText("30분 동안 �속으로 컴퓨터를 사용하셨습니다!")
        msg.setInformativeText("잠시 휴식을 취하는 것은 어떨까요?\n\n눈 건강을 위해 10분 동안 휴식을 취하세요.")
        msg.setStandardButtons(QMessageBox.NoButton)  # 버튼 제거
        
        # 항상 위에 표시하고 이동 불가능하게 설정
        msg.setWindowFlags(
            Qt.WindowStaysOnTopHint |    # 항상 위에 표시
            Qt.FramelessWindowHint |     # 타이틀바 제거
            Qt.WindowDoesNotAcceptFocus |# 포스 받지 않음
            Qt.CustomizeWindowHint |     # 기본 장식 제거
            Qt.WindowFullScreen         # 전체 풀면 모드
        )
        msg.setAttribute(Qt.WA_DeleteOnClose, False)  # 창 닫기 방지
        msg.setAttribute(Qt.WA_ShowWithoutActivating, True)  # 활성화 없이 표시
        
        # 화면 크기 가져오기
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 메시지 박스 크기를 화면 전체로 설정
        msg.setFixedSize(screen_width, screen_height)
        
        # 글자 크기를 화면 크기에 맞게 조정 (더 크게)
        font_size = int(min(screen_width, screen_height) * 0.04)  # 폰트 크기 증가
        
        # 화면 좌상에 위치시키기 (전체화면)
        msg.move(0, 0)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: rgba(0, 0, 0, 0.9);  /* 어두운 배경 */
                min-width: {screen_width}px;
                min-height: {screen_height}px;
            }}
            QMessageBox QLabel {{
                color: white;  /* 흰색 텍스트 */
                font-size: {font_size}px;
                qproperty-alignment: AlignCenter;
            }}
            QMessageBox QLabel:first {{
                font-weight: bold;
                margin-bottom: 40px;
                color: #FF6B6B;  /* 경고 메시지는 붉은 계열 */
            }}
        """)
        
        timer = QTimer()
        timer.remaining = self.REST_TIME
        self.rest_start_time = time.time()  # 휴식 시작 시간 기록
        
        def update_message():
            current_time = time.time()
            # 휴식 중 활동이 감지되었는지 확인
            if current_time - self.last_activity < 1:  # 1초 이내에 활동이 있었다면
                # 타이머 리셋
                timer.remaining = self.REST_TIME
                self.rest_start_time = current_time
                minutes = timer.remaining // 60
                seconds = timer.remaining % 60
                msg.setInformativeText(f"컴퓨터 사용이 감지되었습니다!\n\n"
                                    f"눈 건강을 위해 10분 동안\n"
                                    f"화면에서 시선을 멀리 두세요.\n\n"
                                    f"남은 시간: {minutes}� {seconds}초")
            elif timer.remaining > 0:
                minutes = timer.remaining // 60
                seconds = timer.remaining % 60
                msg.setInformativeText(f"잠시 휴식을 취하는 것은 어떨까요?\n\n"
                                    f"눈 건강을 위해 ��식을 취하세요.\n\n"
                                    f"남은 시간: {minutes}� {seconds}초")
                timer.remaining -= 1
            else:
                msg.done(0)  # 메시지 박스 닫기
                timer.stop()  # 타이머 중지
                # 휴식 완료 시 연속 사용 시간 초기화
                self.start_time = time.time()
                self.warning_shown = False
                print("\n휴식 완료! 다시 시작합니다.")
                # 휴식 완료 음성 알림
                self.speak("휴식 완료. 다시 시작하세요")
        
        timer.timeout.connect(update_message)
        timer.start(1000)  # 1초마다 업데이트
        
        msg.exec_()
        timer.stop()
        
    def check_time(self):
        while True:
            current_time = time.time()
            
            # 경고 후 30초 휴식 시간이 지났는지 확인
            if self.warning_shown and current_time - self.last_activity >= self.REST_TIME:
                self.warning_shown = False
                self.start_time = current_time
                print("\n휴식 완료! 다시 시작합니다.")
                # 휴식 완료 음성 알림
                self.speak("휴식 완료. 다시 시작하세요")
            
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
                # 시그널 발생
                self.signal_emitter.warning_signal.emit()
                self.warning_shown = True
            
            time.sleep(1)
            
    def start(self):
        self.mouse_listener.start()
        self.keyboard_listener.start()
        self.check_thread.start()
        
        # 프로그램이 계속 실행되도록 유지
        try:
            while True:
                self.app.processEvents()  # Qt 이벤트 처리리
                time.sleep(0.1)  # CPU 사용량 감소
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    protector = EyeProtector()
    protector.start()
