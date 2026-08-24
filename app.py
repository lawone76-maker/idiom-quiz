import streamlit as st
import random

# 1. 사자성어 데이터 불러오기 함수 (캐싱 적용)
@st.cache_data
def load_data():
    idioms = []
    try:
        # utf-8로 읽기 시도 (안 될 경우 cp949)
        with open('Four-Character_Idiom.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open('Four-Character_Idiom.txt', 'r', encoding='cp949') as f:
            lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line and ':' in line:  # 구분자가 ':' 기준일 경우 (파일 양식에 맞게 변경)
            parts = line.split(':', 1)
            idioms.append({'idiom': parts[0].strip(), 'meaning': parts[1].strip()})
        elif line and '\t' in line:  # 탭 구분일 경우
            parts = line.split('\t', 1)
            idioms.append({'idiom': parts[0].strip(), 'meaning': parts[1].strip()})
            
    return idioms

all_idioms = load_data()

# 데이터 개수 확인용 디버깅 (사이드바에 전체 개수 표시)
st.sidebar.write(f"📊 총 로드된 사자성어: {len(all_idioms)}개")

# 2. 세션 상태 초기화 (전체 문제 셔플 리스트 생성)
if 'quiz_queue' not in st.session_state or not st.session_state.quiz_queue:
    # 전체 문제를 복사한 뒤 무작위로 섞음
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.quiz_queue = shuffled

if 'current_question' not in st.session_state:
    st.session_state.current_question = st.session_state.quiz_queue.pop()

# 3. 다음 문제 넘어가기 함수
def next_question():
    if st.session_state.quiz_queue:
        st.session_state.current_question = st.session_state.quiz_queue.pop()
    else:
        # 모든 문제를 다 푼 경우 다시 섞기
        shuffled = all_idioms.copy()
        random.shuffle(shuffled)
        st.session_state.quiz_queue = shuffled
        st.session_state.current_question = st.session_state.quiz_queue.pop()
        st.success("🎉 모든 문제를 한 바퀴 완주했습니다! 다시 섞어서 시작합니다.")

# --- 화면 출력 부분 ---
st.title("🏯 사자성어 퀴즈 앱")

current = st.session_state.current_question

st.subheader(f"문제: {current['meaning']}")

# (정답 입력 및 확인 로직...)

if st.button("다음 문제"):
    next_question()
    st.rerun()