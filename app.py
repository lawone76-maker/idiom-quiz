import streamlit as st
import random
import re

# 1. 사자성어 데이터 불러오기 함수 (다양한 구분 기호 자동 처리)
@st.cache_data
def load_data():
    idioms = []
    lines = []
    
    # 파일 인코딩 예외 처리
    try:
        with open('Four-Character_Idiom.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        try:
            with open('Four-Character_Idiom.txt', 'r', encoding='cp949') as f:
                lines = f.readlines()
        except Exception:
            return idioms

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 콜론(:), 하이픈(-), 쉼표(,), 탭(\t) 중 하나로 분리 시도
        parts = re.split(r'[:\-,\t]', line, maxsplit=1)
        
        if len(parts) == 2:
            idiom = parts[0].strip()
            meaning = parts[1].strip()
            if idiom and meaning:
                idioms.append({'idiom': idiom, 'meaning': meaning})
        else:
            # 기호가 없으면 첫 공백을 기준으로 단어와 뜻 분리
            space_parts = line.split(maxsplit=1)
            if len(space_parts) == 2:
                idioms.append({'idiom': space_parts[0].strip(), 'meaning': space_parts[1].strip()})
            
    return idioms

all_idioms = load_data()

# 로드 상태 사이드바 표시
st.sidebar.write(f"📊 총 로드된 사자성어: {len(all_idioms)}개")

# 데이터가 비어있을 경우 안전장치
if not all_idioms:
    st.error("⚠️ 'Four-Character_Idiom.txt' 파일에서 단어를 불러오지 못했습니다. 파일 내용 형식을 확인해 주세요.")
    st.stop()

# 2. 세션 상태 초기화 (전체 문제 셔플 큐)
if 'quiz_queue' not in st.session_state or not st.session_state.quiz_queue:
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.quiz_queue = shuffled

if 'current_question' not in st.session_state:
    st.session_state.current_question = st.session_state.quiz_queue.pop()

# 3. 다음 문제 넘어가는 함수
def next_question():
    if st.session_state.quiz_queue:
        st.session_state.current_question = st.session_state.quiz_queue.pop()
    else:
        shuffled = all_idioms.copy()
        random.shuffle(shuffled)
        st.session_state.quiz_queue = shuffled
        st.session_state.current_question = st.session_state.quiz_queue.pop()

# --- 메인 화면 ---
st.title("🏯 사자성어 퀴즈 앱")

current = st.session_state.current_question

st.subheader(f"문제: {current['meaning']}")

# 정답 확인 예시 (기존 코드에 맞게 변경 가능)
user_answer = st.text_input("정답(사자성어)을 입력하세요:", key="user_input")

if st.button("정답 확인"):
    if user_answer.strip() == current['idiom']:
        st.success("🎉 정답입니다!")
    else:
        st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")

if st.button("다음 문제"):
    next_question()
    st.rerun()
    