import streamlit as st
import random
import re
import time
import json
import extra_streamlit_components as stx

# Custom CSS로 글자 크기 축소 (약 70% 수준)
st.markdown("""
    <style>
    .main-title { font-size: 1.8rem !important; font-weight: 700; margin-bottom: 0.5rem; }
    .question-title { font-size: 1.25rem !important; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# 브라우저 쿠키 관리자 생성 (@st.cache_resource 제거)
cookie_manager = stx.CookieManager()

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
            idiom, meaning = parts[0].strip(), parts[1].strip()
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

# 2. 저장된 데이터 복원 (오답노트 및 진행 위치)
saved_wrong_str = cookie_manager.get(cookie="idiom_wrong_notes")
saved_idx_str = cookie_manager.get(cookie="idiom_current_idx")

if 'wrong_notes' not in st.session_state:
    if saved_wrong_str:
        try:
            st.session_state.wrong_notes = json.loads(saved_wrong_str)
        except Exception:
            st.session_state.wrong_notes = []
    else:
        st.session_state.wrong_notes = []

if 'current_idx' not in st.session_state:
    if saved_idx_str:
        try:
            st.session_state.current_idx = int(saved_idx_str)
        except Exception:
            st.session_state.current_idx = 0
    else:
        st.session_state.current_idx = 0

# 기본 세션 초기화
if 'shuffled_list' not in st.session_state:
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.shuffled_list = shuffled

def save_state_to_browser():
    try:
        cookie_manager.set("idiom_wrong_notes", json.dumps(st.session_state.wrong_notes, ensure_ascii=False), key="save_wrong")
        cookie_manager.set("idiom_current_idx", str(st.session_state.current_idx), key="save_idx")
    except Exception:
        pass

def get_options_for_item(correct_item):
    other_idioms = [item['idiom'] for item in all_idioms if item['idiom'] != correct_item['idiom']]
    wrong_options = random.sample(other_idioms, k=min(3, len(other_idioms)))
    options = wrong_options + [correct_item['idiom']]
    random.shuffle(options)
    return options

if 'options_dict' not in st.session_state:
    st.session_state.options_dict = {}

# 3. 사이드바 메뉴
st.sidebar.title("⚙️ 퀴즈 및 오답노트 설정")
st.sidebar.write(f"📊 전체 사자성어: **{len(all_idioms)}개**")
st.sidebar.write(f"📝 저장된 오답: **{len(st.session_state.wrong_notes)}개**")

test_target = st.sidebar.radio("테스트 대상 선택", ["전체 문제 테스트", "오답노트 테스트"], key="test_target_radio")
quiz_type = st.sidebar.radio("문제 유형 선택", ["객관식 (4지선다)", "주관식"], key="quiz_type_radio")

st.sidebar.write("---")
if st.sidebar.button("🔄 진행도 & 오답노트 초기화"):
    st.session_state.wrong_notes = []
    st.session_state.current_idx = 0
    try:
        cookie_manager.delete("idiom_wrong_notes")
        cookie_manager.delete("idiom_current_idx")
    except Exception:
        pass
    st.sidebar.success("학습 진행도와 오답노트가 모두 초기화되었습니다.")
    st.rerun()

# 4. 테스트 목록 추출
active_list = st.session_state.shuffled_list if test_target == "전체 문제 테스트" else st.session_state.wrong_notes

def go_next_question():
    if st.session_state.current_idx < len(active_list) - 1:
        st.session_state.current_idx += 1
    else:
        st.session_state.current_idx = 0
    save_state_to_browser()

def go_prev_question():
    if st.session_state.current_idx > 0:
        st.session_state.current_idx -= 1
    else:
        st.session_state.current_idx = len(active_list) - 1
    save_state_to_browser()

# --- 메인 화면 ---
st.markdown('<p class="main-title">🏯 사자성어 퀴즈 앱</p>', unsafe_allow_html=True)

if test_target == "오답노트 테스트" and not active_list:
    st.info("🎉 저장된 오답이 없습니다! '전체 문제 테스트'에서 틀린 문제가 생기면 이곳에 자동으로 유지됩니다.")
else:
    if st.session_state.current_idx >= len(active_list):
        st.session_state.current_idx = 0

    current = active_list[st.session_state.current_idx]
    
    st.caption(f"📌 모드: **{test_target}** | **{quiz_type}** | 현재 진행: **{st.session_state.current_idx + 1} / {len(active_list)}번째 문제**")
    st.markdown(f'<p class="question-title">문제: {current["meaning"]}</p>', unsafe_allow_html=True)
    st.write("---")

    # 객관식 / 주관식 문제 출제 및 자동 전환
    if quiz_type == "객관식 (4지선다)":
        if current['idiom'] not in st.session_state.options_dict:
            st.session_state.options_dict[current['idiom']] = get_options_for_item(current)
        
        options = st.session_state.options_dict[current['idiom']]
        selected_option = st.radio(
            "알맞은 사자성어를 선택하세요:", 
            options, 
            index=None, 
            key=f"radio_{test_target}_{st.session_state.current_idx}"
        )
        
        if selected_option:
            if selected_option == current['idiom']:
                st.success("🎉 정답입니다!")
                if test_target == "오답노트 테스트" and current in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.remove(current)
            else:
                st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")
                if test_target == "전체 문제 테스트" and current not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(current)
            
            save_state_to_browser()
            time.sleep(1.2)
            go_next_question()
            st.rerun()

    else:  # 주관식
        user_answer = st.text_input(
            "정답(사자성어)을 입력 후 Enter를 누르세요:", 
            key=f"text_{test_target}_{st.session_state.current_idx}"
        )
        
        if user_answer.strip():
            if user_answer.strip() == current['idiom']:
                st.success("🎉 정답입니다!")
                if test_target == "오답노트 테스트" and current in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.remove(current)
            else:
                st.error(f"❌ 틀렸습니다. 정답은 [{current['idiom']}] 입니다.")
                if test_target == "전체 문제 테스트" and current not in st.session_state.wrong_notes:
                    st.session_state.wrong_notes.append(current)
            
            save_state_to_browser()
            time.sleep(1.2)
            go_next_question()
            st.rerun()

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전 문제"):
            go_prev_question()
            st.rerun()

    with col2:
        if st.button("다음 문제 ➡️"):
            go_next_question()
            st.rerun()
            