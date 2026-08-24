import streamlit as st
import random
import re
import time
import json
from supabase import create_client, Client

# --- Supabase 설정 ---
SUPABASE_URL = "https://vstetskytidhvqeyxyyi.supabase.co"
SUPABASE_KEY = "sb_publishable_WwjtW2g3-5dHGKOAbXbBNw_2dL5ZU-G"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Custom CSS
st.markdown("""
    <style>
    .main-title { font-size: 1.8rem !important; font-weight: 700; margin-bottom: 0.5rem; }
    .question-title { font-size: 1.25rem !important; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# 1. 사자성어 원본 데이터 불러오기
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

# 고정 보기 생성 함수
def generate_options_for_item(correct_item):
    other_idioms = [item['idiom'] for item in all_idioms if item['idiom'] != correct_item['idiom']]
    wrong_options = random.sample(other_idioms, k=min(3, len(other_idioms)))
    options = wrong_options + [correct_item['idiom']]
    random.shuffle(options)
    return options

user_id = "default_user"

# 2. DB에서 학습 진행 상황 및 문제 순서 불러오기
if "db_loaded" not in st.session_state:
    try:
        res = supabase.table("user_progress").select("*").eq("user_id", user_id).execute()
        if res.data and "shuffled_list" in res.data[0] and res.data[0]["shuffled_list"]:
            st.session_state.current_idx = res.data[0].get("current_idx", 0)
            st.session_state.wrong_notes = res.data[0].get("wrong_notes", [])
            st.session_state.shuffled_list = res.data[0].get("shuffled_list", [])
            st.session_state.options_dict = res.data[0].get("options_dict", {})
        else:
            # 최초 실행 시 문제 순서 및 보기 생성 후 저장
            shuffled = all_idioms.copy()
            random.shuffle(shuffled)
            st.session_state.shuffled_list = shuffled
            st.session_state.options_dict = {item['idiom']: generate_options_for_item(item) for item in all_idioms}
            st.session_state.current_idx = 0
            st.session_state.wrong_notes = []
            
            supabase.table("user_progress").upsert({
                "user_id": user_id,
                "current_idx": 0,
                "wrong_notes": [],
                "shuffled_list": st.session_state.shuffled_list,
                "options_dict": st.session_state.options_dict
            }).execute()
    except Exception:
        # DB 읽기 실패 시 세션 폴백
        shuffled = all_idioms.copy()
        random.shuffle(shuffled)
        st.session_state.shuffled_list = shuffled
        st.session_state.options_dict = {item['idiom']: generate_options_for_item(item) for item in all_idioms}
        st.session_state.current_idx = 0
        st.session_state.wrong_notes = []
    
    st.session_state.db_loaded = True

# DB 동기화 함수
def save_to_db():
    try:
        supabase.table("user_progress").upsert({
            "user_id": user_id,
            "current_idx": st.session_state.current_idx,
            "wrong_notes": st.session_state.wrong_notes,
            "shuffled_list": st.session_state.shuffled_list,
            "options_dict": st.session_state.options_dict
        }).execute()
    except Exception:
        pass

# 3. 사이드바 메뉴
st.sidebar.title("⚙️ 퀴즈 및 오답노트 설정")
st.sidebar.write(f"📊 전체 사자성어: **{len(all_idioms)}개**")
st.sidebar.write(f"📝 저장된 오답: **{len(st.session_state.wrong_notes)}개**")

test_target = st.sidebar.radio("테스트 대상 선택", ["전체 문제 테스트", "오답노트 테스트"], key="test_target_radio")
quiz_type = st.sidebar.radio("문제 유형 선택", ["객관식 (4지선다)", "주관식"], key="quiz_type_radio")

st.sidebar.write("---")
if st.sidebar.button("🔄 진행도 & 순서 완전 초기화"):
    shuffled = all_idioms.copy()
    random.shuffle(shuffled)
    st.session_state.shuffled_list = shuffled
    st.session_state.options_dict = {item['idiom']: generate_options_for_item(item) for item in all_idioms}
    st.session_state.wrong_notes = []
    st.session_state.current_idx = 0
    save_to_db()
    st.sidebar.success("학습 진행도와 문제 순서가 모두 새롭게 초기화되었습니다.")
    st.rerun()

# 4. 테스트 목록 추출
active_list = st.session_state.shuffled_list if test_target == "전체 문제 테스트" else st.session_state.wrong_notes

def go_next_question():
    if st.session_state.current_idx < len(active_list) - 1:
        st.session_state.current_idx += 1
    else:
        st.session_state.current_idx = 0
    save_to_db()

def go_prev_question():
    if st.session_state.current_idx > 0:
        st.session_state.current_idx -= 1
    else:
        st.session_state.current_idx = len(active_list) - 1
    save_to_db()

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

    # 객관식 / 주관식 문제 출제
    if quiz_type == "객관식 (4지선다)":
        options = st.session_state.options_dict.get(current['idiom'], generate_options_for_item(current))
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
            
            save_to_db()
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
            
            save_to_db()
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