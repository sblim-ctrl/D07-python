import random
from datetime import datetime

import streamlit as st

SET_COUNT = 5
NUMBERS_PER_SET = 6
WEEKDAYS = "월화수목금토일"


def ball_color(n: int) -> str:
    # 동행복권 공 색상: 1~10 노랑, 11~20 파랑, 21~30 빨강, 31~40 회색, 41~45 초록
    if n <= 10:
        return "#fbc400"
    if n <= 20:
        return "#69c8f2"
    if n <= 30:
        return "#ff7272"
    if n <= 40:
        return "#aaaaaa"
    return "#b0d840"


def ball_html(n: int) -> str:
    return (
        f'<span style="display:inline-block;width:44px;height:44px;line-height:44px;'
        f"margin:4px;border-radius:50%;text-align:center;font-weight:bold;"
        f'color:#222;background:{ball_color(n)};">{n}</span>'
    )


st.title("🎱 로또 번호 생성기")

if st.button("번호 뽑기", type="primary"):
    now = datetime.now()
    st.write(f"📅 {now:%Y-%m-%d} ({WEEKDAYS[now.weekday()]}) {now:%H:%M:%S}")
    for i in range(SET_COUNT):
        numbers = sorted(random.sample(range(1, 46), NUMBERS_PER_SET))  # 1~45 중복 없이 6개
        balls = "".join(ball_html(n) for n in numbers)
        st.markdown(f"**{'ABCDE'[i]}** {balls}", unsafe_allow_html=True)
