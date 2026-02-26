import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import calendar as cal_mod
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import requests

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="에어비앤비 수익 최적화",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── 한글 폰트 ─────────────────────────────────────────────────────────────────
def set_korean_font():
    system = platform.system()
    if system == "Darwin":
        candidates = ["AppleGothic", "Apple SD Gothic Neo", "Arial Unicode MS"]
    elif system == "Windows":
        candidates = ["Malgun Gothic", "NanumGothic", "Gulim"]
    else:
        candidates = ["NanumGothic", "NanumBarunGothic", "UnDotum"]
    available = [f.name for f in fm.fontManager.ttflist]
    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            plt.rcParams["axes.unicode_minus"] = False
            return font
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
    return "default"

set_korean_font()

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #FFF9F7; }
  .block-container { max-width: 880px !important; padding: 1.5rem 2rem 3rem !important; }
  [data-testid="stSidebar"] { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }

  /* 기본 버튼 */
  .stButton > button {
    background-color: #FF5A5F !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    padding: 12px 28px !important; font-size: 15px !important;
    font-weight: 600 !important; width: 100% !important;
    cursor: pointer !important; transition: background 0.2s !important;
  }
  .stButton > button:hover { background-color: #E8484D !important; }

  /* 뒤로가기 버튼 */
  .back-btn .stButton > button {
    background-color: white !important; color: #484848 !important;
    border: 1.5px solid #DDDDDD !important;
  }
  .back-btn .stButton > button:hover { background-color: #F7F7F7 !important; }

  /* 숙소 종류 버튼 (선택됨) */
  .rt-selected .stButton > button {
    background-color: #FF5A5F !important;
  }
  .rt-unselected .stButton > button {
    background-color: white !important; color: #484848 !important;
    border: 1.5px solid #DDDDDD !important;
  }
  .rt-unselected .stButton > button:hover {
    background-color: #F7F7F7 !important;
  }

  /* 호스트 타입 선택 */
  .host-card-selected .stButton > button {
    background-color: #FF5A5F !important; font-size: 15px !important;
  }
  .host-card-unselected .stButton > button {
    background-color: white !important; color: #484848 !important;
    border: 2px solid #DDDDDD !important; font-size: 15px !important;
  }
  .host-card-unselected .stButton > button:hover {
    border-color: #FF5A5F !important; color: #FF5A5F !important;
    background-color: #FFF0EE !important;
  }

  /* 카드 */
  .card { background: white; border-radius: 14px; padding: 22px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); margin-bottom: 14px; }

  /* 구분선 */
  .section-divider { border: none; border-top: 1.5px solid #F0F0F0; margin: 28px 0; }

  /* 숫자 강조 */
  .big-num { font-size: 30px; font-weight: 700; color: #FF5A5F; }

  /* 감춤 */
  #MainMenu { visibility: hidden; } footer { visibility: hidden; }

  /* 입력 요소 */
  .stSelectbox > div > div,
  .stNumberInput > div > div > input { border-radius: 8px !important; }
  .stCheckbox { margin-bottom: 4px; }

  /* 달력 탐색 버튼 — 작게 */
  .cal-nav .stButton > button {
    padding: 6px 12px !important; font-size: 14px !important;
    min-height: 36px !important; border-radius: 8px !important;
  }

  /* POI 뱃지 */
  .poi-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600; margin-right: 4px;
  }

  /* 네비게이션 버튼 정렬 — back-btn/nav-balance 마크다운 래퍼를 0높이로 */
  div[data-testid="stMarkdownContainer"]:has(.back-btn),
  div[data-testid="stMarkdownContainer"]:has(.nav-balance) {
    height: 0 !important; min-height: 0 !important;
    overflow: hidden !important; margin: 0 !important; padding: 0 !important;
  }

  /* 탭 스타일 */
  .stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: #F5F5F5; border-radius: 12px;
    padding: 4px; border-bottom: none !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; padding: 8px 14px !important;
    font-size: 13px !important; font-weight: 600 !important;
    color: #767676 !important; background: transparent !important;
    border: none !important; white-space: nowrap;
  }
  .stTabs [aria-selected="true"] {
    background: white !important; color: #FF5A5F !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.09) !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding: 20px 0 0 !important; }

  /* 모든 버튼 높이 통일 (네비게이션 정렬) */
  .stButton > button { min-height: 52px !important; }

  /* 히어로 섹션 */
  .hero-section {
    background: linear-gradient(135deg, #FF5A5F 0%, #E8484D 60%, #C62828 100%);
    border-radius: 20px; padding: 40px 28px 36px; text-align: center;
    margin-bottom: 28px; position: relative; overflow: hidden;
  }
</style>
""", unsafe_allow_html=True)

# ── 상수 ─────────────────────────────────────────────────────────────────────
DISTRICT_KR = {
    "Gangnam-gu": "강남구", "Gangdong-gu": "강동구", "Gangbuk-gu": "강북구",
    "Gangseo-gu": "강서구", "Gwanak-gu": "관악구", "Gwangjin-gu": "광진구",
    "Guro-gu": "구로구", "Geumcheon-gu": "금천구", "Nowon-gu": "노원구",
    "Dobong-gu": "도봉구", "Dongdaemun-gu": "동대문구", "Dongjak-gu": "동작구",
    "Mapo-gu": "마포구", "Seodaemun-gu": "서대문구", "Seocho-gu": "서초구",
    "Seongdong-gu": "성동구", "Seongbuk-gu": "성북구", "Songpa-gu": "송파구",
    "Yangcheon-gu": "양천구", "Yeongdeungpo-gu": "영등포구", "Yongsan-gu": "용산구",
    "Eunpyeong-gu": "은평구", "Jongno-gu": "종로구", "Jung-gu": "중구",
    "Jungnang-gu": "중랑구",
}

ROOM_TYPE_KR = {
    "entire_home": "집 전체", "private_room": "개인실",
    "hotel_room": "호텔 객실", "shared_room": "다인실",
}
ROOM_TYPE_DESC = {
    "entire_home": "숙소 전체를 단독으로 사용하는 형태",
    "private_room": "침실은 개인 공간, 거실·주방은 공용",
    "hotel_room": "호텔 스타일 객실",
    "shared_room": "다른 게스트와 공간을 함께 사용",
}
ROOM_TYPE_ICONS = {
    "entire_home": "🏠", "private_room": "🚪",
    "hotel_room": "🏨", "shared_room": "👥",
}

ROOM_STYLES = ["모던/미니멀", "빈티지/레트로", "한옥/전통", "아늑/가정적", "럭셔리/프리미엄"]

POI_TYPE_ICON = {
    "관광지": "🗺️", "문화시설": "🏛️", "쇼핑": "🛍️", "음식점": "🍽️",
    "숙박": "🏨", "레포츠": "⛷️", "여행코스": "🚶", "축제공연행사": "🎭",
}

# 자치구 중심 좌표
DISTRICT_CENTERS = {
    "Dobong-gu":        (37.6576, 127.0405),
    "Dongdaemun-gu":    (37.5829, 127.0474),
    "Dongjak-gu":       (37.5005, 126.9510),
    "Eunpyeong-gu":     (37.6077, 126.9217),
    "Gangbuk-gu":       (37.6339, 127.0234),
    "Gangdong-gu":      (37.5397, 127.1347),
    "Gangnam-gu":       (37.5051, 127.0414),
    "Gangseo-gu":       (37.5551, 126.8359),
    "Geumcheon-gu":     (37.4721, 126.8964),
    "Guro-gu":          (37.4959, 126.8660),
    "Gwanak-gu":        (37.4784, 126.9403),
    "Gwangjin-gu":      (37.5434, 127.0748),
    "Jongno-gu":        (37.5767, 126.9932),
    "Jung-gu":          (37.5621, 126.9916),
    "Jungnang-gu":      (37.5948, 127.0846),
    "Mapo-gu":          (37.5555, 126.9249),
    "Nowon-gu":         (37.6477, 127.0665),
    "Seocho-gu":        (37.4948, 127.0175),
    "Seodaemun-gu":     (37.5632, 126.9356),
    "Seongbuk-gu":      (37.5943, 127.0216),
    "Seongdong-gu":     (37.5519, 127.0434),
    "Songpa-gu":        (37.5065, 127.1065),
    "Yangcheon-gu":     (37.5309, 126.8587),
    "Yeongdeungpo-gu":  (37.5178, 126.9070),
    "Yongsan-gu":       (37.5419, 126.9791),
}

CLUSTER_INFO = {
    "프리미엄 관광거점": {
        "emoji": "🏆", "color": "#FF5A5F", "elasticity": -0.7,
        "desc": "외국인 관광객 수요가 높아 요금을 올려도 예약이 잘 줄지 않는 지역입니다.",
        "strategy": [
            "1박 요금 10~20% 인상 테스트 — 수요가 탄탄합니다",
            "즉시예약 반드시 켜기 — 예약 기회를 놓치지 마세요",
            "사진 20~35장 + 주변 관광지 포함 촬영",
            "영문 설명 최적화 — 외국인 게스트 유입",
            "슈퍼호스트 달성 후 요금 프리미엄 적용",
        ],
    },
    "성장형 주거상권": {
        "emoji": "📈", "color": "#00A699", "elasticity": -0.8,
        "desc": "안정적인 수요와 높은 수익을 보이는 프리미엄 주거·상업 복합 지역입니다.",
        "strategy": [
            "현재 요금 수준 방어 — 불필요한 가격 인하 자제",
            "슈퍼호스트 + 게스트 선호 배지 달성 목표",
            "평점 4.8 이상 유지 — 리뷰 관리에 집중",
            "집 전체 형태 전환 검토 — 개인실 대비 수익 2.7배",
            "관광지·문화시설 근접성을 제목에 명시",
        ],
    },
    "중가 균형시장": {
        "emoji": "⚖️", "color": "#FFB400", "elasticity": -1.1,
        "desc": "공급과 수요가 균형을 이루는 안정적인 시장입니다. 운영 최적화가 핵심입니다.",
        "strategy": [
            "사진 20~35장 등록 — 클릭률 높이기가 1순위",
            "최소 숙박 2~3박 — 리뷰를 빠르게 쌓는 전략",
            "즉시예약 켜기 — 비용 없이 예약률 높이기",
            "추가 게스트 요금 없애고 1박 요금에 통합",
            "슈퍼호스트 달성 후 요금 소폭 인상",
        ],
    },
    "가격민감 외곽형": {
        "emoji": "🛡️", "color": "#9C27B0", "elasticity": -1.5,
        "desc": "가격 경쟁이 치열한 지역입니다. 예약률 유지가 최우선 전략입니다.",
        "strategy": [
            "요금 인상 자제 — 예약률 방어가 수익 보호",
            "사진 수 늘려 클릭률 개선",
            "슈퍼호스트 배지로 가격 외 차별화",
            "최소 숙박일 줄이기 — 예약 가능한 날 늘리기",
            "추가 요금 없애 선택 유인 강화",
        ],
    },
}

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/raw/seoul_airbnb_cleaned.csv")
    cluster_df = pd.read_csv("data/processed/district_clustered.csv")
    df = df.merge(
        cluster_df[["district", "cluster", "cluster_name"]],
        on="district", how="left",
    )
    return df, cluster_df

@st.cache_data
def build_poi_db():
    """데이터셋에서 유니크 POI 목록 추출"""
    df = pd.read_csv("data/raw/seoul_airbnb_cleaned.csv")
    cols = ["nearest_poi_name", "nearest_poi_addr", "nearest_poi_type_name",
            "nearest_poi_lat", "nearest_poi_lng"]
    poi_df = df[cols].dropna(subset=["nearest_poi_name", "nearest_poi_lat", "nearest_poi_lng"])
    poi_df = poi_df.drop_duplicates(subset=["nearest_poi_name"]).reset_index(drop=True)
    return poi_df

df, cluster_df = load_data()
active_df = df[
    (df["refined_status"] == "Active") & (df["operation_status"] == "Operating")
].copy()
poi_db = build_poi_db()

# ── 헬퍼 함수 ────────────────────────────────────────────────────────────────
def get_bench(district, room_type):
    return active_df[
        (active_df["district"] == district) &
        (active_df["room_type"] == room_type)
    ]

def bench_val(bench, col, default, pct=50):
    if len(bench) > 0 and col in bench.columns:
        vals = bench[col].dropna()
        if len(vals) > 0:
            return float(np.percentile(vals, pct))
    return default

def dn(district):
    return DISTRICT_KR.get(district, district)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def geocode_address(address: str):
    """Nominatim 지오코딩 — (lat, lng, display_name) 반환, 실패 시 (None, None, None)"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{address} 서울 대한민국", "format": "json", "limit": 1}
        headers = {"User-Agent": "SeoulAirbnbDashboard/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=6)
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        pass
    return None, None, None

def find_nearby_pois(lat, lng, max_km=2.0):
    """반경 max_km 내 POI 목록 반환 (거리 순 정렬)"""
    results = []
    for _, row in poi_db.iterrows():
        dist = haversine_km(lat, lng, row["nearest_poi_lat"], row["nearest_poi_lng"])
        if dist <= max_km:
            results.append({
                "name": row["nearest_poi_name"],
                "type": row["nearest_poi_type_name"] if pd.notna(row["nearest_poi_type_name"]) else "기타",
                "dist_km": dist,
                "dist_m": int(dist * 1000),
                "addr": row["nearest_poi_addr"] if pd.notna(row.get("nearest_poi_addr")) else "",
            })
    results.sort(key=lambda x: x["dist_km"])
    return results

# ── session_state 초기화 ──────────────────────────────────────────────────────
def init_state():
    now = datetime.now()
    defaults = {
        # 공통
        "step": 1,
        "host_type": None,          # "new" | "existing"
        "district": "Mapo-gu",
        "room_type": "entire_home",
        # 요금
        "my_adr": None,
        "my_occ_pct": None,
        "weekday_occ_pct": 0,
        "weekend_occ_pct": 0,
        # 운영비
        "opex_elec": 80000, "opex_water": 30000, "opex_mgmt": 150000,
        "opex_net": 30000, "opex_clean": 200000, "opex_loan": 0, "opex_etc": 50000,
        # 운영 체크 (기존 호스터)
        "my_photos": None, "my_superhost": False, "my_instant": False,
        "my_extra_fee": False, "my_min_nights": None,
        "my_rating": None, "my_reviews": None,
        # 신규 호스터 숙소 정보
        "my_guests": None, "my_bedrooms": None, "my_baths_count": None,
        "my_beds": None, "my_room_style": "모던/미니멀",
        # 달력 (기존 호스터)
        "calendar_year": now.year, "calendar_month": now.month,
        "booked_days": set(),        # 현재 월 선택된 날
        # 위치
        "my_address": "",
        "my_lat": None, "my_lng": None, "my_location_name": "",
        "location_confirmed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── 공통 UI 컴포넌트 ─────────────────────────────────────────────────────────
def render_logo():
    st.markdown("""
    <div style="text-align:center;padding:20px 0 4px;">
      <div style="font-size:34px;">🏠</div>
      <h2 style="color:#FF5A5F;margin:6px 0 2px;font-weight:800;letter-spacing:-0.5px;">
        에어비앤비 수익 최적화
      </h2>
      <p style="color:#888;font-size:13px;margin:0;">
        서울 실운영 숙소 14,399개 데이터 기반 · 내 숙소 맞춤 분석
      </p>
    </div>
    """, unsafe_allow_html=True)

def render_hero():
    st.markdown("""
    <div style="
      background: linear-gradient(135deg, #FF5A5F 0%, #E8484D 55%, #C62828 100%);
      border-radius: 22px; padding: 52px 28px 48px; text-align: center;
      margin-bottom: 28px; position: relative; overflow: hidden;
    ">
      <!-- 장식 원 -->
      <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;
        background:rgba(255,255,255,0.07);border-radius:50%;pointer-events:none;"></div>
      <div style="position:absolute;bottom:-50px;left:-50px;width:200px;height:200px;
        background:rgba(255,255,255,0.05);border-radius:50%;pointer-events:none;"></div>
      <div style="position:absolute;top:20px;left:30px;width:60px;height:60px;
        background:rgba(255,255,255,0.06);border-radius:50%;pointer-events:none;"></div>
      <div style="position:relative;z-index:1;">
        <div style="font-size:52px;margin-bottom:14px;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.2));">🏠</div>
        <h1 style="color:white;font-size:32px;font-weight:900;margin:0 0 14px;
          line-height:1.2;letter-spacing:-1px;text-shadow:0 2px 12px rgba(0,0,0,0.2);">
          에어비앤비 최적화 플래너
        </h1>
        <p style="color:rgba(255,255,255,0.85);font-size:14px;margin:0;
          text-shadow:0 1px 4px rgba(0,0,0,0.1);letter-spacing:0.2px;">
          내 숙소에 딱 맞는 수익 전략을 3분 만에 찾아드립니다
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_progress(current_step):
    host_type = st.session_state.get("host_type", "existing")
    if host_type == "new":
        labels = ["숙소 정보", "숙소 설정", "월 운영비", "분석 결과"]
        step_to_pos = {1: 1, 2: 2, 3: 3, 5: 4}
    else:
        labels = ["숙소 정보", "요금 현황", "월 운영비", "운영 체크"]
        step_to_pos = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}

    current = step_to_pos.get(current_step, current_step)
    total = len(labels)

    html = '<div style="display:flex;align-items:flex-start;justify-content:center;gap:0;margin:18px 0 28px;">'
    for i, label in enumerate(labels, 1):
        if i < current:
            circle_bg, circle_color, line_color = "#FF5A5F", "white", "#FF5A5F"
            circle_content = "✓"
        elif i == current:
            circle_bg, circle_color, line_color = "#FF5A5F", "white", "#EBEBEB"
            circle_content = str(i)
        else:
            circle_bg, circle_color, line_color = "#EBEBEB", "#AAAAAA", "#EBEBEB"
            circle_content = str(i)

        label_color = "#FF5A5F" if i == current else ("#484848" if i < current else "#AAAAAA")
        lw = "600" if i == current else "400"
        left_line = "transparent" if i == 1 else line_color
        right_line = "transparent" if i == total else "#EBEBEB"

        html += '<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
        html += (
            f'<div style="display:flex;align-items:center;width:100%;">'
            f'<div style="flex:1;height:2px;background:{left_line};"></div>'
            f'<div style="width:32px;height:32px;border-radius:50%;background:{circle_bg};'
            f'color:{circle_color};display:flex;align-items:center;justify-content:center;'
            f'font-size:13px;font-weight:700;flex-shrink:0;">{circle_content}</div>'
            f'<div style="flex:1;height:2px;background:{right_line};"></div>'
            f'</div>'
        )
        html += f'<div style="font-size:11px;color:{label_color};margin-top:5px;font-weight:{lw};">{label}</div>'
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def coral_box(content):
    st.markdown(
        f'<div style="background:#FFF0EE;border-radius:10px;padding:16px 20px;margin-top:8px;">{content}</div>',
        unsafe_allow_html=True,
    )

def info_row(label, value, value_color="#484848"):
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F5F5F5;">'
        f'<span style="color:#767676;font-size:14px;">{label}</span>'
        f'<span style="font-weight:600;color:{value_color};font-size:14px;">{value}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

def section_title(title, subtitle=""):
    sub = f'<p style="color:#888;font-size:13px;margin:4px 0 16px;">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<h3 style="color:#484848;margin:0 0 4px;font-weight:700;">{title}</h3>{sub}', unsafe_allow_html=True)

# ── 달력 컴포넌트 ─────────────────────────────────────────────────────────────
def render_calendar():
    """인터랙티브 달력: 예약된 날짜 클릭 선택 → 예약률 반환"""
    year = st.session_state.calendar_year
    month = st.session_state.calendar_month
    days_in_month = cal_mod.monthrange(year, month)[1]
    booked = st.session_state.booked_days  # set of ints

    # ── 월 탐색 ──────────────────────────────────────────────────────────────
    cn1, cn2, cn3 = st.columns([1, 4, 1])
    with cn1:
        st.markdown('<div class="cal-nav">', unsafe_allow_html=True)
        if st.button("◀", key="cal_prev"):
            if month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year = year - 1
            else:
                st.session_state.calendar_month -= 1
            st.session_state.booked_days = set()  # 월 바뀌면 초기화
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with cn2:
        st.markdown(
            f'<div style="text-align:center;font-size:16px;font-weight:700;padding:6px 0;">'
            f'{year}년 {month}월</div>',
            unsafe_allow_html=True,
        )
    with cn3:
        st.markdown('<div class="cal-nav">', unsafe_allow_html=True)
        if st.button("▶", key="cal_next"):
            if month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year = year + 1
            else:
                st.session_state.calendar_month += 1
            st.session_state.booked_days = set()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 요일 헤더 HTML ────────────────────────────────────────────────────────
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    header_html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:4px;">'
    for i, d in enumerate(day_names):
        color = "#FF5A5F" if i >= 5 else "#484848"
        header_html += (
            f'<div style="text-align:center;font-size:12px;font-weight:700;'
            f'color:{color};padding:4px 0;">{d}</div>'
        )
    header_html += "</div>"
    st.markdown(header_html, unsafe_allow_html=True)

    # ── 달력 HTML (시각 표시) + 버튼 클릭 ────────────────────────────────────
    month_cal = cal_mod.monthcalendar(year, month)
    for week in month_cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(
                    '<div style="height:38px;"></div>', unsafe_allow_html=True
                )
            else:
                is_booked = day in booked
                if is_booked:
                    bg, fc, fw = "#FF5A5F", "white", "700"
                    label = f"✓{day}"
                else:
                    bg, fc, fw = "#F7F7F7", "#484848", "400"
                    label = str(day)

                cols[i].markdown(
                    f'<div style="background:{bg};color:{fc};font-weight:{fw};'
                    f'border-radius:8px;text-align:center;font-size:13px;'
                    f'padding:2px;margin-bottom:2px;">&nbsp;</div>',
                    unsafe_allow_html=True,
                )
                if cols[i].button(label, key=f"cal_{year}_{month}_{day}", use_container_width=True):
                    if day in booked:
                        st.session_state.booked_days.discard(day)
                    else:
                        st.session_state.booked_days.add(day)
                    st.rerun()

    booked_count = len(booked)
    occ_rate = booked_count / days_in_month if days_in_month > 0 else 0

    # 평일 / 주말 분리 (월~금=평일, 토~일=주말)
    weekdays_total = weekends_total = weekdays_booked = weekends_booked = 0
    for d in range(1, days_in_month + 1):
        dow = datetime(year, month, d).weekday()  # 0=Mon..4=Fri, 5=Sat, 6=Sun
        if dow >= 5:
            weekends_total += 1
            if d in booked:
                weekends_booked += 1
        else:
            weekdays_total += 1
            if d in booked:
                weekdays_booked += 1

    weekday_occ = weekdays_booked / weekdays_total if weekdays_total > 0 else 0
    weekend_occ = weekends_booked / weekends_total if weekends_total > 0 else 0

    return (occ_rate, booked_count, days_in_month,
            weekday_occ, weekend_occ,
            weekdays_booked, weekdays_total,
            weekends_booked, weekends_total)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — 숙소 기본 정보 + 호스터 유형 선택
# ─────────────────────────────────────────────────────────────────────────────
def step1():
    render_hero()
    render_progress(1)
    section_title("1단계: 내 숙소 기본 정보", "숙소 위치, 종류, 그리고 호스팅 경험을 선택해주세요.")

    # ── 자치구 + 숙소 종류 ────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            '<div style="font-weight:600;font-size:14px;margin-bottom:6px;">📍 자치구</div>',
            unsafe_allow_html=True,
        )
        districts = sorted(df["district"].dropna().unique())
        options_kr = [DISTRICT_KR.get(d, d) for d in districts]
        default_idx = districts.index("Mapo-gu") if "Mapo-gu" in districts else 0
        sel_kr = st.selectbox("자치구 선택", options_kr, index=default_idx, label_visibility="collapsed")
        st.session_state.district = districts[options_kr.index(sel_kr)]

        bench = get_bench(st.session_state.district, st.session_state.room_type)
        if len(bench) > 0:
            med = bench_val(bench, "ttm_revpar", 40000)
            coral_box(
                f'<span style="font-size:12px;color:#888;">이 지역 실운영 숙소 평균 하루 수익</span><br>'
                f'<span style="font-size:22px;font-weight:700;color:#FF5A5F;">₩{int(med):,}</span>'
                f'<span style="font-size:12px;color:#888;"> / 박 ({len(bench):,}개)</span>'
            )

    with col2:
        st.markdown(
            '<div style="font-weight:600;font-size:14px;margin-bottom:6px;">🏠 숙소 종류</div>',
            unsafe_allow_html=True,
        )
        room_types = ["entire_home", "private_room", "hotel_room", "shared_room"]
        for rt in room_types:
            selected = st.session_state.room_type == rt
            css_class = "rt-selected" if selected else "rt-unselected"
            icon = ROOM_TYPE_ICONS.get(rt, "")
            check = "✓ " if selected else ""
            label = f"{check}{icon} {ROOM_TYPE_KR.get(rt, rt)}"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"rt_{rt}", use_container_width=True):
                st.session_state.room_type = rt
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── 호스터 유형 선택 ──────────────────────────────────────────────────────
    st.markdown('<hr style="border:none;border-top:1.5px solid #F0F0F0;margin:24px 0 20px;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-weight:700;font-size:16px;color:#484848;margin-bottom:6px;">나는 어떤 호스터인가요?</div>'
        '<div style="font-size:13px;color:#888;margin-bottom:16px;">호스팅 경험에 따라 최적화된 분석 과정이 제공됩니다.</div>',
        unsafe_allow_html=True,
    )

    ht = st.session_state.host_type
    hc1, hc2 = st.columns(2)

    with hc1:
        sel_new = ht == "new"
        css = "host-card-selected" if sel_new else "host-card-unselected"
        st.markdown(
            f'<div style="background:{"#FFF0EE" if sel_new else "white"};'
            f'border:2px solid {"#FF5A5F" if sel_new else "#DDDDDD"};'
            f'border-radius:14px;padding:20px;text-align:center;margin-bottom:8px;">'
            f'<div style="font-size:36px;margin-bottom:8px;">🌱</div>'
            f'<div style="font-weight:700;font-size:16px;color:{"#FF5A5F" if sel_new else "#484848"};">신규 호스터</div>'
            f'<div style="font-size:12px;color:#888;margin-top:6px;">처음으로 숙소를 등록하거나<br>아직 예약 이력이 없어요</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        if st.button("신규 호스터로 시작" + (" ✓" if sel_new else ""), key="ht_new", use_container_width=True):
            st.session_state.host_type = "new"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with hc2:
        sel_ex = ht == "existing"
        css = "host-card-selected" if sel_ex else "host-card-unselected"
        st.markdown(
            f'<div style="background:{"#FFF0EE" if sel_ex else "white"};'
            f'border:2px solid {"#FF5A5F" if sel_ex else "#DDDDDD"};'
            f'border-radius:14px;padding:20px;text-align:center;margin-bottom:8px;">'
            f'<div style="font-size:36px;margin-bottom:8px;">🏅</div>'
            f'<div style="font-weight:700;font-size:16px;color:{"#FF5A5F" if sel_ex else "#484848"};">기존 호스터</div>'
            f'<div style="font-size:12px;color:#888;margin-top:6px;">이미 에어비앤비를 운영 중이고<br>예약 이력이 있어요</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        if st.button("기존 호스터로 시작" + (" ✓" if sel_ex else ""), key="ht_existing", use_container_width=True):
            st.session_state.host_type = "existing"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 피처 하이라이트 ──────────────────────────────────────────────────────
    st.markdown('<hr style="border:none;border-top:1.5px solid #F0F0F0;margin:24px 0 20px;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">
      <div style="background:white;border-radius:14px;padding:16px 12px;text-align:center;
        box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1.5px solid #FFF0EE;">
        <div style="font-size:28px;margin-bottom:6px;">📊</div>
        <div style="font-weight:700;font-size:12px;color:#484848;margin-bottom:4px;">수익 분석</div>
        <div style="font-size:10px;color:#888;">손익 + RevPAR 비교</div>
      </div>
      <div style="background:white;border-radius:14px;padding:16px 12px;text-align:center;
        box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1.5px solid #FFF0EE;">
        <div style="font-size:28px;margin-bottom:6px;">💡</div>
        <div style="font-weight:700;font-size:12px;color:#484848;margin-bottom:4px;">요금 추천</div>
        <div style="font-size:10px;color:#888;">단계별 적정 요금</div>
      </div>
      <div style="background:white;border-radius:14px;padding:16px 12px;text-align:center;
        box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1.5px solid #FFF0EE;">
        <div style="font-size:28px;margin-bottom:6px;">🗺️</div>
        <div style="font-weight:700;font-size:12px;color:#484848;margin-bottom:4px;">위치 분석</div>
        <div style="font-size:10px;color:#888;">2km 내 관광지 분석</div>
      </div>
      <div style="background:white;border-radius:14px;padding:16px 12px;text-align:center;
        box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1.5px solid #FFF0EE;">
        <div style="font-size:28px;margin-bottom:6px;">🏙️</div>
        <div style="font-weight:700;font-size:12px;color:#484848;margin-bottom:4px;">시장 진단</div>
        <div style="font-size:10px;color:#888;">자치구 군집 전략</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if ht is None:
        st.info("위에서 호스터 유형을 선택해야 다음 단계로 넘어갈 수 있습니다.")
    else:
        if st.button("다음 단계 →", key="next1", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    st.markdown("""
    <div style="text-align:center;margin-top:20px;padding:12px;background:#F7F7F7;border-radius:12px;">
      <span style="font-size:11px;color:#AAA;">
        🔒 입력하신 정보는 저장되지 않습니다 &nbsp;·&nbsp;
        📅 데이터 기간: 2024-10 ~ 2025-09 &nbsp;·&nbsp;
        🏠 32,061개 리스팅 기반
      </span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2-NEW — 신규 호스터: 숙소 상세 설정
# ─────────────────────────────────────────────────────────────────────────────
def step2_new():
    render_logo()
    render_progress(2)
    section_title(
        "2단계: 내 숙소 설정",
        "요금·사진·수용 인원·주소를 입력해주세요. 지역 평균과 비교하여 추천 요금을 안내합니다.",
    )

    bench = get_bench(st.session_state.district, st.session_state.room_type)
    b_adr = bench_val(bench, "ttm_avg_rate", 100000)
    b_adr_p25 = bench_val(bench, "ttm_avg_rate", 70000, 25)
    d_name = dn(st.session_state.district)
    rt_name = ROOM_TYPE_KR.get(st.session_state.room_type, "")

    st.markdown(
        f'<div style="background:#F7F7F7;border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
        f'<span style="font-size:13px;font-weight:600;color:#484848;">📊 {d_name} {rt_name} — 지역 참고값</span><br>'
        f'<span style="font-size:13px;color:#767676;">'
        f'평균 1박 요금 <b>₩{int(b_adr):,}</b> &nbsp;|&nbsp; 하위 25% <b>₩{int(b_adr_p25):,}</b>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ── 요금 & 사진 수 ────────────────────────────────────────────────────────
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        default_adr = int(st.session_state.my_adr) if st.session_state.my_adr else int(b_adr_p25)
        my_adr = st.number_input(
            "💰 예정 1박 요금 (원)",
            min_value=0, max_value=2_000_000,
            value=default_adr, step=5_000,
            help="처음에는 지역 하위 25% 요금으로 리뷰를 빠르게 쌓는 걸 권장합니다",
        )
        st.session_state.my_adr = my_adr

    with r1c2:
        default_ph = int(st.session_state.my_photos) if st.session_state.my_photos else 0
        my_photos = st.number_input(
            "📸 등록 예정 사진 수 (장)",
            min_value=0, max_value=300, value=default_ph,
            help="최적 구간은 20~35장입니다",
        )
        st.session_state.my_photos = my_photos

    # ── 수용 인원 / 침대 / 욕실 / 방 스타일 ──────────────────────────────────
    st.markdown(
        '<div style="font-weight:700;font-size:14px;color:#484848;margin:16px 0 10px;">🛏️ 숙소 구성</div>',
        unsafe_allow_html=True,
    )
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)

    with r2c1:
        default_g = int(st.session_state.my_guests) if st.session_state.my_guests else int(bench_val(bench, "guests", 2))
        my_guests = st.number_input("👥 최대 숙박 인원", 1, 20, default_g)
        st.session_state.my_guests = my_guests

    with r2c2:
        default_br = int(st.session_state.my_bedrooms) if st.session_state.my_bedrooms else int(bench_val(bench, "bedrooms", 1))
        my_bedrooms = st.number_input("🛏️ 침실 수", 0, 20, default_br)
        st.session_state.my_bedrooms = my_bedrooms

    with r2c3:
        default_bt = int(st.session_state.my_baths_count) if st.session_state.my_baths_count else int(bench_val(bench, "baths", 1))
        my_baths = st.number_input("🚿 욕실 수", 0, 10, default_bt)
        st.session_state.my_baths_count = my_baths

    with r2c4:
        beds_default = int(st.session_state.my_beds) if st.session_state.my_beds else max(1, int(bench_val(bench, "beds", 1)))
        my_beds = st.number_input("🛌 침대 수", 0, 20, beds_default)
        st.session_state.my_beds = my_beds

    # ── 방 스타일 ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-weight:700;font-size:14px;color:#484848;margin:16px 0 8px;">🎨 인테리어 스타일</div>',
        unsafe_allow_html=True,
    )
    style_cols = st.columns(len(ROOM_STYLES))
    for i, style in enumerate(ROOM_STYLES):
        is_sel = st.session_state.my_room_style == style
        style_cols[i].markdown(
            f'<div style="text-align:center;padding:8px 4px;border-radius:10px;cursor:pointer;'
            f'background:{"#FFF0EE" if is_sel else "#F7F7F7"};'
            f'border:2px solid {"#FF5A5F" if is_sel else "transparent"};">'
            f'<div style="font-size:11px;font-weight:{"700" if is_sel else "400"};'
            f'color:{"#FF5A5F" if is_sel else "#484848"};">{style}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if style_cols[i].button("선택" if not is_sel else "✓", key=f"style_{i}", use_container_width=True):
            st.session_state.my_room_style = style
            st.rerun()

    # ── 숙소 주소 입력 ────────────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #F0F0F0;margin:20px 0 16px;">', unsafe_allow_html=True
    )
    st.markdown(
        '<div style="font-weight:700;font-size:14px;color:#484848;margin-bottom:6px;">📍 숙소 주소</div>'
        '<div style="font-size:12px;color:#888;margin-bottom:10px;">'
        '주변 관광지 분석에 사용됩니다. 동 이름까지 입력하면 더 정확합니다.</div>',
        unsafe_allow_html=True,
    )
    addr_col, btn_col = st.columns([4, 1])
    with addr_col:
        my_address = st.text_input(
            "주소 입력",
            value=st.session_state.my_address,
            placeholder="예) 마포구 서교동, 홍대입구역, 연남동 245-3",
            label_visibility="collapsed",
        )
        st.session_state.my_address = my_address
    with btn_col:
        if st.button("📍 확인", key="geocode_btn_new"):
            if my_address.strip():
                with st.spinner("위치 확인 중..."):
                    lat, lng, disp = geocode_address(my_address)
                if lat:
                    st.session_state.my_lat = lat
                    st.session_state.my_lng = lng
                    st.session_state.my_location_name = disp
                    st.session_state.location_confirmed = True
                    st.rerun()
                else:
                    # 자치구 중심으로 대체
                    dc = DISTRICT_CENTERS.get(st.session_state.district)
                    if dc:
                        st.session_state.my_lat, st.session_state.my_lng = dc
                        st.session_state.my_location_name = dn(st.session_state.district) + " (자치구 평균)"
                        st.session_state.location_confirmed = True
                    st.warning("정확한 주소를 찾지 못했습니다. 자치구 중심으로 분석합니다.")
                    st.rerun()
            else:
                st.warning("주소를 입력해주세요.")

    if st.session_state.location_confirmed and st.session_state.my_lat:
        st.success(f"📍 위치 확인됨: {st.session_state.my_location_name}")
    else:
        # 자동으로 자치구 중심 좌표 사용
        if not st.session_state.my_lat:
            dc = DISTRICT_CENTERS.get(st.session_state.district)
            if dc:
                st.session_state.my_lat, st.session_state.my_lng = dc
                st.session_state.my_location_name = dn(st.session_state.district) + " (자치구 평균)"
        st.info("주소를 입력하고 [📍 확인]을 누르면 더 정확한 주변 관광지 분석이 가능합니다.")

    # ── 네비게이션 ───────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back2n", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with nc2:
        st.markdown('<div class="nav-balance"></div>', unsafe_allow_html=True)
        if st.button("다음 단계 →", key="next2n", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2-EXISTING — 기존 호스터: 요금 + 달력 예약률
# ─────────────────────────────────────────────────────────────────────────────
def step2_existing():
    render_logo()
    render_progress(2)
    section_title(
        "2단계: 요금 & 예약 현황",
        "현재 1박 요금을 입력하고, 지난 달 예약된 날짜를 달력에서 클릭해 선택하세요.",
    )

    bench = get_bench(st.session_state.district, st.session_state.room_type)
    b_adr = bench_val(bench, "ttm_avg_rate", 100000)
    b_occ = bench_val(bench, "ttm_occupancy", 0.40)
    d_name = dn(st.session_state.district)
    rt_name = ROOM_TYPE_KR.get(st.session_state.room_type, "")

    st.markdown(
        f'<div style="background:#F7F7F7;border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
        f'<span style="font-size:13px;font-weight:600;color:#484848;">📊 {d_name} {rt_name} — 지역 평균</span><br>'
        f'<span style="font-size:13px;color:#767676;">'
        f'평균 1박 요금 <b>₩{int(b_adr):,}</b> &nbsp;|&nbsp; 평균 예약률 <b>{b_occ:.0%}</b>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ── 1박 요금 ─────────────────────────────────────────────────────────────
    default_adr = int(st.session_state.my_adr) if st.session_state.my_adr else int(b_adr)
    my_adr = st.number_input(
        "💰 현재 1박 요금 (원)",
        min_value=0, max_value=2_000_000,
        value=default_adr, step=5_000,
        help="에어비앤비에 설정한 기본 1박 요금",
    )
    st.session_state.my_adr = my_adr

    # ── 달력 예약률 ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-weight:700;font-size:14px;color:#484848;margin:20px 0 6px;">📅 예약된 날짜 선택</div>'
        '<div style="font-size:12px;color:#888;margin-bottom:12px;">'
        '예약이 완료된 날짜를 클릭하세요. 빨간 날짜 = 예약됨 / 회색 = 비어있음</div>',
        unsafe_allow_html=True,
    )

    (occ_rate, booked_count, days_in_month,
     weekday_occ, weekend_occ,
     wd_booked, wd_total,
     we_booked, we_total) = render_calendar()
    st.session_state.my_occ_pct = int(occ_rate * 100)
    st.session_state.weekday_occ_pct = int(weekday_occ * 100)
    st.session_state.weekend_occ_pct = int(weekend_occ * 100)

    # 예약률 요약 — 평일 / 주말 분리
    my_revpar = my_adr * occ_rate
    wd_color = "#484848" if weekday_occ <= weekend_occ else "#FF5A5F"
    we_color = "#FF5A5F" if weekend_occ >= weekday_occ else "#E8484D"
    coral_box(
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;align-items:center;text-align:center;">'
        f'<div>'
        f'<div style="font-size:11px;color:#888;margin-bottom:4px;">예약일 / 총 일수</div>'
        f'<div style="font-size:18px;font-weight:700;color:#FF5A5F;">{booked_count}일 / {days_in_month}일</div>'
        f'</div>'
        f'<div style="border-left:1.5px solid #FFD0CF;padding-left:8px;">'
        f'<div style="font-size:11px;color:#888;margin-bottom:4px;">📅 평일 예약률</div>'
        f'<div style="font-size:20px;font-weight:700;color:{wd_color};">{weekday_occ:.0%}</div>'
        f'<div style="font-size:10px;color:#AAA;">{wd_booked}/{wd_total}일</div>'
        f'</div>'
        f'<div style="border-left:1.5px solid #FFD0CF;padding-left:8px;">'
        f'<div style="font-size:11px;color:#888;margin-bottom:4px;">🎉 주말 예약률</div>'
        f'<div style="font-size:20px;font-weight:700;color:{we_color};">{weekend_occ:.0%}</div>'
        f'<div style="font-size:10px;color:#AAA;">{we_booked}/{we_total}일</div>'
        f'</div>'
        f'<div style="border-left:1.5px solid #FFD0CF;padding-left:8px;">'
        f'<div style="font-size:11px;color:#888;margin-bottom:4px;">하루 평균 실수익</div>'
        f'<div style="font-size:18px;font-weight:700;color:#FF5A5F;">₩{int(my_revpar):,}</div>'
        f'</div>'
        f'</div>'
    )

    # ── 네비게이션 ───────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back2e", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with nc2:
        st.markdown('<div class="nav-balance"></div>', unsafe_allow_html=True)
        if st.button("다음 단계 →", key="next2e", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — 월 운영비 (공통)
# ─────────────────────────────────────────────────────────────────────────────
def step3():
    render_logo()
    render_progress(3)
    section_title(
        "3단계: 월 운영비 입력",
        "숙소를 운영하는 데 매달 고정으로 나가는 비용을 입력해주세요.",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔌 공과금 · 관리비**")
        opex_elec  = st.number_input("전기세 (원/월)",  0, 500_000,   st.session_state.opex_elec,  5_000)
        opex_water = st.number_input("수도세 (원/월)",  0, 200_000,   st.session_state.opex_water, 5_000)
        opex_mgmt  = st.number_input("관리비 (원/월)",  0, 1_000_000, st.session_state.opex_mgmt,  10_000)
        opex_net   = st.number_input("인터넷 (원/월)",  0, 100_000,   st.session_state.opex_net,   5_000)
        st.session_state.opex_elec  = opex_elec
        st.session_state.opex_water = opex_water
        st.session_state.opex_mgmt  = opex_mgmt
        st.session_state.opex_net   = opex_net

    with col2:
        st.markdown("**🧹 청소 · 대출 · 기타**")
        opex_clean = st.number_input("청소 비용 (원/월)",  0, 1_000_000, st.session_state.opex_clean, 10_000)
        opex_loan  = st.number_input("대출 이자 (원/월)", 0, 5_000_000, st.session_state.opex_loan,  50_000)
        opex_etc   = st.number_input("기타 비용 (원/월)", 0, 500_000,   st.session_state.opex_etc,   10_000)
        st.session_state.opex_clean = opex_clean
        st.session_state.opex_loan  = opex_loan
        st.session_state.opex_etc   = opex_etc

    total_opex = (opex_elec + opex_water + opex_mgmt + opex_net
                  + opex_clean + opex_loan + opex_etc)
    coral_box(
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:14px;color:#888;">월 총 운영비</span>'
        f'<span class="big-num">₩{total_opex:,}</span>'
        f'</div>'
        f'<div style="font-size:12px;color:#AAA;margin-top:4px;">에어비앤비 수수료 3%는 별도입니다</div>'
    )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back3", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with nc2:
        st.markdown('<div class="nav-balance"></div>', unsafe_allow_html=True)
        next_step = 5 if st.session_state.host_type == "new" else 4
        label = "🔍 분석 결과 보기" if next_step == 5 else "다음 단계 →"
        if st.button(label, key="next3", use_container_width=True):
            st.session_state.step = next_step
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — 운영 현황 체크 + 위치 입력 (기존 호스터 전용)
# ─────────────────────────────────────────────────────────────────────────────
def step4_existing():
    render_logo()
    render_progress(4)
    section_title(
        "4단계: 운영 현황 체크",
        "현재 숙소 운영 상태를 체크해주세요. 개선 포인트를 찾는 데 사용됩니다.",
    )

    bench = get_bench(st.session_state.district, st.session_state.room_type)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**⭐ 리뷰 & 평점**")
        default_rv = int(st.session_state.my_reviews) if st.session_state.my_reviews is not None else int(bench_val(bench, "num_reviews", 20))
        my_reviews = st.number_input("현재 리뷰 수 (건)", 0, 5000, default_rv)
        st.session_state.my_reviews = my_reviews

        default_rt = float(st.session_state.my_rating) if st.session_state.my_rating is not None else round(bench_val(bench, "rating_overall", 4.70), 1)
        my_rating = st.slider("현재 평점", 0.0, 5.0, default_rt, 0.1)
        st.session_state.my_rating = my_rating

        st.markdown("**🏅 배지 & 예약 설정**")
        my_superhost = st.checkbox("슈퍼호스트 배지 있음", value=bool(st.session_state.my_superhost))
        st.session_state.my_superhost = my_superhost
        my_instant = st.checkbox("즉시예약 켜져 있음", value=bool(st.session_state.my_instant))
        st.session_state.my_instant = my_instant
        my_extra_fee = st.checkbox("추가 게스트 요금 받고 있음", value=bool(st.session_state.my_extra_fee))
        st.session_state.my_extra_fee = my_extra_fee

    with col2:
        st.markdown("**📸 사진 & 숙박 설정**")
        default_ph = int(st.session_state.my_photos) if st.session_state.my_photos is not None else int(bench_val(bench, "photos_count", 22))
        my_photos = st.number_input("등록된 사진 수 (장)", 0, 300, default_ph)
        st.session_state.my_photos = my_photos

        default_mn = int(st.session_state.my_min_nights) if st.session_state.my_min_nights is not None else int(bench_val(bench, "min_nights", 2))
        my_min_nights = st.number_input("최소 숙박일 (박)", 1, 365, default_mn)
        st.session_state.my_min_nights = my_min_nights

        # ── 위치 정보 ────────────────────────────────────────────────────────
        st.markdown("**📍 숙소 위치 입력**")
        st.markdown(
            '<div style="font-size:12px;color:#888;margin-bottom:8px;">'
            '주변 관광지 분석에 사용됩니다. 동 이름까지 입력하면 더 정확합니다.</div>',
            unsafe_allow_html=True,
        )
        my_address = st.text_input(
            "주소",
            value=st.session_state.my_address,
            placeholder="예) 마포구 서교동, 홍대입구역, 연남동",
            label_visibility="collapsed",
        )
        st.session_state.my_address = my_address

        if st.button("📍 위치 확인", key="geocode_btn_ex"):
            if my_address.strip():
                with st.spinner("위치 확인 중..."):
                    lat, lng, disp = geocode_address(my_address)
                if lat:
                    st.session_state.my_lat = lat
                    st.session_state.my_lng = lng
                    st.session_state.my_location_name = disp
                    st.session_state.location_confirmed = True
                    st.rerun()
                else:
                    dc = DISTRICT_CENTERS.get(st.session_state.district)
                    if dc:
                        st.session_state.my_lat, st.session_state.my_lng = dc
                        st.session_state.my_location_name = dn(st.session_state.district) + " (자치구 평균)"
                        st.session_state.location_confirmed = True
                    st.warning("정확한 주소를 찾지 못했습니다. 자치구 중심으로 분석합니다.")
                    st.rerun()
            else:
                st.warning("주소를 입력해주세요.")

        if st.session_state.my_lat:
            st.success(f"📍 {st.session_state.my_location_name}")
        else:
            dc = DISTRICT_CENTERS.get(st.session_state.district)
            if dc:
                st.session_state.my_lat, st.session_state.my_lng = dc
                st.session_state.my_location_name = dn(st.session_state.district) + " (자치구 평균)"

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back4", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with nc2:
        st.markdown('<div class="nav-balance"></div>', unsafe_allow_html=True)
        if st.button("🔍 분석 결과 보기", key="next4", use_container_width=True):
            st.session_state.step = 5
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — 분석 결과 대시보드
# ─────────────────────────────────────────────────────────────────────────────
def step5():
    district      = st.session_state.district
    room_type     = st.session_state.room_type
    host_type     = st.session_state.get("host_type", "existing")
    my_adr        = float(st.session_state.my_adr or 100000)
    my_photos     = int(st.session_state.my_photos or 0)
    my_superhost  = bool(st.session_state.my_superhost)
    my_instant    = bool(st.session_state.my_instant)
    my_extra_fee  = bool(st.session_state.my_extra_fee)
    my_min_nights = int(st.session_state.my_min_nights or 2)
    my_rating     = float(st.session_state.my_rating or 4.5)
    my_reviews    = int(st.session_state.my_reviews or 0)
    my_lat        = st.session_state.my_lat
    my_lng        = st.session_state.my_lng
    my_loc_name   = st.session_state.my_location_name

    bench     = get_bench(district, room_type)
    b_adr     = bench_val(bench, "ttm_avg_rate", 100000)
    b_adr_p25 = bench_val(bench, "ttm_avg_rate", 70000, 25)
    b_adr_p75 = bench_val(bench, "ttm_avg_rate", 140000, 75)
    b_revpar  = bench_val(bench, "ttm_revpar", 40000)
    b_occ     = bench_val(bench, "ttm_occupancy", 0.40)

    # 신규 호스터 → 지역 평균 예약률 사용
    if host_type == "new":
        my_occ = b_occ
    else:
        my_occ = (st.session_state.my_occ_pct or int(b_occ * 100)) / 100

    opex_items = {
        "전기세": st.session_state.opex_elec,
        "수도세": st.session_state.opex_water,
        "관리비": st.session_state.opex_mgmt,
        "인터넷": st.session_state.opex_net,
        "청소비": st.session_state.opex_clean,
        "대출이자": st.session_state.opex_loan,
        "기타": st.session_state.opex_etc,
    }
    total_opex      = sum(opex_items.values())
    my_revpar       = my_adr * my_occ
    monthly_revenue = my_revpar * 30
    airbnb_fee      = monthly_revenue * 0.03
    net_profit      = monthly_revenue - airbnb_fee - total_opex
    bep_adr         = (total_opex / 0.97) / (30 * my_occ) if my_occ > 0 else 0

    d_row        = cluster_df[cluster_df["district"] == district]
    cluster_name = d_row["cluster_name"].values[0] if len(d_row) > 0 else "중가 균형시장"
    c_info       = CLUSTER_INFO.get(cluster_name, CLUSTER_INFO["중가 균형시장"])
    elasticity   = c_info["elasticity"]
    d_name       = dn(district)
    rt_name      = ROOM_TYPE_KR.get(room_type, room_type)

    # ── 헤더 ────────────────────────────────────────────────────────────────
    host_badge = "🌱 신규 호스터" if host_type == "new" else "🏅 기존 호스터"
    st.markdown(f"""
    <div style="text-align:center;padding:20px 0 4px;">
      <div style="font-size:34px;">🏠</div>
      <h2 style="color:#FF5A5F;margin:6px 0 2px;font-weight:800;">분석 결과</h2>
      <p style="color:#888;font-size:13px;margin:0;">
        {d_name} · {rt_name} · 실운영 {len(bench):,}개 기준 · {host_badge}
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 탭 구성 ─────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if host_type == "existing":
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 수익 요약", "💡 요금 전략", "📍 주변 관광지", "📋 운영 개선", "🏙️ 지역 진단"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 수익 요약", "💡 요금 추천", "📍 주변 관광지", "🏙️ 지역 진단"
        ])
        tab5 = None

    # ── TAB 1: 수익 요약 (KPI + 손익계산서) ─────────────────────────────────
    with tab1:
        k1, k2, k3 = st.columns(3)
        revpar_diff  = my_revpar - b_revpar
        profit_color = "#2E7D32" if net_profit > 0 else "#C62828"
        bep_ok       = my_adr >= bep_adr

        def kpi_card(col, label, value, sub, sub_color="#767676"):
            col.markdown(
                f'<div style="background:white;border-radius:12px;padding:18px;text-align:center;'
                f'box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
                f'<div style="font-size:12px;color:#888;margin-bottom:6px;">{label}</div>'
                f'<div style="font-size:22px;font-weight:700;color:#484848;">{value}</div>'
                f'<div style="font-size:12px;color:{sub_color};margin-top:4px;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        kpi_card(k1, "하루 평균 실수익", f"₩{int(my_revpar):,}",
                 f"{'▲' if revpar_diff>=0 else '▼'} 지역 평균 대비 ₩{int(abs(revpar_diff)):,}",
                 "#2E7D32" if revpar_diff >= 0 else "#C62828")
        kpi_card(k2, "월 예상 순이익", f"₩{int(net_profit):,}",
                 "흑자 ✅" if net_profit > 0 else "적자 ❌", profit_color)
        kpi_card(k3, "본전 요금", f"₩{int(bep_adr):,}",
                 f"현재 요금 {'이상 ✅' if bep_ok else '이하 ❌'}",
                 "#2E7D32" if bep_ok else "#C62828")

        if host_type == "new":
            st.info(f"💡 신규 호스터는 실제 예약 데이터가 없어 지역 평균 예약률({b_occ:.0%})로 계산했습니다.")

        # 예약률 평일/주말 분리 — 기존 호스터만 표시
        if host_type == "existing":
            wd_occ_pct = st.session_state.get("weekday_occ_pct", 0)
            we_occ_pct = st.session_state.get("weekend_occ_pct", 0)
            overall_pct = int(my_occ * 100)
            wd_col = "#2E7D32" if wd_occ_pct >= overall_pct else "#767676"
            we_col = "#FF5A5F" if we_occ_pct >= overall_pct else "#767676"
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px;">'
                f'<div style="background:white;border-radius:12px;padding:14px 10px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">전체 예약률</div>'
                f'<div style="font-size:24px;font-weight:700;color:#484848;">{overall_pct}%</div>'
                f'<div style="font-size:11px;color:#AAA;">지역 평균 {b_occ:.0%}</div>'
                f'</div>'
                f'<div style="background:white;border-radius:12px;padding:14px 10px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">📅 평일 예약률</div>'
                f'<div style="font-size:24px;font-weight:700;color:{wd_col};">{wd_occ_pct}%</div>'
                f'<div style="font-size:11px;color:#AAA;">월 ~ 금</div>'
                f'</div>'
                f'<div style="background:white;border-radius:12px;padding:14px 10px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">🎉 주말 예약률</div>'
                f'<div style="font-size:24px;font-weight:700;color:{we_col};">{we_occ_pct}%</div>'
                f'<div style="font-size:11px;color:#AAA;">토 ~ 일</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        section_title("💰 월 손익 계산서", "이번 달 예상 수익 구조입니다.")

        col_pnl, col_pie = st.columns(2)
        with col_pnl:
            rows = [
                ("월 매출", f"₩{int(monthly_revenue):,}", "#484848"),
                ("에어비앤비 수수료 (3%)", f"- ₩{int(airbnb_fee):,}", "#C62828"),
                ("월 운영비", f"- ₩{int(total_opex):,}", "#C62828"),
            ]
            html = '<div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
            for label, value, color in rows:
                html += (f'<div style="display:flex;justify-content:space-between;padding:9px 0;'
                         f'border-bottom:1px solid #F5F5F5;">'
                         f'<span style="color:#767676;font-size:14px;">{label}</span>'
                         f'<span style="color:{color};font-weight:600;">{value}</span></div>')
            pc2 = "#2E7D32" if net_profit >= 0 else "#C62828"
            html += (f'<div style="display:flex;justify-content:space-between;padding:12px 0 0;">'
                     f'<span style="font-weight:700;font-size:15px;">월 순이익</span>'
                     f'<span style="font-weight:700;font-size:18px;color:{pc2};">₩{int(net_profit):,}</span></div>')
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
            if net_profit > 0:
                st.success(f"✅ 월 ₩{int(net_profit):,} 흑자")
            elif net_profit == 0:
                st.warning("⚠️ 정확히 본전 상태")
            else:
                st.error(f"❌ 월 ₩{int(abs(net_profit)):,} 적자 — 요금 인상 또는 운영비 절감 필요")

        with col_pie:
            nonzero = {k: v for k, v in opex_items.items() if v > 0}
            if nonzero and total_opex > 0:
                fig, ax = plt.subplots(figsize=(4.5, 4))
                colors = ["#FF5A5F","#FF8A8D","#FFB3B5","#00A699","#4DB6AC","#FFB400","#EBEBEB"]
                ax.pie(nonzero.values(), labels=nonzero.keys(), autopct="%1.0f%%",
                       startangle=90, colors=colors[:len(nonzero)],
                       textprops={"fontsize": 10},
                       wedgeprops={"linewidth": 1, "edgecolor": "white"})
                ax.set_title(f"월 운영비 구성 (₩{total_opex:,})", fontsize=11)
                fig.patch.set_facecolor("#FAFAFA")
                fig.tight_layout()
                st.pyplot(fig)
                plt.close()
            else:
                st.info("운영비를 입력하면 구성 차트가 표시됩니다.")

    # ── TAB 2: 요금 전략 ─────────────────────────────────────────────────────
    with tab2:
        section_title("💡 내 숙소에 맞는 적정 요금")

        if my_superhost and my_rating >= 4.8 and my_reviews >= 50:
            stage, s_color, s_icon = "프리미엄", "#FF5A5F", "🏆"
            rec_min, rec_max = int(b_adr), int(b_adr_p75)
            s_tip = "현재 요금이 지역 평균보다 낮다면 10~20% 인상을 테스트해보세요."
        elif my_reviews >= 10 and my_rating >= 4.5:
            stage, s_color, s_icon = "안정", "#00A699", "📈"
            rec_min, rec_max = int(b_adr_p25), int(b_adr)
            s_tip = "슈퍼호스트 달성 후 요금을 지역 평균 이상으로 올릴 수 있습니다."
        else:
            stage, s_color, s_icon = "신규", "#2196F3", "🌱"
            rec_min = max(int(bep_adr), int(b_adr_p25 * 0.85))
            rec_max = int(b_adr_p25)
            s_tip = "하위 25% 요금으로 첫 10건의 리뷰를 빠르게 쌓은 후 요금을 올리세요."

        t1, t2, t3 = st.columns(3)
        stage_data = [
            ("신규", "🌱", "#2196F3", f"₩{int(b_adr_p25*0.85):,} ~ ₩{int(b_adr_p25):,}", "리뷰 10건 미만"),
            ("안정", "📈", "#00A699", f"₩{int(b_adr_p25):,} ~ ₩{int(b_adr):,}", "리뷰 10건+ & 평점 4.5+"),
            ("프리미엄", "🏆", "#FF5A5F", f"₩{int(b_adr):,} ~ ₩{int(b_adr_p75):,}", "슈퍼호스트 & 평점 4.8+"),
        ]
        for col, (sname, sicon, scolor, sprice, scond) in zip([t1, t2, t3], stage_data):
            is_me = sname == stage
            bg    = scolor if is_me else "#F7F7F7"
            fc    = "white" if is_me else "#767676"
            border = f"3px solid {scolor}" if is_me else "2px solid #EBEBEB"
            me_tag = (f'<div style="margin-top:8px;"><span style="background:white;color:{scolor};'
                      f'padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;">▲ 내 단계</span></div>'
                      if is_me else "")
            col.markdown(
                f'<div style="border:{border};border-radius:12px;padding:18px;text-align:center;background:{bg};color:{fc};">'
                f'<div style="font-size:22px;">{sicon}</div>'
                f'<div style="font-weight:700;font-size:14px;margin:6px 0;">{sname} 호스트</div>'
                f'<div style="font-size:11px;opacity:0.85;margin-bottom:8px;">{scond}</div>'
                f'<div style="font-size:15px;font-weight:700;">{sprice}</div>'
                f'{me_tag}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if my_adr < rec_min:
            gap_msg, gap_icon, gap_bg = (f"현재 요금 ₩{int(my_adr):,}이 추천 구간보다 ₩{rec_min - int(my_adr):,} 낮습니다.", "⬆️", "#E3F2FD")
        elif my_adr > rec_max:
            gap_msg, gap_icon, gap_bg = (f"현재 요금 ₩{int(my_adr):,}이 추천 구간보다 ₩{int(my_adr) - rec_max:,} 높습니다.", "⚠️", "#FFF8E1")
        else:
            gap_msg, gap_icon, gap_bg = ("현재 요금이 내 단계에 맞는 구간 안에 있습니다. 잘 하고 계세요!", "✅", "#E8F5E9")

        st.markdown(
            f'<div style="background:{gap_bg};border-left:4px solid {s_color};border-radius:10px;padding:16px 18px;">'
            f'<div style="font-weight:700;color:{s_color};margin-bottom:6px;">{s_icon} {stage} 호스터 — 추천 요금 ₩{rec_min:,} ~ ₩{rec_max:,}</div>'
            f'<div style="font-size:13px;color:#484848;">{gap_icon} {gap_msg}</div>'
            f'<div style="font-size:12px;color:#767676;margin-top:6px;">💬 {s_tip}</div>'
            f'<div style="font-size:11px;color:#AAAAAA;margin-top:8px;">'
            f'본전 ₩{int(bep_adr):,} | 하위25% ₩{int(b_adr_p25):,} | 평균 ₩{int(b_adr):,} | 상위25% ₩{int(b_adr_p75):,}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # F. 요금 시뮬레이션 (기존 호스터 전용)
        if host_type == "existing":
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            section_title(
                "📊 요금 변경 시뮬레이션",
                f"이 지역({cluster_name})은 요금을 10% 올리면 예약률이 약 {abs(elasticity)*10:.0f}% 변화합니다.",
            )

            delta_pct = st.slider("요금 변화율 (%)", -30, 50, 0, 5)
            delta     = delta_pct / 100
            new_adr   = my_adr * (1 + delta)
            new_occ   = min(1.0, max(0.0, my_occ * (1 + elasticity * delta)))
            new_revp  = new_adr * new_occ
            new_net   = new_revp * 30 * 0.97 - total_opex
            p_change  = new_net - net_profit

            cs1, cs2 = st.columns(2)
            with cs1:
                sim_rows = [
                    ("1박 요금", f"₩{int(my_adr):,}", f"₩{int(new_adr):,}", f"{delta_pct:+d}%"),
                    ("예약률", f"{my_occ:.0%}", f"{new_occ:.0%}", f"{(new_occ-my_occ)*100:+.1f}%p"),
                    ("하루 실수익", f"₩{int(my_revpar):,}", f"₩{int(new_revp):,}",
                     f"{(new_revp/my_revpar-1)*100:+.1f}%" if my_revpar > 0 else "-"),
                    ("월 순이익", f"₩{int(net_profit):,}", f"₩{int(new_net):,}", f"₩{p_change:+,.0f}"),
                ]
                html = ('<div style="background:white;border-radius:12px;padding:20px;'
                        'box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
                        '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;'
                        'color:#888;font-size:12px;font-weight:600;padding-bottom:8px;'
                        'border-bottom:1.5px solid #F0F0F0;margin-bottom:4px;">'
                        '<span>항목</span><span style="text-align:right;">현재</span>'
                        '<span style="text-align:right;">변경 후</span>'
                        '<span style="text-align:right;">변화</span></div>')
                for label, cur, nxt, chg in sim_rows:
                    w = "700" if "순이익" in label else "400"
                    chg_c = "#2E7D32" if ("+" in chg and "₩-" not in chg) else "#C62828" if ("-" in chg and "₩+" not in chg) else "#484848"
                    html += (f'<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;'
                             f'padding:9px 0;border-bottom:1px solid #F5F5F5;font-weight:{w};">'
                             f'<span style="font-size:13px;">{label}</span>'
                             f'<span style="text-align:right;font-size:13px;">{cur}</span>'
                             f'<span style="text-align:right;font-size:13px;">{nxt}</span>'
                             f'<span style="text-align:right;font-size:13px;color:{chg_c};">{chg}</span></div>')
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

                if delta_pct == 0:
                    st.info("슬라이더를 움직여 요금 변화 효과를 확인하세요.")
                elif delta_pct > 0 and p_change > 0:
                    st.success(f"✅ 요금 인상 효과 — 순이익 ₩{p_change:+,.0f} 증가")
                elif delta_pct > 0:
                    st.error(f"❌ 요금 인상 역효과 — 순이익 ₩{abs(p_change):,.0f} 감소")
                elif p_change > 0:
                    st.success(f"✅ 요금 인하로 예약률 상승 → 순이익 ₩{p_change:+,.0f} 증가")
                else:
                    st.warning(f"⚠️ 요금 인하 시 순이익 ₩{abs(p_change):,.0f} 감소")

            with cs2:
                x_range = np.linspace(-0.30, 0.50, 80)
                profits = [
                    my_adr*(1+d) * min(1., max(0., my_occ*(1+elasticity*d))) * 30 * 0.97 - total_opex
                    for d in x_range
                ]
                fig4, ax4 = plt.subplots(figsize=(5, 3.8))
                ax4.plot(x_range*100, profits, color="#FF5A5F", linewidth=2.5)
                ax4.axhline(0, color="#767676", linestyle="--", lw=1.2, alpha=0.6, label="손익분기선")
                ax4.axvline(delta_pct, color="#FFB400", linestyle="--", lw=1.5, label=f"현재 ({delta_pct:+d}%)")
                ax4.scatter([delta_pct], [new_net], color="#FFB400", s=70, zorder=6)
                ax4.fill_between(x_range*100, profits, 0, where=[p > 0 for p in profits], alpha=0.07, color="#4CAF50")
                ax4.fill_between(x_range*100, profits, 0, where=[p <= 0 for p in profits], alpha=0.07, color="#FF5A5F")
                ax4.set_xlabel("요금 변화율 (%)"); ax4.set_ylabel("월 순이익 (원)")
                ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"₩{y/10000:.0f}만"))
                ax4.legend(fontsize=8)
                ax4.spines["top"].set_visible(False); ax4.spines["right"].set_visible(False)
                ax4.set_facecolor("#FAFAFA"); fig4.patch.set_facecolor("#FAFAFA")
                fig4.tight_layout()
                st.pyplot(fig4); plt.close()
                best_idx  = int(np.argmax(profits))
                best_adr  = my_adr * (1 + x_range[best_idx])
                best_prof = profits[best_idx]
                st.success(f"🎯 최대 순이익: ₩{int(best_adr):,} ({x_range[best_idx]*100:+.0f}%) → 월 ₩{int(best_prof):,}")

    # ── TAB 3: 주변 관광지 ────────────────────────────────────────────────────
    with tab3:
        section_title(
            "📍 숙소 주변 관광지 분석",
            f"위치: {my_loc_name or d_name} 기준 — 데이터베이스 내 2,965개 POI 기반",
        )

        if my_lat and my_lng:
            with st.spinner("주변 관광지 분석 중..."):
                nearby = find_nearby_pois(my_lat, my_lng, max_km=2.0)

            cnt_500m = sum(1 for p in nearby if p["dist_m"] <= 500)
            cnt_1km  = sum(1 for p in nearby if p["dist_m"] <= 1000)
            cnt_2km  = len(nearby)

            sc1, sc2, sc3 = st.columns(3)
            def stat_box(col, label, value, sub, color="#FF5A5F"):
                col.markdown(
                    f'<div style="background:white;border-radius:12px;padding:18px;text-align:center;'
                    f'box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
                    f'<div style="font-size:12px;color:#888;margin-bottom:4px;">{label}</div>'
                    f'<div style="font-size:28px;font-weight:700;color:{color};">{value}</div>'
                    f'<div style="font-size:12px;color:#888;margin-top:4px;">{sub}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            stat_box(sc1, "500m 이내 관광지", f"{cnt_500m}개", "도보 6분 거리")
            stat_box(sc2, "1km 이내 관광지", f"{cnt_1km}개", "도보 12분 거리")
            stat_box(sc3, "2km 이내 관광지", f"{cnt_2km}개", "전체 주변 반경")

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(
                '<div style="font-weight:700;font-size:15px;color:#484848;margin-bottom:10px;">'
                '🗺️ 가장 가까운 관광지 TOP 5</div>',
                unsafe_allow_html=True,
            )
            if nearby:
                for i, poi in enumerate(nearby[:5], 1):
                    icon = POI_TYPE_ICON.get(poi["type"], "📌")
                    dist_txt = f"{poi['dist_m']}m" if poi["dist_m"] < 1000 else f"{poi['dist_km']:.2f}km"
                    type_color = {
                        "관광지": "#FF5A5F", "문화시설": "#9C27B0", "음식점": "#FF9800",
                        "쇼핑": "#2196F3", "숙박": "#00A699", "레포츠": "#4CAF50",
                        "여행코스": "#795548", "축제공연행사": "#E91E63",
                    }.get(poi["type"], "#888")
                    st.markdown(
                        f'<div style="background:white;border:1.5px solid #EBEBEB;border-radius:10px;'
                        f'padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:14px;">'
                        f'<div style="background:#FF5A5F;color:white;border-radius:50%;min-width:28px;height:28px;'
                        f'display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;">{i}</div>'
                        f'<div style="flex:1;">'
                        f'<div style="font-weight:600;font-size:14px;">{icon} {poi["name"]}</div>'
                        f'<div style="font-size:12px;color:#888;margin-top:2px;">{poi.get("addr","")}</div>'
                        f'</div>'
                        f'<div style="text-align:right;min-width:80px;">'
                        f'<span style="background:{type_color}20;color:{type_color};font-size:11px;'
                        f'font-weight:600;padding:2px 8px;border-radius:20px;">{poi["type"]}</span><br>'
                        f'<span style="font-size:13px;font-weight:700;color:#484848;margin-top:4px;">{dist_txt}</span>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("데이터베이스에서 2km 이내 관광지를 찾지 못했습니다.")

            if nearby:
                st.markdown(
                    '<div style="font-weight:700;font-size:15px;color:#484848;margin:16px 0 10px;">'
                    '📊 1km 이내 관광지 유형 분포</div>',
                    unsafe_allow_html=True,
                )
                nearby_1km = [p for p in nearby if p["dist_m"] <= 1000]
                if nearby_1km:
                    type_counts = {}
                    for p in nearby_1km:
                        t = p["type"]
                        type_counts[t] = type_counts.get(t, 0) + 1
                    type_counts = dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True))

                    bar_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;">'
                    for t, cnt in type_counts.items():
                        icon = POI_TYPE_ICON.get(t, "📌")
                        color = {
                            "관광지": "#FF5A5F", "문화시설": "#9C27B0", "음식점": "#FF9800",
                            "쇼핑": "#2196F3", "숙박": "#00A699", "레포츠": "#4CAF50",
                            "여행코스": "#795548", "축제공연행사": "#E91E63",
                        }.get(t, "#888")
                        bar_html += (
                            f'<div style="background:{color}15;border:1.5px solid {color};'
                            f'border-radius:20px;padding:6px 14px;font-size:13px;">'
                            f'{icon} {t} <b style="color:{color};">{cnt}개</b></div>'
                        )
                    bar_html += "</div>"
                    st.markdown(bar_html, unsafe_allow_html=True)

                    bench_500m = bench_val(bench, "nearest_500m", 19)
                    bench_1km  = bench_val(bench, "nearest_1km", 79)
                    st.markdown(
                        f'<div style="background:#F7F7F7;border-radius:10px;padding:12px 16px;">'
                        f'<span style="font-size:13px;color:#484848;">'
                        f'<b>지역 평균 비교</b> — {d_name} {rt_name} 실운영 숙소 기준<br>'
                        f'500m 이내: 평균 <b>{int(bench_500m)}개</b> vs 내 숙소 <b style="color:{"#2E7D32" if cnt_500m>=bench_500m else "#C62828"};">{cnt_500m}개</b>'
                        f' &nbsp;|&nbsp; '
                        f'1km 이내: 평균 <b>{int(bench_1km)}개</b> vs 내 숙소 <b style="color:{"#2E7D32" if cnt_1km>=bench_1km else "#C62828"};">{cnt_1km}개</b>'
                        f'</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("1km 이내 관광지가 없습니다. 관광지 접근성이 낮은 지역에 위치해 있습니다.")
        else:
            st.info("주소를 입력하면 주변 관광지 분석 결과가 여기에 표시됩니다.")

    # ── TAB 4: 운영 개선(기존) / 지역진단(신규) ──────────────────────────────
    def _render_market_tab(tab_obj):
        with tab_obj:
            section_title(
                f"{c_info['emoji']} {d_name} 시장 유형: {cluster_name}",
                c_info["desc"],
            )
            col_m1, col_m2 = st.columns([1, 1.4])
            with col_m1:
                st.markdown(
                    f'<div style="background:{c_info["color"]}15;border:2px solid {c_info["color"]};'
                    f'border-radius:12px;padding:20px;">'
                    f'<div style="font-size:34px;">{c_info["emoji"]}</div>'
                    f'<div style="font-weight:700;font-size:15px;color:{c_info["color"]};margin:8px 0;">{cluster_name}</div>'
                    f'<div style="font-size:13px;color:#484848;">{c_info["desc"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if len(d_row) > 0:
                    row = d_row.iloc[0]
                    info_row("지역 평균 하루 수익", f"₩{int(row.get('median_revpar_ao', 0)):,}")
                    info_row("비활성 숙소 비율", f"{row.get('dormant_ratio', 0):.1%}")
                    info_row("슈퍼호스트 비율", f"{row.get('superhost_rate', 0):.1%}")
            with col_m2:
                st.markdown("**이 지역에서 수익을 올리는 전략:**")
                for i, strat in enumerate(c_info["strategy"], 1):
                    st.markdown(
                        f'<div style="background:white;border:1.5px solid #EBEBEB;border-radius:8px;'
                        f'padding:10px 14px;margin-bottom:6px;">'
                        f'<span style="background:#FF5A5F;color:white;border-radius:50%;padding:1px 7px;'
                        f'font-size:11px;font-weight:700;margin-right:8px;">{i}</span>'
                        f'<span style="font-size:14px;">{strat}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    if host_type == "existing":
        with tab4:
            section_title("📋 지금 바로 개선할 수 있는 것들")

            checks = []
            if my_superhost:
                checks.append(("✅", "슈퍼호스트 달성", "수익 +83% 프리미엄 유지 중", "done"))
            else:
                est = my_revpar * 1.831
                checks.append(("🔴", "슈퍼호스트 미달성",
                    f"달성 시 하루 수익 ₩{int(my_revpar):,} → ₩{int(est):,} 잠재", "todo"))
            if my_instant:
                checks.append(("✅", "즉시예약 켜짐", "예약률 최대화 중", "done"))
            else:
                checks.append(("🟡", "즉시예약 꺼짐", "설정 1분, 비용 없음 → 예약률 +5~10% 기대", "quick"))
            if 20 <= my_photos <= 35:
                checks.append(("✅", f"사진 {my_photos}장 (최적)", "최적 20~35장 구간 유지 중", "done"))
            elif my_photos < 20:
                checks.append(("🔴", f"사진 {my_photos}장 (부족)", f"{20-my_photos}장 추가 → 클릭률 상승", "todo"))
            else:
                checks.append(("🟡", f"사진 {my_photos}장 (많음)", "35장 초과 — 좋은 사진만 추려서 정리 권장", "quick"))
            if not my_extra_fee:
                checks.append(("✅", "추가 게스트 요금 없음", "요금에 포함 — 최적 구조", "done"))
            else:
                checks.append(("🔴", "추가 게스트 요금 있음", "없애고 1박 요금에 통합 → 수익 +25~56% 회복", "quick"))
            if 2 <= my_min_nights <= 3:
                checks.append(("✅", f"최소 {my_min_nights}박 (최적)", "수익 최적 + 리뷰 축적 속도 최적", "done"))
            elif my_min_nights == 1:
                checks.append(("🟡", "최소 1박", "수익 효율 낮음 — 2박으로 변경 추천", "quick"))
            else:
                checks.append(("🟡", f"최소 {my_min_nights}박 (길음)", "리뷰 축적 속도 느림 — 2~3박으로 줄이기", "quick"))
            if my_rating >= 4.8:
                checks.append(("✅", f"평점 {my_rating:.1f}", "슈퍼호스트 기준 충족 + 검색 상위", "done"))
            elif my_rating >= 4.5:
                checks.append(("🟡", f"평점 {my_rating:.1f}", "4.8 이상이면 슈퍼호스트 + 검색 부스트", "todo"))
            else:
                checks.append(("🔴", f"평점 {my_rating:.1f} (낮음)", "4.5 미만 — 검색 노출 불이익", "todo"))
            if my_reviews >= 10:
                checks.append(("✅", f"리뷰 {my_reviews}건", "슈퍼호스트 최소 요건 충족", "done"))
            else:
                checks.append(("🔴", f"리뷰 {my_reviews}건",
                    f"슈퍼호스트 최소 10건 필요 — {10-my_reviews}건 더 필요", "todo"))

            col_c1, col_c2 = st.columns(2)
            for i, (icon, title, desc, status) in enumerate(checks):
                col = col_c1 if i % 2 == 0 else col_c2
                bg_c     = "#F1F8F4" if status=="done" else "#FFF8E1" if status=="quick" else "#FFF0EE"
                border_c = "#4CAF50" if status=="done" else "#FFB400" if status=="quick" else "#FF5A5F"
                col.markdown(
                    f'<div style="background:{bg_c};border-left:3px solid {border_c};border-radius:8px;'
                    f'padding:12px 14px;margin-bottom:8px;">'
                    f'<span style="font-weight:600;font-size:14px;">{icon} {title}</span><br>'
                    f'<span style="font-size:12px;color:#767676;">{desc}</span></div>',
                    unsafe_allow_html=True,
                )

            quick_list = [(icon, title, desc) for icon, title, desc, status in checks if status in ("quick","todo")]
            if quick_list:
                st.markdown("#### 🎯 지금 당장 실행하면 효과 큰 TOP 3")
                for i, (icon, title, desc) in enumerate(quick_list[:3], 1):
                    st.markdown(
                        f'<div style="background:white;border:1.5px solid #FFE0DE;border-radius:10px;'
                        f'padding:14px 16px;margin-bottom:8px;display:flex;align-items:flex-start;">'
                        f'<span style="background:#FF5A5F;color:white;border-radius:50%;min-width:24px;height:24px;'
                        f'display:flex;align-items:center;justify-content:center;font-size:12px;'
                        f'font-weight:700;margin-right:12px;">{i}</span>'
                        f'<div><b style="font-size:14px;">{title}</b><br>'
                        f'<span style="font-size:12px;color:#767676;">{desc}</span></div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("🎉 모든 운영 레버가 최적 상태입니다!")

        _render_market_tab(tab5)
    else:
        _render_market_tab(tab4)

    # ── 다시 시작 ────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        if st.button("🔄 처음부터 다시 입력하기", key="restart", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("""
    <div style="text-align:center;padding:20px 0;color:#BBBBBB;font-size:12px;">
      서울 Airbnb 수익 최적화 · 데이터 기간: 2024-10 ~ 2025-09 · 32,061개 리스팅 기반
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 라우터
# ─────────────────────────────────────────────────────────────────────────────
step      = st.session_state.get("step", 1)
host_type = st.session_state.get("host_type", None)

if step == 1:
    step1()
elif step == 2:
    if host_type == "new":
        step2_new()
    else:
        step2_existing()
elif step == 3:
    step3()
elif step == 4:
    step4_existing()
else:
    step5()
