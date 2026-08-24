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

if not all_idioms:
    st.error("⚠️ 'Four-Character_Idiom.txt' 파일에서 단어를 불러오지 못했습니다.")
    st.stop()

# 2. 세션 상태 초기화
if 'wrong_notes' not in st.session_state:
    st.session_state.wrong_notes = []  # 틀린 문제 리스트

if 'quiz_queue' not in st.session_state or not st.session_state.quiz_queue:
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.quiz_queue = shuffled

if 'wrong_queue' not in st.session_state:
    st.session_state.wrong_queue = []

if 'current_question' not in st.session_state:
    st.session_state.current_question = st.session_state.quiz_queue.pop()

# 보기(4지선다) 생성 함수
def generate_options(correct_item):
    other_idioms = [item['idiom'] for item in all_idioms if item['idiom'] != correct_item['idiom']]
    wrong_options = random.sample(other_idioms, k=min(3, len(other_idioms)))
    options = wrong_options + [correct_item['idiom']]
    random.shuffle(options)
    return options

if 'current_options' not in st.session_state:
    st.session_state.current_options = generate_options(st.session_state.current_question)

# 3. 사이드바 메뉴 구성
st.sidebar.title("⚙️ 퀴즈 및 오답노트 설정")
st.sidebar.write(f"📊 전체 사자성어: **{len(all_idioms)}개**")
st.sidebar.write(f"📝 저장된 오답: **{len(st.session_state.wrong_notes)}개**")

test_target = st.sidebar.radio("테스트 대상 선택", ["전체 문제 테스트", "오답노트 테스트"])
quiz_type = st.sidebar.radio("문제 유형 선택", ["객관식 (4지선다)", "주관식"])

st.sidebar.write("---")
if st.sidebar.button("🗑️ 오답노트 초기화"):
    st.session_state.wrong_notes = []
    st.session_state.wrong_queue = []
    st.sidebar.success("오답노트가 초기화되었습니다.")
    st.rerun()

# 4. 문제 갱신 함수
def next_question(target_mode):
    if target_mode == "전체 문제 테스트":
        if not st.session_state.quiz_queue:
            shuffled = all_idioms.copy()
            random.shuffle(shuffled)
            st.session_state.quiz_queue = shuffled
        st.session_state.current_question = st.session_state.quiz_queue.pop()
    else:  # 오답노트 테스트
        if not st.session_state.wrong_queue and st.session_state.wrong_notes:
            st.session_state.wrong_queue = st.session_state.wrong_notes.copy()
            random.shuffle(st.session_state.wrong_queue)
        
        if st.session_state.wrong_queue:
            st.session_state.current_question = st.session_state.wrong_queue.pop()

    st.session_state.current_options = generate_options(st.session_state.current_question)

# --- 메인 화면 ---
st.title("🏯 사자성어 퀴즈 앱")

# 오답노트 모드 선택 시 오답이 없는 경우 예외 처리
if test_target == "오답노트 테스트" and not st.session_state.wrong_notes:
    st.info("🎉 저장된 오답이 없습니다! '전체 문제 테스트'에서 틀린 문제가 생기면 이곳에 자동으로 추가됩니다.")
else:
    current = st.session_state.current_question
    
    st.caption(f"📌 현재 모드: **{test_target}** | **{quiz_type}**")
    st.subheader(f"문제: {current['meaning']}")
    st.write("---")

    # 객관식 / 주관식 분기 처리
    if quiz_type == "객관식 (4지선다)":
        selected_option = st.radio("알맞은 사자성어를 선택하세요:", st.session_state.current_options, key="radio_choice")
        
        if st.button("정답 확인"):
            if selected_option == current['idiom']:
                st.success("🎉 정답입니다!")
                # 오답노트 모드에서 정답을 맞추면 오답노트에서 제거
                if test_target == "오답노트 테스트" and current in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.remove(current)
            else:
                st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")
                # 전체 문제 모드에서 틀리면 오답노트에 추가
                if test_target == "전체 문제 테스트" and current not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(current)

    else:  # 주관식
        user_answer = st.text_input("정답(사자성어)을 입력하세요:", key="user_input")
        
        if st.button("정답 확인"):
            if user_answer.strip() == current['idiom']:
                st.success("🎉 정답입니다!")
                if test_target == "오답노트 테스트" and current in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.remove(current)
            else:
                st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")
                if test_target == "전체 문제 테스트" and current not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(current)

    st.write("")
    if st.button("다음 문제 ➡️"):
        next_question(test_target)
        st.rerun()
        