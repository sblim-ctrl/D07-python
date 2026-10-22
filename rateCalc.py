import os
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 의 키를 환경 변수로 불러옴

API = {
    "rate": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 최신 환율 (USD 기준)
}

KST = timezone(timedelta(hours=9))  # 한국 시간 (서머타임 없음)

CURRENCIES = {
    "KRW": "🇰🇷 대한민국 원",
    "USD": "🇺🇸 미국 달러",
    "JPY": "🇯🇵 일본 엔",
    "EUR": "🇪🇺 유로",
    "CNY": "🇨🇳 중국 위안",
    "GBP": "🇬🇧 영국 파운드",
    "AUD": "🇦🇺 호주 달러",
    "CAD": "🇨🇦 캐나다 달러",
    "HKD": "🇭🇰 홍콩 달러",
    "TWD": "🇹🇼 대만 달러",
    "THB": "🇹🇭 태국 바트",
    "VND": "🇻🇳 베트남 동",
}

# 주요 환율 카드: (통화, 단위, 카드 색)
MAIN_RATES = [("USD", 1, "#ff6b6b"), ("JPY", 100, "#feca57"), ("EUR", 1, "#48dbfb"), ("CNY", 1, "#1dd1a1")]

ERROR_MESSAGES = {
    "invalid-key": "환율 키가 틀렸어요. .env의 EXCHANGERATE_API_KEY를 확인해 주세요.",
    "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
    "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
}


@st.cache_data(ttl=3600)  # 1시간 동안은 저장해 둔 결과를 다시 씀 (무료는 한 달 1,500번, 실패는 저장 안 됨)
def get_rates(api_key: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}  # 키는 주소가 아니라 헤더로 보냄
    try:
        res = requests.get(API["rate"], headers=headers, timeout=10)  # 🔌 API 호출
    except requests.RequestException:
        raise RuntimeError("환율 서버에 연결하지 못했어요. 인터넷과 🔌 API 주소를 확인해 주세요.") from None
    try:
        data = res.json()
    except ValueError:
        raise RuntimeError("환율 주소를 찾지 못했어요. 🔌 API 주소를 확인해 주세요.") from None
    if data.get("result") != "success":  # data["result"] = "success" 또는 "error"
        error_type = data.get("error-type")  # data["error-type"] = 실패 이유
        raise RuntimeError(ERROR_MESSAGES.get(error_type, f"환율을 가져오지 못했어요. ({error_type})"))
    return data


def convert(amount: float, src: str, dst: str, rates: dict) -> float:
    return amount / rates[src] * rates[dst]  # 모든 환율이 USD 기준이라 USD를 거쳐서 바꿈


def card(title: str, value: str, background: str) -> str:
    return (
        f'<div style="background:{background};border-radius:16px;padding:16px 20px;margin:8px 0;color:#222;">'
        f'<div style="font-size:0.9rem;">{title}</div>'
        f'<div style="font-size:1.5rem;font-weight:bold;">{value}</div></div>'
    )


st.title("💱 환율 계산기")

api_key = os.getenv("EXCHANGERATE_API_KEY")
if not api_key:
    st.error(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

try:
    data = get_rates(api_key)
except RuntimeError as e:
    st.error(str(e))
    st.stop()

rates = data["conversion_rates"]  # data["conversion_rates"]["KRW"] = 1달러가 몇 원인지 (모든 통화가 USD 기준)

col1, col2, col3 = st.columns(3)
amount = col1.number_input("금액", min_value=0.0, value=100.0, step=10.0)
src = col2.selectbox("바꿀 통화", list(CURRENCIES), index=1, format_func=lambda c: f"{c} · {CURRENCIES[c]}")
dst = col3.selectbox("받을 통화", list(CURRENCIES), index=0, format_func=lambda c: f"{c} · {CURRENCIES[c]}")

result = convert(amount, src, dst, rates)
st.markdown(
    card(f"{amount:,.2f} {src} =", f"{result:,.2f} {dst}", "linear-gradient(135deg, #a18cd1, #fbc2eb)"),
    unsafe_allow_html=True,
)

st.subheader("오늘의 주요 환율")
for col, (code, unit, color) in zip(st.columns(len(MAIN_RATES)), MAIN_RATES):
    col.markdown(card(f"{CURRENCIES[code]} {unit:,} {code}", f"{convert(unit, code, 'KRW', rates):,.2f}원", color), unsafe_allow_html=True)

updated = parsedate_to_datetime(data["time_last_update_utc"]).astimezone(KST)  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
st.caption(f"기준 시각: {updated:%Y-%m-%d %H:%M} (한국 시간) · 무료 플랜은 하루 한 번 갱신돼요")
st.caption("출처: 환율 - ExchangeRate-API")
