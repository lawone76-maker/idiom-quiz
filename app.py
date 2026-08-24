import streamlit as st
import random
import re
import time
from supabase import create_client, Client

# --- Supabase 접속 설정 ---
SUPABASE_URL = "https://vstetskytidhvqeyxyyi.supabase.co"
SUPABASE_KEY = "sb_publishable_WwjtW2g3-5dHGKOAbXbBNw_2dL5ZU-G"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# UI 스타일 설정
st.markdown("""
    <style>
    .main-title { font-size: 1.8rem !important; font-weight: 700; margin-bottom: 0.5rem; }
    .question-title { font-size: 1.25rem !important; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# 1. 데이터 로드 및 보기 생성 함수
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
    st.error("⚠️ 'Four-Character_Idiom.txt' 파일을 찾을 수 없거나 데이터가 비어있습니다.")
    st.stop()

def generate_options_for_item(correct_item):
    other_idioms = [item['idiom'] for item in all_idioms if item['idiom'] != correct_item['idiom']]
    wrong_options = random.sample(other_idioms, k=min(3, len(other_idioms)))
    options = wrong_options + [correct_item['idiom']]
    random.shuffle(options)
    return options

# 2. 사이드바: 사용자 ID 입력 기능 추가
st.sidebar.title("👤 사용자 관리")
user_input_id = st.sidebar.text_input(
    "사용자 ID (닉네임)", 
    value="default_user", 
    help="본인 ID를 입력하고 Enter를 누르면 내 학습 데이터를 불러옵니다."
)

# ID가 변경되었을 때 데이터 재로드 처리
if "current_user_id" not in st.session_state or st.session_state.current_user_id != user_input_id:
    st.session_state.current_user_id = user_input_id
    st.session_state.db_loaded = False

user_id = st.session_state.current_user_id

# 3. DB 데이터 동기화
if not st.session_state.get("db_loaded", False):
    try:
        res = supabase.table("user_progress").select("*").eq("user_id", user_id).execute()
        if res.data and "shuffled_list" in res.data[0] and res.data[0]["shuffled_list"]:
            st.session_state.current_idx = res.data[0].get("current_idx", 0)
            st.session_state.wrong_notes = res.data[0].get("wrong_notes", [])
            st.session_state.shuffled_list = res.data[0].get("shuffled_list", [])
            st.session_state.options_dict = res.data[0].get("options_dict", {})
        else:
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
        shuffled = all_idioms.copy()
        random.shuffle(shuffled)
        st.session_state.shuffled_list = shuffled
        st.session_state.options_dict = {item['idiom']: generate_options_for_item(item) for item in all_idioms}
        st.session_state.current_idx = 0
        st.session_state.wrong_notes = []
    
    st.session_state.db_loaded = True

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

# 4. 사이드바 메뉴
st.sidebar.write("---")
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
    st.sidebar.success(f"[{user_id}] 님의 학습 진행도와 문제 순서가 초기화되었습니다.")
    st.rerun()

# 5. 메인 퀴즈 화면
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

st.markdown('<p class="main-title">🏯 사자성어 퀴즈 앱</p>', unsafe_allow_html=True)

if test_target == "오답노트 테스트" and not active_list:
    st.info("🎉 저장된 오답이 없습니다! '전체 문제 테스트'에서 틀린 문제가 생기면 이곳에 자동으로 유지됩니다.")
else:
    if st.session_state.current_idx >= len(active_list):
        st.session_state.current_idx = 0

    current = active_list[st.session_state.current_idx]
    
    st.caption(f"🔑 현재 사용자: **{user_id}** | 모드: **{test_target}** | **{quiz_type}** | 진행: **{st.session_state.current_idx + 1} / {len(active_list)}번째**")
    st.markdown(f'<p class="question-title">문제: {current["meaning"]}</p>', unsafe_allow_html=True)
    st.write("---")

    if quiz_type == "객관식 (4지선다)":
        options = st.session_state.options_dict.get(current['idiom'], generate_options_for_item(current))
        selected_option = st.radio(
            "알맞은 사자성어를 선택하세요:", 
            options, 
            index=None, 
            key=f"radio_{user_id}_{test_target}_{st.session_state.current_idx}"
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

    else:
        user_answer = st.text_input(
            "정답(사자성어)을 입력 후 Enter를 누르세요:", 
            key=f"text_{user_id}_{test_target}_{st.session_state.current_idx}"
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