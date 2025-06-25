# streamlit_lotte_game.py

import streamlit as st
import datetime
import requests
from urllib.parse import urlencode
import pandas as pd
from bs4 import BeautifulSoup



# 오늘 날짜
today = datetime.date.today()
today_str = today.strftime('%Y%m%d')

# 네이버 스포츠의 롯데 자이언츠 경기 일정 URL
lotte_game_url = f"https://sports.news.naver.com/kbaseball/schedule/index.nhn?date={today_str}&teamCode=LT"




st.set_page_config(layout="wide", page_title="롯데 자이언츠 데일리", page_icon="🎯")

st.title(f"🎯 데일리 롯데 ({today.strftime('%m월 %d일')})")


# 2열 구성
# 기존
# col1, col2 = st.columns(2)

# 수정: 7:3 비율로 설정
col1, col2 = st.columns([6.5, 3.5])



def get_kbo_rankings_official_kr():
    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRank.aspx"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.select_one("table.tData")
    if not table:
        raise ValueError("공식 KBO 사이트에서 순위 테이블을 찾을 수 없습니다.")

    df = pd.read_html(str(table))[0]
    df = df.rename(columns={
        "순위": "순위",
        "팀명": "팀",
        "승": "승",
        "패": "패",
        "무": "무",
        "승률": "승률",
        "게임차": "게임차"
    })

    df = df[["순위", "팀", "승", "패", "무", "승률", "게임차"]]
    df = df.reset_index(drop=True)
    return df

def render_kbo_table(df, highlight_team="롯데"):
    table_html = '<table style="border-collapse: collapse; width: 600px;">'  # 여기서 폭 조절
    table_html += '<thead><tr>' + ''.join(
        [f'<th style="border: 1px solid #ddd; padding: 6px; font-size:14px;">{col}</th>' for col in df.columns]
    ) + '</tr></thead><tbody>'

    for _, row in df.iterrows():
        is_lotte = highlight_team in row['팀']
        row_style = 'background-color: rgba(255,0,0,0.2); font-weight: bold;' if is_lotte else ''
        table_html += f'<tr style="{row_style}">'
        for val in row:
            table_html += f'<td style="border: 1px solid #ddd; padding: 6px; font-size:14px; text-align:center;">{val}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table>'
    return table_html


with col1:
    kbo_gamecenter_url2 = "https://sports.daum.net/schedule/kbo"
    # iframe으로 임베드 (주의: 사이트가 X-Frame-Options 정책으로 막혀 있을 수 있음)
    st.components.v1.iframe(src=kbo_gamecenter_url2, width=1142, height=500, scrolling=False)



with col2:
    st.subheader("📊 KBO 리그 현재 순위 (공식 KBO 기준)")
    st.write("")


    try:
        df_rank = get_kbo_rankings_official_kr()
        html_table = render_kbo_table(df_rank, highlight_team="롯데")

        # ✅ 오른쪽 정렬 div 추가
        st.markdown(
            f"""
            <div style="float: right;">
                {html_table}
            </div>
            """,
            unsafe_allow_html=True
        )

        lotte_row = df_rank[df_rank["팀"].str.contains("롯데")]
#        if not lotte_row.empty:
#            st.success(f"🎉 롯데 {lotte_row.iloc[0]['순위']}위? 난 만족 못해!! 가을 야구 마 함 해보입시더")
#        else:
#            st.warning("롯데 자이언츠가 순위표에 없습니다.")
    except Exception as e:
        st.write(f"순위를 불러오는 데 실패했습니다: {e}")
#----------------------------------------------------------------
# 구분선
st.markdown("<hr style='border: 1px solid #ddd; margin: 20px 0;'>", unsafe_allow_html=True)

col3, col4 = st.columns([6.5, 3.5])

from datetime import datetime, timedelta

# 1. 원본 인증키 그대로 넣기 (Decoding 버전!)
service_key = "UXqugk+0AxpQyJqlQtC3Ebew3mFF6rvXVzErFuMm/0g7zMMAndYGFHjkPkcMK1LBSM+wEs8d3hslVgSWeSOoqw=="

# ▶ 공통 설정
nx, ny = 98, 76  # 사직야구장 격자
now = datetime.now()
base_date = now.strftime('%Y%m%d')
base_time_obs = (now - timedelta(minutes=40)).strftime('%H') + "00"
base_time_fcst = now.strftime('%H') + "30"

# ▶ 강수 형태 코드 맵
pty_map = {
    "0": "맑음 ☀️", "1": "비 🌧️", "2": "비/눈 🌨️", "3": "눈 ❄️",
    "4": "소나기 ⛈️", "5": "빗방울 💧", "6": "빗방울/눈날림", "7": "눈날림"
}

# ▶ 실황 API
def get_current_weather():
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "100",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time_obs,
        "nx": nx,
        "ny": ny
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        items = res.json()["response"]["body"]["items"]["item"]
        return {i["category"]: i["obsrValue"] for i in items}
    return {}

# ▶ 예보 API
def get_forecast_weather():
    # ✅ 현재 시각 기준 1시간 전으로 설정 (가장 안정적)
    base_dt = datetime.now() - timedelta(hours=1)
    base_date = base_dt.strftime('%Y%m%d')
    base_time = base_dt.strftime('%H') + "30"  # ex. "1430"

    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {
        "serviceKey": service_key,  # 전역에 있는 인증키
        "pageNo": "1",
        "numOfRows": "100",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": 98,
        "ny": 76
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()  # HTTP 에러 확인
    except requests.exceptions.SSLError as ssl_err:
        st.error(f"SSL 오류 발생: {ssl_err}")
        return {}
    except Exception as e:
        st.error("예외 발생:")
        st.exception(e)
        return {}

with col3:
        st.subheader("📰 롯데 자이언츠 최신 뉴스")

        kbo_gamecenter_url = "https://sports.daum.net/team/kbo/386/news"

        # iframe으로 임베드 (주의: 사이트가 X-Frame-Options 정책으로 막혀 있을 수 있음)
        st.components.v1.iframe(src=kbo_gamecenter_url, width=1147, height=600, scrolling=True)
    

with col4:
    st.subheader("🏟️ 지금 사직 - 날씨 정보")

    current = get_current_weather()
    if current:
        pty_code = current.get("PTY", "0")
        icon = pty_map.get(pty_code, "🌈")
        summary = pty_map.get(pty_code, "정보 없음")

        # 날씨별 배경 이미지 매핑
        weather_images = {
            "0": "https://www.visitbusan.net/uploadImgs/files/cntnts/20200110150216398_oen",  # 맑음
            "1": "https://www.chosun.com/resizer/v2/RC4YQUIO6TPXXIQIIMERBREDVQ.jpg?auth=57cc1bb3781a935c346ac3b827ae4f65575f32c65246d4e66948bba0d71a1eb8&width=616",  # 비
            "2": "https://www.chosun.com/resizer/v2/RC4YQUIO6TPXXIQIIMERBREDVQ.jpg?auth=57cc1bb3781a935c346ac3b827ae4f65575f32c65246d4e66948bba0d71a1eb8&width=616",  # 비/눈
            "3": "https://images.unsplash.com/photo-1608889175119-0c3f8d518b22",  # 눈
            "4": "https://images.unsplash.com/photo-1600147181321-c9d6e5e39d04",  # 소나기
            "5": "data:image/jpeg;base64,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",  # 빗방울
            "6": "https://images.unsplash.com/photo-1519681393784-d120267933ba",  # 빗방울/눈날림
            "7": "https://images.unsplash.com/photo-1516796181133-e5a4f2b08b0b"   # 눈날림
        }
        bg_url = weather_images.get(pty_code, "https://images.unsplash.com/photo-1470137430626-983a37b8ea46")

        # 날씨 카드
        st.markdown(
            f"""
            <div style='
                background-image: url("{bg_url}");
                background-size: cover;
                background-position: center;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 2px 2px 12px rgba(0,0,0,0.2);
                margin-bottom: 20px;
                text-align: center;
                color: white;
            '>
                <h3 style='margin-bottom: 10px; text-shadow: 1px 1px 2px black;'>{icon} 현재 날씨</h3>
                <p style='font-size:20px; text-shadow: 1px 1px 2px black;'>{summary}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 날씨 상세정보
        st.markdown("### 🌡️ 실시간 기상 정보")
        weather_cards = {
            "🌡️ 기온": f"{current.get('T1H', '-')} °C",
            "💧 습도": f"{current.get('REH', '-')} %",
            "🌬️ 풍속": f"{current.get('WSD', '-')} m/s",
            "☔ 1시간 강수량": f"{current.get('RN1', '0')} mm"
        }

        for label, value in weather_cards.items():
            st.markdown(
                f"""
                <div style='
                    background-color: #ffffff;
                    padding: 12px 20px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    border: 1px solid #e0e0e0;
                    font-size: 16px;
                    color: #333;
                '>
                    <strong>{label}</strong> : {value}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.error("❌ 현재 날씨 데이터를 불러오지 못했습니다.")

        # ▶ 경기 진행 확률 계산
    try:
        rain = float(current.get("RN1", 0))
        temp = float(current.get("T1H", 20))
        wind = float(current.get("WSD", 1))

        # 간단한 규칙 기반 확률 계산
        score = 100
        if rain > 10:
            score -= 40
        elif rain > 3:
            score -= 25
        elif rain > 1:
            score -= 10

        if temp < 5 or temp > 33:
            score -= 10
        if wind > 7:
            score -= 10

        # 확률 범위 보정
        score = max(30, min(score, 100))

        # 해설 문구
        if score > 90:
            comment = "야구하기 아주 좋은 날씨! ⚾ 오늘은 몬하면 안된다!"
        elif score > 75:
            comment = "적당한 날씨! 이겨보자 제발"
        elif score > 60:
            comment = "다소 흐리거나 바람이 있으나, 경기에는 큰 영향 없을 듯!"
        elif score > 45:
            comment = "경기 여부가 유동적일 수 있습니다. 우산 준비하세요! ☂️"
        else:
            comment = "우천 취소 가능성 있습니다. 공식 공지를 확인하세요! ⛔"

        # ▶ 출력 카드
        st.markdown(
    f"""
    <div style='
        background-color: #fffbe6;
        border-left: 6px solid #ffc107;
        padding: 10px 14px;
        border-radius: 8px;
        margin-top: 15px;
    '>
        <h5 style='margin: 4px 0 2px 0; font-size: 17px;'>📢 경기 진행 확률: 
            <span style='color: #e25822;'>{score}%</span>
        </h5>
        <p style='font-size: 14px; margin: 2px 0;'>{comment}</p>
    </div>
    """,
    unsafe_allow_html=True
    )

    except Exception as e:
        st.warning("⚠️ 경기 진행 확률 계산에 실패했습니다.")


        
#---------------------------------------------------------------




# 구분선
st.markdown("<hr style='border: 1px solid #ddd; margin: 20px 0;'>", unsafe_allow_html=True)





#lotte_url = f"https://sports.news.naver.com/kbaseball/schedule/index?date={today}&teamCode=LT"

# st.subheader("📅 오늘 롯데 자이언츠 경기 보기")
# st.write("네이버 스포츠에서 오늘 롯데 경기 일정을 확인하세요.")
# st.link_button("▶ 네이버 스포츠 경기 페이지 열기", lotte_url)



#-------------------------------------------------------------------
col5, col6 = st.columns([7.5, 2.4])

with col5:
    st.subheader("🎮 실시간 중계 게임 센터")
    st.write("오늘 경기에 맞추면 실시간 중계를 이곳에서 확인이 가능합니다.")

    kbo_gamecenter_url1 = "https://sports.daum.net/match/80090756"

    # iframe으로 임베드 (주의: 사이트가 X-Frame-Options 정책으로 막혀 있을 수 있음)
    st.components.v1.iframe(src=kbo_gamecenter_url1, width=1250, height=800, scrolling=True)
    

#with col6:
#    from youtubesearchpython import VideosSearch

#    st.subheader("🎬 최근 경기 하이라이트")

#    query = "티빙 롯데 자이언츠 하이라이트"
#    videos_search = VideosSearch(query, limit=2)
#    result = videos_search.result()

#    if result["result"]:
#        for video in result["result"]:
#            video_url = video["link"]
#            video_id = video_url.split("v=")[-1]
#            st.markdown(
#                f"""
#                <iframe width="400" height="225"
#                src="https://www.youtube.com/embed/{video_id}"
#                frameborder="0" allowfullscreen></iframe>
#                """,
#                unsafe_allow_html=True
#            )
#    else:
#        st.warning("하이라이트 영상을 찾을 수 없습니다.")

with col6:
    st.subheader("🎬 롯데 자이언츠 하이라이트")

    # 영상 1
    st.markdown("**1. 롯데 vs 삼성 하이라이트**")
    st.video("https://youtu.be/VToF__mooJs?si=ViJYOvBfV0RTiduD")

    # 영상 2
    st.markdown("**2. 롯데 자이언츠 주간 플레이 모음**")
    st.video("https://youtu.be/zNFLJ5o_Sfg?si=GoCT-3TPuiqStHGP")
    
    lotte_url = f"https://ticket.giantsclub.com/loginForm.do"

    st.subheader("📅 예매하러 가기")
    st.write("오픈 시간: 일반 예매 기준 일주일 전 14시 입니다.")
    st.link_button("▶ 예매 페이지", lotte_url)



st.markdown("<hr style='border: 1px solid #ddd; margin: 20px 0;'>", unsafe_allow_html=True)





from supabase import create_client, Client
import uuid

# Supabase 설정
url = "https://vdltbxhknxhckhakuyin.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkbHRieGhrbnhoY2toYWt1eWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4MzQ3MTgsImV4cCI6MjA2NjQxMDcxOH0.XY07QQtvjjQ2QyR4-FvZGk3yipRs8EGYmHBZ845tUu0"
supabase: Client = create_client(url, key)

# UI
st.title(f"⚾ {today.strftime('%m월 %d일')} 롯데 경기 승부 예측")

col11, col12, col13 = st.columns([2, 2, 6])
with col11:
    nickname = st.text_input("닉네임을 입력하세요")

with col12:
    selected = st.radio("누가 이길까요?", ("롯데", "상대팀"))

if st.button("예측 제출하기"):
    if nickname:
        supabase.table("vote_predictions").insert({
            "id": str(uuid.uuid4()),
            "nickname": nickname,
            "selected_team": selected,
            "vote_date": today.isoformat()
        }).execute()
        st.success(f"{nickname} 님의 예측이 저장되었습니다!")
    else:
        st.warning("닉네임을 입력해주세요.")

# 오늘 날짜의 예측만 집계
res = supabase.table("vote_predictions").select("*").eq("vote_date", today).execute()
votes = pd.DataFrame(res.data)

with col13:
    if not votes.empty:
        count_df = votes["selected_team"].value_counts().reset_index()
        count_df.columns = ["팀", "득표 수"]
        total = count_df["득표 수"].sum()
        count_df["득표율"] = count_df["득표 수"] / total * 100
    
        st.subheader("📊 현재 예측 현황")
        import streamlit.components.v1 as components
    
        team_a = count_df[count_df["팀"] == "롯데"]["득표율"].values[0] if "롯데" in count_df["팀"].values else 0
        team_b = 100 - team_a
    
        html_code = f"""
        <div style="display: flex; height: 40px; width: 100%; border-radius: 8px; overflow: hidden; box-shadow: inset 0 0 5px rgba(0,0,0,0.1);">
            <div style="width: {team_a}%; background-color: #ff4d4d; text-align: center; color: white; line-height: 40px;">
                롯데 {team_a:.1f}%
            </div>
            <div style="width: {team_b}%; background-color: #4da6ff; text-align: center; color: white; line-height: 40px;">
                상대팀 {team_b:.1f}%
            </div>
        </div>
        """
        components.html(html_code, height=50)
    
        st.markdown("### 🧑 예측한 사람 목록")
        for team in count_df["팀"]:
            names = votes[votes["selected_team"] == team]["nickname"].tolist()
            st.markdown(f"**{team}**: {', '.join(names)}")
    else:
        st.info("아직 오늘의 예측이 없습니다. 첫 예측자가 되어보세요!")






# 경기 일정 https://www.giantsclub.com/html/?pcode=257
# 티켓 예매 https://ticket.giantsclub.com/loginForm.do
