import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import calendar as cal_mod
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from pathlib import Path
import sys
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
    import os
    system = platform.system()
    if system == "Darwin":
        candidates = ["AppleGothic", "Apple SD Gothic Neo", "Arial Unicode MS"]
    elif system == "Windows":
        candidates = ["Malgun Gothic", "NanumGothic", "Gulim"]
    else:
        # Linux (Streamlit Cloud 등) — fonts-nanum 패키지 경로 직접 등록
        nanum_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/nanum/NanumGothic.ttf",
        ]
        for p in nanum_paths:
            if os.path.exists(p):
                fm.fontManager.addfont(p)
                break
        candidates = ["NanumGothic", "NanumBarunGothic", "UnDotum", "DejaVu Sans"]
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

  /* 기본 버튼 — 흰색 (캘린더 미선택 날짜도 이 스타일) */
  .stButton > button {
    background-color: white !important; color: #484848 !important;
    border: 1.5px solid #DDDDDD !important; border-radius: 10px !important;
    padding: 12px 28px !important; font-size: 15px !important;
    font-weight: 600 !important; width: 100% !important;
    cursor: pointer !important; transition: background 0.2s !important;
  }
  .stButton > button:hover { background-color: #F7F7F7 !important; }

  /* 주요 액션 버튼 — 코랄 (다음 단계, 분석 결과 보기 등) */
  .nav-primary .stButton > button {
    background-color: #FF5A5F !important; color: white !important;
    border: none !important;
  }
  .nav-primary .stButton > button:hover { background-color: #E8484D !important; }

  /* 예약된 날짜 버튼 (type="primary") — 코랄 */
  .stButton > button[data-testid="stBaseButton-primary"],
  button[kind="primary"] {
    background-color: #FF5A5F !important; color: white !important;
    border: none !important;
  }
  .stButton > button[data-testid="stBaseButton-primary"]:hover,
  button[kind="primary"]:hover { background-color: #E8484D !important; }

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

  /* ── iOS 스타일 달력 날짜 버튼 공통 ── */
  .cal-weekday .stButton > button,
  .cal-sun .stButton > button,
  .cal-sat .stButton > button,
  .cal-holiday .stButton > button,
  .cal-booked .stButton > button,
  .cal-booked-red .stButton > button,
  .cal-booked-blue .stButton > button {
    min-height: 44px !important; max-height: 44px !important;
    font-size: 18px !important; font-weight: 400 !important;
    padding: 0 4px !important; border: none !important;
    background: transparent !important;
    width: 100% !important; line-height: 44px !important;
    border-radius: 22px !important;
  }
  /* 평일 (월~금) */
  .cal-weekday .stButton > button { color: #1C1C1E !important; }
  .cal-weekday .stButton > button:hover {
    background: #F2F2F7 !important; color: #FF5A5F !important;
  }
  /* 일요일 + 일요일 공휴일 → 빨간색 */
  .cal-sun .stButton > button { color: #FF3B30 !important; }
  .cal-sun .stButton > button:hover { background: #FFF0EE !important; }
  /* 토요일 → 파란색 */
  .cal-sat .stButton > button { color: #007AFF !important; }
  .cal-sat .stButton > button:hover { background: #EEF4FF !important; }
  /* 평일 공휴일 → 빨간색 */
  .cal-holiday .stButton > button { color: #FF3B30 !important; font-weight: 500 !important; }
  .cal-holiday .stButton > button:hover { background: #FFF0EE !important; }
  /* 예약됨 (평일/공휴일) — 코랄 원형 채우기 */
  .cal-booked .stButton > button {
    background: #FF5A5F !important; color: white !important;
    font-weight: 700 !important;
  }
  .cal-booked .stButton > button:hover { background: #E8484D !important; }
  /* 예약됨 (일요일) */
  .cal-booked-red .stButton > button {
    background: #FF3B30 !important; color: white !important; font-weight: 700 !important;
  }
  .cal-booked-red .stButton > button:hover { background: #D62D20 !important; }
  /* 예약됨 (토요일) */
  .cal-booked-blue .stButton > button {
    background: #007AFF !important; color: white !important; font-weight: 700 !important;
  }
  .cal-booked-blue .stButton > button:hover { background: #0062CC !important; }

  /* POI 뱃지 */
  .poi-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600; margin-right: 4px;
  }

  /* 네비게이션 버튼 정렬 — back-btn/nav-primary 마크다운 래퍼를 0높이로 */
  div[data-testid="stMarkdownContainer"]:has(.back-btn),
  div[data-testid="stMarkdownContainer"]:has(.nav-primary) {
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

# 2026년 대한민국 공휴일 (월, 일) 기준
HOLIDAYS = {
    2026: {
        (1, 1): "신정",
        (2, 16): "설날 전날",
        (2, 17): "설날",
        (2, 18): "설날 다음날",
        (3, 1): "삼일절",
        (3, 2): "삼일절 대체",
        (5, 5): "어린이날",
        (5, 24): "부처님오신날",
        (5, 25): "부처님오신날 대체",
        (6, 3): "지방선거일",
        (6, 6): "현충일",
        (8, 15): "광복절",
        (8, 17): "광복절 대체",
        (9, 24): "추석 전날",
        (9, 25): "추석",
        (9, 26): "추석 다음날",
        (10, 3): "개천절",
        (10, 5): "개천절 대체",
        (10, 9): "한글날",
        (12, 25): "크리스마스",
    }
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

# ── ML 모델 로드 (INTEGRATION_GUIDE.md 캐싱 패턴) ─────────────────────────────
_PKG_DIR = Path(__file__).parent / "revpar_model_package"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from predict_utils import load_models, predict_revpar, compute_health_score  # noqa: E402

@st.cache_resource
def load_ml_models():
    return load_models(_PKG_DIR / "models")

@st.cache_data
def load_district_lookup():
    return pd.read_csv(str(_PKG_DIR / "district_lookup.csv")).set_index("district")

@st.cache_data
def load_cluster_listings():
    return pd.read_csv(str(_PKG_DIR / "cluster_listings_ao.csv"))

ml_artifacts       = load_ml_models()
ml_district_lookup = load_district_lookup()
ml_ao_df           = load_cluster_listings()

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
        "weekdays_booked": 0,
        "weekends_booked": 0,
        "weekdays_total": 22,
        "weekends_total": 9,
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

    # ── 요일 헤더 — 일요일 먼저 (iOS 스타일) ────────────────────────────────
    # 일=빨강, 토=파랑, 평일=진회색
    DAY_NAMES   = ["일", "월", "화", "수", "목", "금", "토"]
    DAY_COLORS  = ["#FF3B30", "#333", "#333", "#333", "#333", "#333", "#007AFF"]
    header_html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:4px;">'
    for d, c in zip(DAY_NAMES, DAY_COLORS):
        header_html += (
            f'<div style="text-align:center;font-size:13px;font-weight:600;'
            f'color:{c};padding:8px 0 4px;">{d}</div>'
        )
    header_html += "</div>"
    # 구분선
    header_html += '<div style="border-top:1px solid #E5E5EA;margin-bottom:4px;"></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── 달력 그리드 — 일요일 시작 ────────────────────────────────────────────
    cal_mod.setfirstweekday(6)   # 6 = Sunday first
    month_cal = cal_mod.monthcalendar(year, month)
    cal_mod.setfirstweekday(0)   # 원상복구 (Monday)
    year_holidays = HOLIDAYS.get(year, {})

    for w_idx, week in enumerate(month_cal):
        cols = st.columns(7)
        for i, day in enumerate(week):
            # i=0 → 일요일, i=6 → 토요일
            is_sunday   = (i == 0)
            is_saturday = (i == 6)

            with cols[i]:
                if day == 0:
                    # 빈 칸
                    st.markdown('<div style="height:59px;"></div>', unsafe_allow_html=True)
                else:
                    is_booked  = day in booked
                    hname      = year_holidays.get((month, day), "")
                    is_holiday = bool(hname)

                    # ── CSS 클래스 결정 (우선순위: 예약 > 요일/공휴일) ────────
                    if is_booked:
                        css_class = "cal-booked-red" if is_sunday else (
                                    "cal-booked-blue" if is_saturday else "cal-booked")
                    elif is_sunday or (is_holiday and is_sunday):
                        css_class = "cal-sun"
                    elif is_saturday:
                        css_class = "cal-sat"
                    elif is_holiday:
                        css_class = "cal-holiday"
                    else:
                        css_class = "cal-weekday"

                    # ── 버튼 (날짜 숫자만) — 예약됨: primary(코랄), 미예약: secondary(흰색) ──
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    btn_type = "primary" if is_booked else "secondary"
                    if st.button(str(day), key=f"cal_{year}_{month}_{day}",
                                 use_container_width=True, type=btn_type):
                        if day in booked:
                            st.session_state.booked_days.discard(day)
                        else:
                            st.session_state.booked_days.add(day)
                        st.rerun()

                    # ── 공휴일 이름 (버튼 아래, 15px 고정 행) ────────────────
                    if hname:
                        hcolor = "white" if is_booked else "#FF3B30"
                        short  = hname if len(hname) <= 5 else hname[:4] + "…"
                        st.markdown(
                            f'<div style="text-align:center;font-size:9px;font-weight:600;'
                            f'color:{hcolor};height:15px;line-height:15px;'
                            f'overflow:hidden;white-space:nowrap;">{short}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown('<div style="height:15px;"></div>', unsafe_allow_html=True)

        # 주 구분선 (마지막 주 제외)
        if w_idx < len(month_cal) - 1:
            st.markdown(
                '<div style="border-top:1px solid #F0F0F0;margin:2px 0 4px;"></div>',
                unsafe_allow_html=True,
            )

    # ── 달력 범례 ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;align-items:center;">
      <span style="font-size:11px;color:#888;display:flex;align-items:center;gap:5px;">
        <span style="display:inline-block;width:16px;height:16px;background:#FF5A5F;
          border-radius:50%;"></span>예약됨</span>
      <span style="font-size:11px;color:#FF3B30;font-weight:600;">일 = 일요일</span>
      <span style="font-size:11px;color:#007AFF;font-weight:600;">토 = 토요일</span>
      <span style="font-size:11px;color:#FF3B30;">빨간 숫자 = 공휴일</span>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        if st.button("다음 단계 →", key="next1", use_container_width=True, type="primary"):
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
        _raw_g = st.session_state.my_guests
        default_g = max(1, int(_raw_g) if _raw_g is not None else int(bench_val(bench, "guests", 2)))
        my_guests = st.number_input("👥 최대 숙박 인원", 1, 20, default_g)
        st.session_state.my_guests = my_guests

    with r2c2:
        _raw_br = st.session_state.my_bedrooms
        default_br = max(1, int(_raw_br) if _raw_br is not None else int(bench_val(bench, "bedrooms", 1)))
        my_bedrooms = st.number_input("🛏️ 침실 수", 0, 20, default_br)
        st.session_state.my_bedrooms = my_bedrooms

    with r2c3:
        _raw_bt = st.session_state.my_baths_count
        default_bt = max(1, int(_raw_bt) if _raw_bt is not None else int(bench_val(bench, "baths", 1)))
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
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        if st.button("다음 단계 →", key="next2n", use_container_width=True, type="primary"):
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
    st.session_state.weekdays_booked = wd_booked
    st.session_state.weekends_booked = we_booked
    st.session_state.weekdays_total = wd_total
    st.session_state.weekends_total = we_total

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
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        if st.button("다음 단계 →", key="next2e", use_container_width=True, type="primary"):
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
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        next_step = 5 if st.session_state.host_type == "new" else 4
        label = "🔍 분석 결과 보기" if next_step == 5 else "다음 단계 →"
        if st.button(label, key="next3", use_container_width=True, type="primary"):
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
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        if st.button("🔍 분석 결과 보기", key="next4", use_container_width=True, type="primary"):
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

    # ── ML 예측 계산 ─────────────────────────────────────────────────────────
    def _poi_dist_cat(d):
        if d < 0.2:  return "초근접"
        if d < 0.5:  return "근접"
        if d < 1.0:  return "보통"
        return "원거리"

    def _photos_tier(n):
        if n < 14:   return "하"
        if n < 23:   return "중하"
        if n <= 35:  return "중상"
        return "상"

    # POI 거리 계산 (위치 확인 시 실거리, 없으면 벤치마크 중위값)
    if my_lat and my_lng:
        _nearby_pois = find_nearby_pois(my_lat, my_lng, max_km=5.0)
        _poi_dist = _nearby_pois[0]["dist_km"] if _nearby_pois else 0.5
        _poi_type = _nearby_pois[0]["type"]    if _nearby_pois else "관광지"
    else:
        _poi_dist = float(bench_val(bench, "nearest_poi_dist_km", 0.5))
        _poi_type = "관광지"

    # district_lookup 조회
    _dl = ml_district_lookup.loc[district] if district in ml_district_lookup.index \
        else ml_district_lookup.iloc[0]

    _listing = {
        "cluster":                   int(_dl["cluster"]),
        "district_median_revpar":    float(_dl["district_median_revpar"]),
        "district_listing_count":    int(_dl["district_listing_count"]),
        "district_superhost_rate":   float(_dl["district_superhost_rate"]),
        "district_entire_home_rate": float(_dl["district_entire_home_rate"]),
        "ttm_pop":                   int(_dl["ttm_pop"]),
        "room_type":                 room_type,
        "bedrooms":    int(st.session_state.my_bedrooms  or bench_val(bench, "bedrooms", 1)),
        "baths":     float(st.session_state.my_baths_count or bench_val(bench, "baths", 1)),
        "guests":      int(st.session_state.my_guests    or bench_val(bench, "guests",   2)),
        "min_nights":              my_min_nights,
        "instant_book":            1 if my_instant  else 0,
        "superhost":               1 if my_superhost else 0,
        "rating_overall":          my_rating  or 4.5,
        "photos_count":            my_photos  or 0,
        "num_reviews":             my_reviews or 0,
        "extra_guest_fee_policy":  "1" if my_extra_fee else "0",
        "is_active_operating":     1,
        "nearest_poi_dist_km":     _poi_dist,
        "poi_dist_category":       _poi_dist_cat(_poi_dist),
        "nearest_poi_type_name":   _poi_type,
        "photos_tier":             _photos_tier(my_photos or 0),
        "ttm_avg_rate":            my_adr,
    }

    try:
        _ml    = predict_revpar(_listing, opex_per_month=total_opex, **ml_artifacts)
        _ml_ok = True
    except Exception:
        _ml_ok = False
        _ml    = {}

    # 헬스스코어 (기존 호스터 전용)
    if host_type == "existing":
        _cluster_id       = int(_dl["cluster"])
        _cluster_listings = ml_ao_df[ml_ao_df["cluster"] == _cluster_id]
        _user_vals = {
            "my_reviews":    my_reviews or 0,
            "my_rating":     my_rating  or 4.5,
            "my_photos":     my_photos  or 0,
            "my_instant":    my_instant,
            "my_min_nights": my_min_nights,
            "my_extra_fee":  my_extra_fee,
            "my_poi_dist":   _poi_dist,
            "my_bedrooms":   int(st.session_state.my_bedrooms   or bench_val(bench, "bedrooms", 1)),
            "my_baths":    float(st.session_state.my_baths_count or bench_val(bench, "baths",    1)),
        }
        try:
            _hs    = compute_health_score(_user_vals, _cluster_listings)
            _hs_ok = True
        except Exception:
            _hs_ok = False
            _hs    = {}
    else:
        _hs_ok = False
        _hs    = {}

    st.markdown("""
    <div style="text-align:center;padding:20px 0 4px;">
      <div style="font-size:34px;">🏠</div>
      <h2 style="color:#FF5A5F;margin:6px 0 2px;font-weight:800;">분석 결과</h2>
    </div>
    """, unsafe_allow_html=True)

    # ── 분석 요약 카드 (탭 상단) ─────────────────────────────────────────────
    _revpar_diff_s = my_revpar - b_revpar
    _diff_arrow    = "▲" if _revpar_diff_s >= 0 else "▼"
    _diff_color    = "#2E7D32" if _revpar_diff_s >= 0 else "#C62828"
    _profit_label  = "흑자" if net_profit >= 0 else "적자"
    _profit_color  = "#2E7D32" if net_profit >= 0 else "#C62828"
    st.markdown(f"""
    <div style="background:white;border-radius:14px;padding:16px 22px;
      box-shadow:0 2px 12px rgba(0,0,0,0.07);margin:8px 0 16px;
      border-left:4px solid #FF5A5F;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
        <span style="background:#FFF0EE;color:#FF5A5F;font-size:12px;font-weight:700;
          padding:3px 10px;border-radius:20px;">📍 {d_name}</span>
        <span style="background:#F5F5F5;color:#484848;font-size:12px;font-weight:600;
          padding:3px 10px;border-radius:20px;">{ROOM_TYPE_ICONS.get(room_type,"")} {rt_name}</span>
        <span style="background:#F5F5F5;color:#767676;font-size:12px;
          padding:3px 10px;border-radius:20px;">실운영 {len(bench):,}개 기준</span>
        <span style="background:#FFF0EE;color:#FF5A5F;font-size:12px;font-weight:600;
          padding:3px 10px;border-radius:20px;">{host_badge}</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
        <div style="text-align:center;">
          <div style="font-size:11px;color:#888;margin-bottom:3px;">하루 실수익 (1박 요금×예약률)</div>
          <div style="font-size:20px;font-weight:700;color:#FF5A5F;">₩{int(my_revpar):,}</div>
          <div style="font-size:10px;color:{_diff_color};">{_diff_arrow} 지역 평균 대비 ₩{int(abs(_revpar_diff_s)):,}</div>
        </div>
        <div style="text-align:center;border-left:1px solid #F0F0F0;border-right:1px solid #F0F0F0;">
          <div style="font-size:11px;color:#888;margin-bottom:3px;">월 예상 순이익</div>
          <div style="font-size:20px;font-weight:700;color:{_profit_color};">₩{int(net_profit):,}</div>
          <div style="font-size:10px;color:{_profit_color};">{_profit_label}</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:11px;color:#888;margin-bottom:3px;">시장 유형</div>
          <div style="font-size:14px;font-weight:700;color:{c_info['color']};">{c_info['emoji']} {cluster_name}</div>
          <div style="font-size:10px;color:#888;">가격 탄력성 {abs(elasticity):.1f}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 탭 구성 ─────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if host_type == "existing":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 수익 요약", "💡 요금 전략", "📍 주변 관광지",
            "📋 운영 개선", "🏙️ 지역 진단", "🩺 헬스 스코어", "✍️ 숙소 설명"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 수익 요약", "💡 요금 추천", "📍 주변 관광지", "🏙️ 지역 진단", "✍️ 숙소 설명"
        ])
        tab6 = None

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
        kpi_card(k3, "적자 예방 최소 요금", f"₩{int(bep_adr):,}",
                 f"현재 요금 {'이상 — 흑자 ✅' if bep_ok else '이하 — 손실 위험 ❌'}",
                 "#2E7D32" if bep_ok else "#C62828")
        st.markdown(
            '<div style="font-size:11px;color:#BBB;text-align:right;margin-top:4px;">'
            '💡 적자 예방 최소 요금 = 운영비 + 수수료를 모두 커버하려면 1박에 최소 이 금액이 필요합니다</div>',
            unsafe_allow_html=True,
        )

        if host_type == "new":
            st.info(f"💡 신규 호스터는 실제 예약 데이터가 없어 지역 평균 예약률({b_occ:.0%})로 계산했습니다.")

        # ── 평일 / 주말 예약률 + 수익 비교 (기존 호스터) ────────────────────
        if host_type == "existing":
            wd_occ_pct = st.session_state.get("weekday_occ_pct", 0)
            we_occ_pct = st.session_state.get("weekend_occ_pct", 0)
            wd_booked_n = st.session_state.get("weekdays_booked", 0)
            we_booked_n = st.session_state.get("weekends_booked", 0)
            wd_total_n  = st.session_state.get("weekdays_total", 22)
            we_total_n  = st.session_state.get("weekends_total", 9)
            overall_pct = int(my_occ * 100)

            # 월 매출 분리
            wd_revenue_n = my_adr * wd_booked_n
            we_revenue_n = my_adr * we_booked_n
            # 하루 기대 수익 (RevPAR) = 요금 × 예약률
            wd_revpar_n = my_adr * (wd_occ_pct / 100)
            we_revpar_n = my_adr * (we_occ_pct / 100)
            # 색상 — 전체 대비 높으면 강조
            wd_col = "#2E7D32" if wd_occ_pct >= overall_pct else "#767676"
            we_col = "#FF5A5F" if we_occ_pct >= overall_pct else "#767676"

            # 예약률 3분할 카드
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px;">'
                f'<div style="background:white;border-radius:12px;padding:14px 8px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">전체 예약률</div>'
                f'<div style="font-size:22px;font-weight:700;color:#484848;">{overall_pct}%</div>'
                f'<div style="font-size:10px;color:#AAA;">지역 평균 {b_occ:.0%}</div>'
                f'</div>'
                f'<div style="background:white;border-radius:12px;padding:14px 8px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">📅 평일 예약률</div>'
                f'<div style="font-size:22px;font-weight:700;color:{wd_col};">{wd_occ_pct}%</div>'
                f'<div style="font-size:10px;color:#AAA;">{wd_booked_n}/{wd_total_n}일 (월~금)</div>'
                f'</div>'
                f'<div style="background:white;border-radius:12px;padding:14px 8px;text-align:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<div style="font-size:11px;color:#888;margin-bottom:4px;">🎉 주말 예약률</div>'
                f'<div style="font-size:22px;font-weight:700;color:{we_col};">{we_occ_pct}%</div>'
                f'<div style="font-size:10px;color:#AAA;">{we_booked_n}/{we_total_n}일 (토~일)</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # 평일 / 주말 수익 비교 카드
            we_higher = we_revpar_n >= wd_revpar_n
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">'
                f'<div style="background:{"#F7F9FF" if not we_higher else "white"};border-radius:12px;'
                f'padding:16px 14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);'
                f'border:{"2px solid #E3F0FF" if not we_higher else "1px solid #F0F0F0"};">'
                f'<div style="font-size:12px;font-weight:700;color:#484848;margin-bottom:10px;">📅 평일 수익</div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #F5F5F5;">'
                f'<span style="font-size:12px;color:#888;">하루 기대 수익</span>'
                f'<span style="font-size:12px;font-weight:600;color:{wd_col};">₩{int(wd_revpar_n):,}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;">'
                f'<span style="font-size:12px;color:#888;">이달 평일 매출</span>'
                f'<span style="font-size:12px;font-weight:600;color:#484848;">₩{int(wd_revenue_n):,}</span></div>'
                f'</div>'
                f'<div style="background:{"#FFF8F8" if we_higher else "white"};border-radius:12px;'
                f'padding:16px 14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);'
                f'border:{"2px solid #FFCDD2" if we_higher else "1px solid #F0F0F0"};">'
                f'<div style="font-size:12px;font-weight:700;color:#484848;margin-bottom:10px;">🎉 주말 수익</div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #F5F5F5;">'
                f'<span style="font-size:12px;color:#888;">하루 기대 수익</span>'
                f'<span style="font-size:12px;font-weight:600;color:{we_col};">₩{int(we_revpar_n):,}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;">'
                f'<span style="font-size:12px;color:#888;">이달 주말 매출</span>'
                f'<span style="font-size:12px;font-weight:600;color:#484848;">₩{int(we_revenue_n):,}</span></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # 한 줄 인사이트
            if we_booked_n > 0 and wd_booked_n > 0:
                diff_pct = abs(we_revpar_n - wd_revpar_n) / max(wd_revpar_n, 1) * 100
                if we_revpar_n > wd_revpar_n:
                    insight = f"주말 하루 수익이 평일보다 {diff_pct:.0f}% 높습니다. 주말 요금 인상을 검토해보세요."
                    i_color = "#FF5A5F"
                else:
                    insight = f"평일 하루 수익이 주말보다 {diff_pct:.0f}% 높습니다. 평일 예약 확보 전략이 효과적입니다."
                    i_color = "#2E7D32"
                st.markdown(
                    f'<div style="background:#FAFAFA;border-radius:10px;padding:10px 14px;'
                    f'margin-top:8px;border-left:3px solid {i_color};">'
                    f'<span style="font-size:12px;color:#484848;">💬 {insight}</span></div>',
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

        # ── AI 시장 예측 섹션 ────────────────────────────────────────────────
        if _ml_ok:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            section_title(
                "🤖 AI 시장 예측",
                "서울 실운영 14,399개 리스팅을 학습한 AI 모델 기반 시장 적정값입니다.",
            )
            mc1, mc2, mc3 = st.columns(3)

            adr_diff   = _ml["ADR_pred"]   - my_adr
            occ_diff   = _ml["Occ_pred"]   - my_occ
            revp_diff  = _ml["RevPAR_pred"] - my_revpar

            kpi_card(mc1, "AI 추천 1박 요금",
                     f"₩{int(_ml['ADR_pred']):,}",
                     f"{'▲' if adr_diff >= 0 else '▼'} 내 요금 대비 ₩{int(abs(adr_diff)):,}",
                     "#2E7D32" if adr_diff >= 0 else "#C62828")
            kpi_card(mc2, "AI 예측 예약률",
                     f"{_ml['Occ_pred']:.1%}",
                     f"{'▲' if occ_diff >= 0 else '▼'} 내 예약률 대비 {abs(occ_diff)*100:.1f}%p",
                     "#2E7D32" if occ_diff >= 0 else "#C62828")
            kpi_card(mc3, "AI 예측 하루 실수익",
                     f"₩{int(_ml['RevPAR_pred']):,}",
                     f"{'▲' if revp_diff >= 0 else '▼'} 현재 대비 ₩{int(abs(revp_diff)):,}",
                     "#2E7D32" if revp_diff >= 0 else "#C62828")

            # 월 수익 + 순이익 (AI 기준)
            ml_net = _ml["net_profit"]
            ml_net_color = "#2E7D32" if ml_net >= 0 else "#C62828"
            st.markdown(
                f'<div style="background:#F9F9F9;border-radius:12px;padding:14px 20px;'
                f'margin-top:10px;display:flex;gap:28px;flex-wrap:wrap;">'
                f'<span style="font-size:13px;color:#767676;">AI 기준 월 예상 수익: '
                f'<b style="color:#484848;">₩{int(_ml["monthly_revenue"]):,}</b></span>'
                f'<span style="font-size:13px;color:#767676;">AI 기준 월 순이익: '
                f'<b style="color:{ml_net_color};">₩{int(ml_net):,}</b></span>'
                f'<span style="font-size:11px;color:#AAAAAA;align-self:center;">'
                f'운영비 ₩{int(total_opex):,} 반영</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

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

    # ── 숙소 설명 탭 렌더링 함수 ────────────────────────────────────────────
    def _render_description_tab():
        _room_style = st.session_state.get("my_room_style", "모던/미니멀")
        _guests   = int(st.session_state.my_guests   or 2)
        _bedrooms = int(st.session_state.my_bedrooms or 1)
        _baths    = float(st.session_state.my_baths_count or 1)
        _beds     = int(st.session_state.my_beds or 1)

        section_title(
            "✍️ 숙소 설명 생성",
            "내 숙소 유형에 맞는 설명 템플릿입니다. [직접 입력] 부분을 채워 완성하세요.",
        )

        _style_adj = {
            "모던/미니멀": "깔끔하고 심플한 모던",
            "빈티지/레트로": "감성적인 빈티지",
            "한옥/전통": "한국 전통 감성이 살아있는",
            "아늑/가정적": "따뜻하고 아늑한",
            "럭셔리/프리미엄": "고급스러운 프리미엄",
        }.get(_room_style, "세련된")

        if room_type == "entire_home":
            _privacy = "숙소 전체를 단독으로 사용하실 수 있어 프라이빗한 공간이 필요하신 분께 적합합니다."
            _space   = f"침실 {_bedrooms}개, 욕실 {int(_baths)}개로 구성된 집 전체입니다."
            _intro   = f"{_style_adj} 감성의 {d_name} 집 전체를 단독으로 즐겨보세요."
        elif room_type == "private_room":
            _privacy = "침실은 단독으로 사용하시고, 거실·주방·욕실은 다른 게스트와 함께 이용합니다."
            _space   = "개인 침실을 단독으로 이용하시며, 그 외 공간은 공용입니다."
            _intro   = f"{_style_adj} 분위기의 {d_name} 개인실에서 편안하게 머무르세요."
        elif room_type == "hotel_room":
            _privacy = "호텔 수준의 서비스와 편의시설을 갖춘 독립 객실입니다."
            _space   = "객실 내 침실과 욕실이 완비되어 있습니다."
            _intro   = f"{d_name}에 위치한 {_style_adj} 호텔 스타일 객실입니다."
        else:
            _privacy = "합리적인 가격으로 서울을 여행하시는 분께 적합한 다인실입니다."
            _space   = "침대와 기본 수납공간이 제공됩니다."
            _intro   = f"{d_name}의 {_style_adj} 다인실에서 새로운 여행자들을 만나보세요."

        template = f"""◼ 숙소 소개
{_intro} [가까운 지하철역 또는 주요 명소 — 직접 입력: 예) 홍대입구역 도보 5분 거리에 위치하여] 서울 주요 지역으로의 이동이 편리합니다.
{_privacy}

[숙소만의 특별한 포인트 — 직접 입력: 예) 통창으로 들어오는 자연광, 루프탑 테라스, 한강 뷰 등]

◼ 숙소 구성
최대 {_guests}명 이용 가능 · {_space}

침실에는 [침대 종류 — 직접 입력: 예) 킹사이즈 침대 / 더블베드 / 싱글 침대 {_beds}개]이 갖춰져 있으며, [주요 가전·가구 — 직접 입력: 예) 에어컨, 난방, TV, 냉장고, 전자레인지, 세탁기, 드레스룸]가 제공됩니다.

◼ 기본 제공 어메니티
[직접 입력: 예) 수건, 헤어드라이기, 샴푸, 컨디셔너, 바디워시, 핸드워시, 비누, 티슈, 슬리퍼]가 기본으로 제공됩니다.
[별도 준비 필요 항목 — 직접 입력: 예) 칫솔·치약은 개별적으로 준비해주시기 바랍니다.]

◼ 체크인 / 체크아웃
체크인: [직접 입력: 예) 15:00 이후] / 체크아웃: [직접 입력: 예) 11:00 이전]
[입실 방법 — 직접 입력: 예) 도어락으로 키 없이 입실 가능합니다. 예약 확정 후 비밀번호를 안내드립니다.]

◼ 주의사항
[직접 입력: 예) 금연 / 반려동물 동반 불가 / 파티·행사 불가 / 층간소음 주의 / 쓰레기 분리수거 안내]"""

        st.markdown(
            '<div style="background:#FFF9F7;border:1.5px solid #FFD0CF;border-radius:12px;'
            'padding:14px 18px;margin-bottom:14px;font-size:13px;color:#484848;line-height:1.7;">'
            '💡 <b>사용 방법</b>: 아래 텍스트를 복사해 에어비앤비 숙소 설명란에 붙여넣은 뒤, '
            '<span style="color:#FF5A5F;font-weight:700;">[직접 입력]</span> 부분을 '
            '내 숙소 상황에 맞게 직접 수정해주세요. '
            '가구·가전·어메니티는 실제 보유 여부를 확인 후 작성해야 합니다.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.text_area(
            "숙소 설명 템플릿 (복사 후 수정하여 사용)",
            value=template,
            height=430,
            key="desc_template_area",
        )

        coral_box(
            '<div style="font-size:13px;line-height:1.8;">'
            '📌 <b>설명 작성 꿀팁</b><br>'
            '• <b>첫 문장</b>이 검색 결과 미리보기로 노출됩니다. 가장 매력적인 포인트를 먼저 쓰세요.<br>'
            '• <b>지하철역·버스 정류장</b> 이름과 도보 시간을 구체적으로 명시하면 예약률이 높아집니다.<br>'
            '• <b>어메니티 목록</b>은 구체적일수록 좋습니다. 없는 항목을 적으면 나중에 분쟁 원인이 됩니다.<br>'
            '• <b>주의사항</b>은 명확하게 적어야 불필요한 환불 요청을 예방할 수 있습니다.'
            '</div>'
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

        with tab7:
            _render_description_tab()

        # ── TAB 6: 헬스 스코어 (기존 호스터) ────────────────────────────────
        with tab6:
            section_title(
                "🩺 숙소 운영 건강 점수",
                f"동일 클러스터({cluster_name}) 내 Active+Operating 숙소 {len(_cluster_listings):,}개와 비교한 5가지 운영 건강 지표입니다.",
            )
            if _hs_ok:
                grade_colors = {
                    "A": "#2E7D32", "B": "#00A699",
                    "C": "#FFB400", "D": "#FF8C00", "F": "#C62828",
                }
                gc = grade_colors.get(_hs["grade"], "#767676")

                hs_c1, hs_c2 = st.columns([1, 2])
                with hs_c1:
                    st.markdown(
                        f'<div style="background:{gc}18;border:2.5px solid {gc};border-radius:16px;'
                        f'padding:32px 20px;text-align:center;">'
                        f'<div style="font-size:14px;color:#888;margin-bottom:8px;font-weight:600;">종합 점수</div>'
                        f'<div style="font-size:64px;font-weight:800;color:{gc};line-height:1;">{int(_hs["composite"])}</div>'
                        f'<div style="font-size:14px;color:#767676;margin-top:4px;">/ 100</div>'
                        f'<div style="background:{gc};color:white;border-radius:50%;width:52px;height:52px;'
                        f'display:inline-flex;align-items:center;justify-content:center;'
                        f'font-size:24px;font-weight:800;margin-top:14px;">{_hs["grade"]}</div>'
                        f'<div style="font-size:11px;color:#767676;margin-top:10px;">클러스터 내 백분위 기준</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with hs_c2:
                    comp_labels = {
                        "review_signal":   ("리뷰 신호",   "리뷰 수 & 평점 백분위"),
                        "listing_quality": ("사진 품질",   "최적 23~35장 기준"),
                        "booking_policy":  ("예약 정책",   "즉시예약·최소박·추가요금"),
                        "location":        ("위치",        "POI 거리 (가까울수록 높음)"),
                        "listing_config":  ("숙소 구성",   "침실·욕실 수 백분위"),
                    }
                    bar_html = ""
                    for key, (label, hint) in comp_labels.items():
                        v = _hs["components"][key]
                        color = "#2E7D32" if v >= 70 else "#FFB400" if v >= 40 else "#C62828"
                        bar_html += (
                            f'<div style="margin-bottom:14px;">'
                            f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">'
                            f'<div><span style="font-size:14px;font-weight:600;color:#484848;">{label}</span>'
                            f'<span style="font-size:11px;color:#AAA;margin-left:6px;">{hint}</span></div>'
                            f'<span style="font-size:14px;font-weight:700;color:{color};">{int(v)}/100</span></div>'
                            f'<div style="background:#EBEBEB;border-radius:6px;height:10px;">'
                            f'<div style="background:{color};width:{v:.0f}%;height:10px;border-radius:6px;'
                            f'transition:width 0.3s;"></div></div></div>'
                        )
                    st.markdown(bar_html, unsafe_allow_html=True)

                # 개선 액션 (full width)
                if _hs["actions"] and not _hs["actions"][0].startswith("✅"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    actions_html = (
                        '<div style="background:#FFF5F5;border:1.5px solid #FFCDD2;'
                        'border-radius:12px;padding:16px 18px;">'
                        '<div style="font-size:13px;font-weight:700;color:#C62828;margin-bottom:10px;">'
                        '🎯 지금 개선하면 점수가 올라가요</div>'
                    )
                    for a in _hs["actions"]:
                        actions_html += (
                            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;">'
                            f'<span style="font-size:13px;color:#484848;">{a}</span></div>'
                        )
                    actions_html += "</div>"
                    st.markdown(actions_html, unsafe_allow_html=True)
                else:
                    st.success("🎉 모든 운영 지표가 클러스터 상위권입니다! 현재 상태를 유지하세요.")
            else:
                st.warning("헬스 스코어 계산 중 오류가 발생했습니다.")

    else:
        _render_market_tab(tab4)
        with tab5:
            _render_description_tab()

    # ── 다시 시작 ────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        st.markdown('<div class="nav-primary">', unsafe_allow_html=True)
        if st.button("🔄 처음부터 다시 입력하기", key="restart", use_container_width=True, type="primary"):
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
