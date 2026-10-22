import os

import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 의 키를 환경 변수로 불러옴

API = {
    "openai": "https://api.openai.com/v1",  # 🔌 OpenAI API (Chat Completions)
}

MODEL = "gpt-4o-mini"

# gpt-4o-mini는 reasoning_effort를 지원하지 않아서, effort는 지시문 + 최대 길이(토큰)로 답변 자세함을 조절
EFFORTS = {
    "낮음": ("핵심만 짧게 답하세요.", 300),
    "보통": ("알맞은 길이로 답하세요.", 800),
    "높음": ("단계별로 자세하고 꼼꼼하게 답하세요.", 2000),
}

ERROR_MESSAGES = {
    401: "OpenAI 키가 틀렸어요. .env의 OPENAI_API_KEY를 확인해 주세요.",
    404: "모델이나 🔌 API 주소를 찾지 못했어요.",
    429: "사용량 한도를 넘었거나 크레딧이 없어요. 잠시 뒤에 다시 하거나 결제 정보를 확인해 주세요.",
}


def error_message(e: openai.APIError) -> str:
    # e.message 는 화면에 쓰지 않음: 키 일부가 들어 있을 수 있음
    if isinstance(e, openai.APIConnectionError):
        return "OpenAI 서버에 연결하지 못했어요. 인터넷과 🔌 API 주소를 확인해 주세요."
    if isinstance(e, openai.APIStatusError):
        return ERROR_MESSAGES.get(e.status_code, f"답변을 받지 못했어요. (오류 코드 {e.status_code})")
    return "답변을 받지 못했어요. 잠시 뒤에 다시 해 주세요."


st.title("💬 챗봇")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role": "user" 또는 "assistant", "content": 내용}]

effort = st.sidebar.select_slider("effort (답변 자세함)", options=list(EFFORTS), value="보통")
temperature = st.sidebar.slider(
    "temperature (창의성)", 0.0, 2.0, 0.7, 0.1, help="낮을수록 매번 비슷한 답, 높을수록 다양한 답"
)
if st.sidebar.button("대화 지우기"):
    st.session_state.messages = []
st.sidebar.caption(f"모델: {MODEL} · 출처: OpenAI")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("메시지를 입력하세요")
if prompt:
    st.chat_message("user").write(prompt)
    history = st.session_state.messages + [{"role": "user", "content": prompt}]
    instruction, max_tokens = EFFORTS[effort]
    client = openai.OpenAI(api_key=api_key, base_url=API["openai"], timeout=30)  # 긴 답변은 10초를 넘기도 해서 30초
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(  # 🔌 API 호출
                model=MODEL,
                messages=[{"role": "system", "content": instruction}] + history,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            answer = st.write_stream(stream)  # 답이 만들어지는 대로 글자를 바로 보여 줌
        except openai.APIError as e:
            st.error(error_message(e))
            st.stop()  # 실패한 질문은 대화 기록에 남기지 않음
    st.session_state.messages = history + [{"role": "assistant", "content": answer}]
