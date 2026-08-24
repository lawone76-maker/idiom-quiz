import streamlit as st
import random
import re

# 1. 사자성어 데이터 불러오기
@st.cache_data
def load_data():
    idioms = []
    lines = []
    
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
        
        parts = re.split(r'[:\-,\t]', line, maxsplit=1)
        if len(parts) == 2:
            idiom = parts[0].strip()
            meaning = parts[1].strip()
            if idiom and meaning:
                idioms.append({'idiom': idiom, 'meaning': meaning})
        else:
            space_parts = line.split(maxsplit=1)
            if len(space_parts) == 2:
                idioms.append({'idiom': space_parts[0].strip(), 'meaning': space_parts[1].strip()})
            
    return idioms

all_idioms = load_data()

# 데이터가 비어있을 경우 예외 처리
if not all_idioms:
    st.error("⚠️ 'Four-Character_Idiom.txt' 파일에서 단어를 불러오지 못했습니다.")
    st.stop()

# 2. 사이드바 설정 (퀴즈 모드 및 로드 상태)
st.sidebar.title("⚙️ 퀴즈 설정")
st.sidebar.write(f"📊 총 로드된 사자성어: **{len(all_idioms)}개**")
quiz_mode = st.sidebar.radio("문제 유형 선택", ["객관식 (4지선다)", "주관식"])

# 3. 세션 상태 초기화 (전체 문제 셔플 큐)
if 'quiz_queue' not in st.session_state or not st.session_state.quiz_queue:
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.quiz_queue = shuffled

if 'current_question' not in st.session_state:
    st.session_state.current_question = st.session_state.quiz_queue.pop()

# 보기(4지선다) 세션 상태 생성 함수
def generate_options(correct_item):
    other_idioms = [item['idiom'] for item in all_idioms if item['idiom'] != correct_item['idiom']]
    wrong_options = random.sample(other_idioms, k=min(3, len(other_idioms)))
    options = wrong_options + [correct_item['idiom']]
    random.shuffle(options)
    return options

if 'current_options' not in st.session_state:
    st.session_state.current_options = generate_options(st.session_state.current_question)

# 다음 문제 넘어가기 함수
def next_question():
    if st.session_state.quiz_queue:
        st.session_state.current_question = st.session_state.quiz_queue.pop()
    else:
        shuffled = all_idioms.copy()
        random.shuffle(shuffled)
        st.session_state.quiz_queue = shuffled
        st.session_state.current_question = st.session_state.quiz_queue.pop()
    
    st.session_state.current_options = generate_options(st.session_state.current_question)

# --- 메인 화면 ---
st.title("🏯 사자성어 퀴즈 앱")

current = st.session_state.current_question

st.subheader(f"문제: {current['meaning']}")
st.write("---")

# 모드별 입력창 분기
if quiz_mode == "객관식 (4지선다)":
    selected_option = st.radio("알맞은 사자성어를 선택하세요:", st.session_state.current_options, key="radio_choice")
    
    if st.button("정답 확인"):
        if selected_option == current['idiom']:
            st.success("🎉 정답입니다!")
        else:
            st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")

else:  # 주관식
    user_answer = st.text_input("정답(사자성어)을 입력하세요:", key="user_input")
    
    if st.button("정답 확인"):
        if user_answer.strip() == current['idiom']:
            st.success("🎉 정답입니다!")
        else:
            st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")

st.write("")
if st.button("다음 문제 ➡️"):
    next_question()
    st.rerun()
    