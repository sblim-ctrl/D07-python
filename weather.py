import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 의 키를 환경 변수로 불러옴

API = {
    "geo": "https://api.openweathermap.org/geo/1.0/direct",  # 🔌 OpenWeather 지오코딩 (도시 이름 → 위도·경도)
    "weather": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
}

# 검색 가능 목록: 지오코딩으로 찾아지는 이름만 (강릉·목포는 '시'를 붙여야 찾아짐)
CITIES = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "수원", "고양", "용인", "성남", "춘천", "강릉시", "청주", "천안",
    "전주", "목포시", "여수", "포항", "경주", "창원", "진주", "제주", "서귀포",
]

ERROR_MESSAGES = {
    401: "날씨 키가 틀렸거나 아직 켜지지 않았어요(가입 후 최대 2시간).",
    404: "날씨 주소를 찾지 못했어요. 🔌 API 주소를 확인해 주세요.",
    429: "1분에 너무 많이 불렀어요. 잠시 뒤에 다시 열어 주세요.",
}


def call_api(url: str, params: dict) -> dict | list:
    try:
        res = requests.get(url, params=params, timeout=10)  # 🔌 API 호출
    except requests.RequestException:
        # from None: 원래 에러에 키가 든 주소가 있어서 숨김
        raise RuntimeError("OpenWeather 서버에 연결하지 못했어요. 인터넷과 🔌 API 주소를 확인해 주세요.") from None
    if res.status_code != 200:
        raise RuntimeError(ERROR_MESSAGES.get(res.status_code, f"날씨를 가져오지 못했어요. (오류 코드 {res.status_code})"))
    return res.json()


@st.cache_data(ttl=600)  # 10분 동안은 저장해 둔 결과를 다시 씀 (실패는 저장 안 됨)
def get_weather(city: str, api_key: str) -> tuple[str, dict]:
    places = call_api(API["geo"], {"q": city, "limit": 1, "appid": api_key})
    if not places:
        raise RuntimeError(f"'{city}'을(를) 찾지 못했어요. 영어 이름(예: Busan)으로도 해 보세요.")
    place = places[0]
    name = (place.get("local_names") or {}).get("ko", place["name"])  # places[0]["local_names"]["ko"] = 한국어 이름 (없으면 places[0]["name"])
    # places[0]["lat"], places[0]["lon"] = 1번(지오코딩) 응답의 위도·경도 → 2번(날씨) 주소에 그대로 들어감
    params = {"lat": place["lat"], "lon": place["lon"], "appid": api_key, "units": "metric", "lang": "kr"}
    return name, call_api(API["weather"], params)


city = st.sidebar.selectbox(
    "도시",
    CITIES,
    accept_new_options=True,  # 목록에 없는 도시도 입력 후 Enter로 검색
    help="글자를 입력하면 목록이 좁혀져요(자동완성). 목록에 없는 도시는 이름을 입력하고 Enter.",
).strip()
if st.sidebar.button("새로 불러오기"):
    st.cache_data.clear()

api_key = os.getenv("OPENWEATHER_API_KEY")
if not api_key:
    st.error(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()
if not city:
    st.info("왼쪽에 도시 이름을 입력해 주세요.")
    st.stop()

try:
    name, data = get_weather(city, api_key)
except RuntimeError as e:
    st.error(str(e))
    st.stop()

st.title(f"🌤 {name} 지금 날씨")

col1, col2, col3, col4 = st.columns(4)
col1.metric("기온", f"{data['main']['temp']:.1f}°C")  # data["main"]["temp"] = 지금 기온
col2.metric("체감 온도", f"{data['main']['feels_like']:.1f}°C")  # data["main"]["feels_like"] = 체감 온도
col3.metric("습도", f"{data['main']['humidity']}%")  # data["main"]["humidity"] = 습도(%)
col4.metric("날씨", data["weather"][0]["description"])  # data["weather"][0]["description"] = 날씨 설명 (weather는 목록이라 첫 번째 칸)

st.caption("출처: 날씨 - OpenWeather")
