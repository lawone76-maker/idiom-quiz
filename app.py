import os
import random
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="사자성어 퀴즈 앱", page_icon="📖", layout="centered")

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(filename):
    data = []
    if not os.path.exists(filename):
        return [{"word": "샘플성어", "meaning": "파일이 없을 때 표시되는 샘플 뜻입니다."}]

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and ')' in line and ',' in line:
                try:
                    word_part, meaning_part = line.split(',', 1)
                    data.append({
                        "word": word_part.strip(),
                        "meaning": meaning_part.strip()
                    })
                except Exception:
                    continue
    return data if data else [{"word": "데이터 없음", "meaning": "텍스트 형식을 확인해주세요."}]

# --- 세션 상태(변수) 초기화 ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = load_data("Four-Character_Idiom.txt")
if 'wrong_queue' not in st.session_state:
    st.session_state.wrong_queue = []
if 'review_mode' not in st.session_state:
    st.session_state.review_mode = False
if 'total_asked' not in st.session_state:
    st.session_state.total_asked = 0
if 'correct_cnt' not in st.session_state:
    st.session_state.correct_cnt = 0
if 'wrong_cnt' not in st.session_state:
    st.session_state.wrong_cnt = 0
if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'result_msg' not in st.session_state:
    st.session_state.result_msg = ""

# --- 문제 출제 함수 ---
def next_question():
    data = st.session_state.quiz_data
    if not data:
        return

    # 오답 모드 체크
    if st.session_state.review_mode:
        if not st.session_state.wrong_queue:
            st.session_state.review_mode = False
            st.session_state.result_msg = "🎉 모든 오답을 정복했습니다! 전체 학습 모드로 복귀합니다."
            st.session_state.current_q = random.choice(data)
        else:
            st.session_state.current_q = random.choice(st.session_state.wrong_queue)
    else:
        st.session_state.current_q = random.choice(data)

    # 보기 4개 생성
    current_word = st.session_state.current_q['word']
    other_words = [item['word'] for item in data if item['word'] != current_word]
    sample_count = min(3, len(other_words))
    wrong_options = random.sample(other_words, sample_count)
    
    options = wrong_options + [current_word]
    random.shuffle(options)
    st.session_state.options = options

# 최초 실행 시 첫 문제 출제
if st.session_state.current_q is None:
    next_question()

# --- 정답 체크 함수 ---
def check_answer(selected_word):
    st.session_state.total_asked += 1
    current_q = st.session_state.current_q
    
    if selected_word == current_q['word']:
        st.session_state.correct_cnt += 1
        if st.session_state.review_mode and current_q in st.session_state.wrong_queue:
            st.session_state.wrong_queue.remove(current_q)
            st.session_state.result_msg = "⭕ 정답! 오답 보관함에서 삭제되었습니다."
        else:
            st.session_state.result_msg = "⭕ 정답입니다!"
    else:
        st.session_state.wrong_cnt += 1
        if current_q not in st.session_state.wrong_queue:
            st.session_state.wrong_queue.append(current_q)
        st.session_state.result_msg = f"❌ 오답! (정답: {current_q['word']}) -> 오답 보관함 등록"
    
    next_question()

# --- UI 레이아웃 구성 ---
st.title("📖 사자성어 퀴즈 웹 앱")

# 1. 상단 현황판 및 모드 전환
col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.info(f"**풀이:** {st.session_state.total_asked} | **정답:** {st.session_state.correct_cnt} | **오답:** {st.session_state.wrong_cnt}\n\n📦 **오답 보관함:** {len(st.session_state.wrong_queue)}개")

with col2:
    mode_text = "🔥 오답 집중" if st.session_state.review_mode else "📖 전체 학습"
    if st.button(f"모드: {mode_text}", use_container_width=True):
        if not st.session_state.review_mode:
            if not st.session_state.wrong_queue:
                st.warning("오답이 없습니다!")
            else:
                st.session_state.review_mode = True
                st.session_state.result_msg = "🔥 [오답 집중 모드] 맞히면 보관함에서 삭제됩니다!"
        else:
            st.session_state.review_mode = False
            st.session_state.result_msg = "📖 [전체 학습 모드] 전환 완료"
        next_question()
        st.rerun()

# 2. 결과 메시지
if st.session_state.result_msg:
    st.write(st.session_state.result_msg)

st.divider()

# 3. 문제 출력
if st.session_state.current_q:
    prefix = "🔥 [오답] Q. " if st.session_state.review_mode else "Q. "
    st.subheader(f"{prefix}{st.session_state.current_q['meaning']}")

# 4. 보기 버튼 4개 (2x2 grid)
st.write("")
btn_cols = st.columns(2)
for idx, option in enumerate(st.session_state.options):
    with btn_cols[idx % 2]:
        if st.button(option, key=f"btn_{idx}", use_container_width=True):
            check_answer(option)
            st.rerun()