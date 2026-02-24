import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

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

# ── Airbnb 스타일 CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* 배경 */
  .stApp { background-color: #FFF9F7; }

  /* 메인 컨테이너 */
  .block-container {
    max-width: 860px !important;
    padding: 1.5rem 2rem 3rem !important;
  }

  /* 사이드바 숨기기 */
  [data-testid="stSidebar"] { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }

  /* 버튼 — 기본(primary) */
  .stButton > button {
    background-color: #FF5A5F !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
  }
  .stButton > button:hover {
    background-color: #E8484D !important;
  }

  /* 뒤로가기 버튼 덮어쓰기 — key="back_*" 버튼만 적용 불가하므로 주변 div로 */
  .back-btn .stButton > button {
    background-color: white !important;
    color: #484848 !important;
    border: 1.5px solid #DDDDDD !important;
  }
  .back-btn .stButton > button:hover {
    background-color: #F7F7F7 !important;
  }

  /* 카드 공통 */
  .card {
    background: white;
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 14px;
  }

  /* 구분선 */
  .section-divider {
    border: none;
    border-top: 1.5px solid #F0F0F0;
    margin: 28px 0;
  }

  /* 숫자 하이라이트 */
  .big-num { font-size: 30px; font-weight: 700; color: #FF5A5F; }

  /* 숨기기 */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }

  /* selectbox, number_input 테두리 radius */
  .stSelectbox > div > div,
  .stNumberInput > div > div > input {
    border-radius: 8px !important;
  }

  /* 체크박스 간격 */
  .stCheckbox { margin-bottom: 4px; }
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
    "entire_home": "집 전체",
    "private_room": "개인실",
    "hotel_room": "호텔 객실",
    "shared_room": "다인실",
}
ROOM_TYPE_DESC = {
    "entire_home": "숙소 전체를 단독으로 사용하는 형태",
    "private_room": "침실은 개인 공간, 거실·주방은 공용",
    "hotel_room": "호텔 스타일 객실",
    "shared_room": "다른 게스트와 공간을 함께 사용",
}

CLUSTER_INFO = {
    "프리미엄 관광거점": {
        "emoji": "🏆", "color": "#FF5A5F",
        "elasticity": -0.7,
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
        "emoji": "📈", "color": "#00A699",
        "elasticity": -0.8,
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
        "emoji": "⚖️", "color": "#FFB400",
        "elasticity": -1.1,
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
        "emoji": "🛡️", "color": "#9C27B0",
        "elasticity": -1.5,
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

POI_TYPES = ["관광지", "문화시설", "쇼핑", "음식점", "숙박", "레포츠", "여행코스"]

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

df, cluster_df = load_data()
active_df = df[
    (df["refined_status"] == "Active") & (df["operation_status"] == "Operating")
].copy()

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
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
    """district 영문 → 한국어"""
    return DISTRICT_KR.get(district, district)

# ── session_state 초기화 ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "district": "Mapo-gu",
        "room_type": "entire_home",
        "my_adr": None,
        "my_occ_pct": None,
        "opex_elec": 80000,
        "opex_water": 30000,
        "opex_mgmt": 150000,
        "opex_net": 30000,
        "opex_clean": 200000,
        "opex_loan": 0,
        "opex_etc": 50000,
        "my_photos": None,
        "my_superhost": False,
        "my_instant": False,
        "my_extra_fee": False,
        "my_min_nights": None,
        "my_rating": None,
        "my_reviews": None,
        "my_poi_dist": None,
        "my_500m": None,
        "my_poi_type": "관광지",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── 공통 UI 컴포넌트 ─────────────────────────────────────────────────────────
def render_logo():
    st.markdown("""
    <div style="text-align:center;padding:24px 0 6px;">
      <div style="font-size:36px;">🏠</div>
      <h2 style="color:#FF5A5F;margin:6px 0 2px;font-weight:800;letter-spacing:-0.5px;">
        에어비앤비 수익 최적화
      </h2>
      <p style="color:#888;font-size:13px;margin:0;">
        서울 실운영 숙소 14,399개 데이터 기반 · 내 숙소 맞춤 분석
      </p>
    </div>
    """, unsafe_allow_html=True)

def render_progress(current):
    labels = ["숙소 정보", "요금 현황", "월 운영비", "운영 체크"]
    html = '<div style="display:flex;align-items:flex-start;justify-content:center;gap:0;margin:20px 0 32px;">'
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
        html += '<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
        html += (
            f'<div style="display:flex;align-items:center;width:100%;">'
            f'<div style="flex:1;height:2px;background:{"transparent" if i==1 else line_color};"></div>'
            f'<div style="width:32px;height:32px;border-radius:50%;background:{circle_bg};'
            f'color:{circle_color};display:flex;align-items:center;justify-content:center;'
            f'font-size:13px;font-weight:700;flex-shrink:0;">{circle_content}</div>'
            f'<div style="flex:1;height:2px;background:{"transparent" if i==4 else "#EBEBEB"};"></div>'
            f'</div>'
        )
        html += f'<div style="font-size:11px;color:{label_color};margin-top:5px;font-weight:{"600" if i==current else "400"};">{label}</div>'
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def section_title(title, subtitle=""):
    sub = f'<p style="color:#888;font-size:13px;margin:4px 0 16px;">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<h3 style="color:#484848;margin:0 0 4px;font-weight:700;">{title}</h3>{sub}', unsafe_allow_html=True)

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

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — 내 숙소 정보
# ═══════════════════════════════════════════════════════════════════════════════
def step1():
    render_logo()
    render_progress(1)
    section_title("1단계: 내 숙소 기본 정보", "내 숙소의 위치와 종류를 선택해주세요.")

    col1, col2 = st.columns(2)

    with col1:
        districts = sorted(df["district"].dropna().unique())
        options = [f"{DISTRICT_KR.get(d, d)}" for d in districts]
        default_idx = districts.index("Mapo-gu") if "Mapo-gu" in districts else 0
        sel_idx = st.selectbox("📍 자치구", options, index=default_idx)
        st.session_state.district = districts[options.index(sel_idx)]

        # 선택 구 미리보기
        bench = get_bench(st.session_state.district, st.session_state.room_type)
        if len(bench) > 0:
            med = bench_val(bench, "ttm_revpar", 40000)
            coral_box(
                f'<span style="font-size:12px;color:#888;">이 지역 실운영 숙소 평균 하루 수익</span><br>'
                f'<span style="font-size:22px;font-weight:700;color:#FF5A5F;">₩{int(med):,}</span>'
                f'<span style="font-size:12px;color:#888;"> / 박 기준 ({len(bench):,}개 숙소)</span>'
            )

    with col2:
        st.markdown("**🏠 숙소 종류**")
        room_types = sorted(df["room_type"].dropna().unique())
        for rt in room_types:
            selected = st.session_state.room_type == rt
            check = "✓  " if selected else ""
            label = f"{check}{ROOM_TYPE_KR.get(rt, rt)} — {ROOM_TYPE_DESC.get(rt, '')}"
            if st.button(label, key=f"rt_{rt}", use_container_width=True):
                st.session_state.room_type = rt
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("다음 단계 →", key="next1", use_container_width=True):
        st.session_state.step = 2
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — 요금 & 예약률
# ═══════════════════════════════════════════════════════════════════════════════
def step2():
    render_logo()
    render_progress(2)
    section_title(
        "2단계: 내 숙소 요금 & 예약률",
        "현재 1박 요금과 예약률을 입력해주세요. 에어비앤비 앱 → 인사이트에서 확인할 수 있어요.",
    )

    bench = get_bench(st.session_state.district, st.session_state.room_type)
    b_adr = bench_val(bench, "ttm_avg_rate", 100000)
    b_occ = bench_val(bench, "ttm_occupancy", 0.40)

    # 지역 평균 참고 박스
    d_name = dn(st.session_state.district)
    rt_name = ROOM_TYPE_KR.get(st.session_state.room_type, "")
    st.markdown(
        f'<div style="background:#F7F7F7;border-radius:10px;padding:14px 18px;margin-bottom:16px;">'
        f'<span style="font-size:13px;font-weight:600;color:#484848;">'
        f'📊 {d_name} {rt_name} — 지역 평균 참고값</span><br>'
        f'<span style="font-size:13px;color:#767676;">'
        f'평균 1박 요금 <b>₩{int(b_adr):,}</b> &nbsp;|&nbsp; 평균 예약률 <b>{b_occ:.0%}</b>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        default_adr = int(st.session_state.my_adr) if st.session_state.my_adr else int(b_adr)
        my_adr = st.number_input(
            "💰 현재 1박 요금 (원)",
            min_value=0, max_value=2_000_000,
            value=default_adr, step=5_000,
            help="에어비앤비에 설정한 기본 1박 요금을 입력하세요",
        )
        st.session_state.my_adr = my_adr

    with col2:
        default_occ = int(st.session_state.my_occ_pct) if st.session_state.my_occ_pct else int(b_occ * 100)
        my_occ_pct = st.slider(
            "📅 한 달 예약률 (%)",
            0, 100, default_occ,
            help="한 달 30일 중 실제 예약이 들어온 날의 비율입니다",
        )
        st.session_state.my_occ_pct = my_occ_pct

    my_revpar = my_adr * (my_occ_pct / 100)
    coral_box(
        f'<div style="text-align:center;">'
        f'<span style="font-size:13px;color:#888;">내 하루 평균 실수익 (요금 × 예약률)</span><br>'
        f'<span class="big-num">₩{int(my_revpar):,}</span>'
        f'<span style="font-size:14px;color:#888;"> / 박</span>'
        f'</div>'
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back2", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        if st.button("다음 단계 →", key="next2", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — 월 운영비
# ═══════════════════════════════════════════════════════════════════════════════
def step3():
    render_logo()
    render_progress(3)
    section_title(
        "3단계: 월 운영비 입력",
        "숙소를 운영하는 데 매달 고정으로 나가는 비용을 입력해주세요. 본전 요금 계산에 사용됩니다.",
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

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back3", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        if st.button("다음 단계 →", key="next3", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — 운영 현황 체크
# ═══════════════════════════════════════════════════════════════════════════════
def step4():
    render_logo()
    render_progress(4)
    section_title(
        "4단계: 운영 현황 체크",
        "현재 숙소 운영 상태를 체크해주세요. 개선 포인트를 정확히 찾는 데 사용됩니다.",
    )

    bench = get_bench(st.session_state.district, st.session_state.room_type)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**⭐ 리뷰 & 평점**")
        default_rv = int(st.session_state.my_reviews) if st.session_state.my_reviews is not None else int(bench_val(bench, "num_reviews", 20))
        my_reviews = st.number_input("현재 리뷰 수 (건)", 0, 5000, default_rv, help="에어비앤비 앱에서 확인한 총 리뷰 수")
        st.session_state.my_reviews = my_reviews

        default_rt = float(st.session_state.my_rating) if st.session_state.my_rating is not None else round(bench_val(bench, "rating_overall", 4.70), 1)
        my_rating = st.slider("현재 평점", 0.0, 5.0, default_rt, 0.1)
        st.session_state.my_rating = my_rating

        st.markdown("**🏅 배지 & 예약 설정**")
        my_superhost = st.checkbox(
            "슈퍼호스트 배지 있음",
            value=bool(st.session_state.my_superhost),
            help="에어비앤비에서 슈퍼호스트 배지를 보유하고 있으면 체크",
        )
        st.session_state.my_superhost = my_superhost

        my_instant = st.checkbox(
            "즉시예약 켜져 있음",
            value=bool(st.session_state.my_instant),
            help="게스트가 호스트 승인 없이 바로 예약할 수 있는 기능",
        )
        st.session_state.my_instant = my_instant

        my_extra_fee = st.checkbox(
            "추가 게스트 요금 받고 있음",
            value=bool(st.session_state.my_extra_fee),
            help="기본 인원 초과 시 1인당 추가 요금을 받는 설정",
        )
        st.session_state.my_extra_fee = my_extra_fee

    with col2:
        st.markdown("**📸 사진 & 숙박 설정**")
        default_ph = int(st.session_state.my_photos) if st.session_state.my_photos is not None else int(bench_val(bench, "photos_count", 22))
        my_photos = st.number_input("등록된 사진 수 (장)", 0, 300, default_ph)
        st.session_state.my_photos = my_photos

        default_mn = int(st.session_state.my_min_nights) if st.session_state.my_min_nights is not None else int(bench_val(bench, "min_nights", 2))
        my_min_nights = st.number_input(
            "최소 숙박일 (박)",
            1, 365, default_mn,
            help="게스트가 예약할 수 있는 최소 숙박 기간",
        )
        st.session_state.my_min_nights = my_min_nights

        st.markdown("**📍 위치 정보**")
        default_poi = float(st.session_state.my_poi_dist) if st.session_state.my_poi_dist is not None else round(bench_val(bench, "nearest_poi_dist_km", 0.10), 2)
        my_poi_dist = st.number_input("가장 가까운 관광지까지 거리 (km)", 0.0, 5.0, default_poi, 0.01)
        st.session_state.my_poi_dist = my_poi_dist

        default_500 = int(st.session_state.my_500m) if st.session_state.my_500m is not None else int(bench_val(bench, "nearest_500m", 19))
        my_500m = st.number_input("도보 10분(500m) 이내 관광지 수", 0, 300, default_500)
        st.session_state.my_500m = my_500m

        poi_idx = POI_TYPES.index(st.session_state.my_poi_type) if st.session_state.my_poi_type in POI_TYPES else 0
        my_poi_type = st.selectbox("가장 가까운 관광지 유형", POI_TYPES, index=poi_idx)
        st.session_state.my_poi_type = my_poi_type

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 이전", key="back4", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        if st.button("🔍 분석 결과 보기", key="next4", use_container_width=True):
            st.session_state.step = 5
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — 결과 대시보드
# ═══════════════════════════════════════════════════════════════════════════════
def step5():
    # ── 값 수집 ─────────────────────────────────────────────────────────────
    district      = st.session_state.district
    room_type     = st.session_state.room_type
    my_adr        = float(st.session_state.my_adr or 100000)
    my_occ        = (st.session_state.my_occ_pct or 40) / 100
    my_photos     = int(st.session_state.my_photos or 20)
    my_superhost  = bool(st.session_state.my_superhost)
    my_instant    = bool(st.session_state.my_instant)
    my_extra_fee  = bool(st.session_state.my_extra_fee)
    my_min_nights = int(st.session_state.my_min_nights or 2)
    my_rating     = float(st.session_state.my_rating or 4.7)
    my_reviews    = int(st.session_state.my_reviews or 10)
    opex_items = {
        "전기세": st.session_state.opex_elec,
        "수도세": st.session_state.opex_water,
        "관리비": st.session_state.opex_mgmt,
        "인터넷": st.session_state.opex_net,
        "청소비": st.session_state.opex_clean,
        "대출이자": st.session_state.opex_loan,
        "기타": st.session_state.opex_etc,
    }
    total_opex = sum(opex_items.values())

    bench     = get_bench(district, room_type)
    b_adr     = bench_val(bench, "ttm_avg_rate", 100000)
    b_adr_p25 = bench_val(bench, "ttm_avg_rate", 70000, 25)
    b_adr_p75 = bench_val(bench, "ttm_avg_rate", 140000, 75)
    b_revpar  = bench_val(bench, "ttm_revpar", 40000)

    my_revpar       = my_adr * my_occ
    monthly_revenue = my_revpar * 30
    airbnb_fee      = monthly_revenue * 0.03
    net_profit      = monthly_revenue - airbnb_fee - total_opex
    bep_adr         = (total_opex / 0.97) / (30 * my_occ) if my_occ > 0 else 0

    d_row = cluster_df[cluster_df["district"] == district]
    cluster_name = d_row["cluster_name"].values[0] if len(d_row) > 0 else "중가 균형시장"
    c_info     = CLUSTER_INFO.get(cluster_name, CLUSTER_INFO["중가 균형시장"])
    elasticity = c_info["elasticity"]
    d_name     = dn(district)
    rt_name    = ROOM_TYPE_KR.get(room_type, room_type)

    # ── 헤더 ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;padding:24px 0 6px;">
      <div style="font-size:36px;">🏠</div>
      <h2 style="color:#FF5A5F;margin:6px 0 2px;font-weight:800;">분석 결과</h2>
      <p style="color:#888;font-size:13px;margin:0;">
        {d_name} · {rt_name} · 실운영 숙소 {len(bench):,}개 기준
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 섹션 A: 요약 지표 ───────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)

    revpar_diff  = my_revpar - b_revpar
    profit_color = "#2E7D32" if net_profit > 0 else "#C62828"
    bep_ok       = my_adr >= bep_adr

    def kpi_card(col, label, value, sub, sub_color="#767676"):
        col.markdown(
            f'<div style="background:white;border-radius:12px;padding:18px;text-align:center;'
            f'box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
            f'<div style="font-size:12px;color:#888;margin-bottom:6px;">{label}</div>'
            f'<div style="font-size:24px;font-weight:700;color:#484848;">{value}</div>'
            f'<div style="font-size:12px;color:{sub_color};margin-top:4px;">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    kpi_card(k1, "내 하루 평균 실수익", f"₩{int(my_revpar):,}",
             f"지역 평균 대비 {'▲' if revpar_diff >= 0 else '▼'}₩{int(abs(revpar_diff)):,}",
             "#2E7D32" if revpar_diff >= 0 else "#C62828")
    kpi_card(k2, "월 예상 순이익", f"₩{int(net_profit):,}",
             "흑자 ✅" if net_profit > 0 else "적자 ❌", profit_color)
    kpi_card(k3, "본전 요금 (손해 없는 최소 요금)", f"₩{int(bep_adr):,}",
             f"현재 요금 {'위 ✅' if bep_ok else '아래 ❌'}",
             "#2E7D32" if bep_ok else "#C62828")

    # ── 섹션 B: 적정 요금 추천 ──────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_title("💡 내 숙소에 맞는 적정 요금", "내 운영 단계에 따라 추천 요금 구간이 달라집니다.")

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
        bg     = scolor if is_me else "#F7F7F7"
        fc     = "white" if is_me else "#767676"
        border = f"3px solid {scolor}" if is_me else "2px solid #EBEBEB"
        me_tag = (f'<div style="margin-top:8px;"><span style="background:white;color:{scolor};'
                  f'padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;">▲ 내 단계</span></div>'
                  if is_me else "")
        col.markdown(
            f'<div style="border:{border};border-radius:12px;padding:18px;text-align:center;background:{bg};color:{fc};">'
            f'<div style="font-size:24px;">{sicon}</div>'
            f'<div style="font-weight:700;font-size:14px;margin:6px 0;">{sname} 호스트</div>'
            f'<div style="font-size:11px;opacity:0.85;margin-bottom:10px;">{scond}</div>'
            f'<div style="font-size:16px;font-weight:700;">{sprice}</div>'
            f'{me_tag}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if my_adr < rec_min:
        gap_msg, gap_icon, gap_bg = (f"현재 요금 ₩{int(my_adr):,}이 추천 구간보다 ₩{rec_min - int(my_adr):,} 낮습니다. 조금 올려도 괜찮습니다.", "⬆️", "#E3F2FD")
    elif my_adr > rec_max:
        gap_msg, gap_icon, gap_bg = (f"현재 요금 ₩{int(my_adr):,}이 추천 구간보다 ₩{int(my_adr) - rec_max:,} 높습니다. 예약률이 낮다면 조정을 고려하세요.", "⚠️", "#FFF8E1")
    else:
        gap_msg, gap_icon, gap_bg = ("현재 요금이 내 단계에 맞는 구간 안에 있습니다. 잘 하고 계세요!", "✅", "#E8F5E9")

    st.markdown(
        f'<div style="background:{gap_bg};border-left:4px solid {s_color};border-radius:10px;padding:16px 18px;">'
        f'<div style="font-weight:700;color:{s_color};margin-bottom:6px;">{s_icon} 내 단계: {stage} 호스트 — 추천 요금 ₩{rec_min:,} ~ ₩{rec_max:,}</div>'
        f'<div style="font-size:13px;color:#484848;">{gap_icon} {gap_msg}</div>'
        f'<div style="font-size:12px;color:#767676;margin-top:6px;">💬 {s_tip}</div>'
        f'<div style="font-size:11px;color:#AAAAAA;margin-top:8px;">'
        f'본전 요금 ₩{int(bep_adr):,} | 지역 하위25% ₩{int(b_adr_p25):,} | 지역 평균 ₩{int(b_adr):,} | 지역 상위25% ₩{int(b_adr_p75):,}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── 섹션 C: 월 손익 계산서 ──────────────────────────────────────────────
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
        profit_color2 = "#2E7D32" if net_profit >= 0 else "#C62828"
        html += (f'<div style="display:flex;justify-content:space-between;padding:12px 0 0;">'
                 f'<span style="font-weight:700;font-size:15px;">월 순이익</span>'
                 f'<span style="font-weight:700;font-size:18px;color:{profit_color2};">₩{int(net_profit):,}</span></div>')
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

        if net_profit > 0:
            st.success(f"✅ 월 ₩{int(net_profit):,} 흑자입니다.")
        elif net_profit == 0:
            st.warning("⚠️ 정확히 본전 상태입니다.")
        else:
            st.error(f"❌ 월 ₩{int(abs(net_profit)):,} 적자입니다. 요금 인상 또는 운영비 절감이 필요합니다.")

    with col_pie:
        nonzero = {k: v for k, v in opex_items.items() if v > 0}
        if nonzero and total_opex > 0:
            fig, ax = plt.subplots(figsize=(4.5, 4))
            colors = ["#FF5A5F", "#FF8A8D", "#FFB3B5", "#00A699", "#4DB6AC", "#FFB400", "#EBEBEB"]
            ax.pie(
                nonzero.values(), labels=nonzero.keys(),
                autopct="%1.0f%%", startangle=90,
                colors=colors[:len(nonzero)],
                textprops={"fontsize": 10},
                wedgeprops={"linewidth": 1, "edgecolor": "white"},
            )
            ax.set_title(f"월 운영비 구성 (총 ₩{total_opex:,})", fontsize=11)
            fig.patch.set_facecolor("#FAFAFA")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close()
        else:
            st.info("운영비를 입력하면 구성 차트가 표시됩니다.")

    # ── 섹션 D: 운영 체크리스트 ─────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_title("📋 지금 바로 개선할 수 있는 것들")

    checks = []

    if my_superhost:
        checks.append(("✅", "슈퍼호스트 달성", f"수익 +83% 프리미엄 유지 중", "done"))
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
        checks.append(("🔴", f"사진 {my_photos}장 (부족)", f"{20 - my_photos}장 추가 → 클릭률 상승 구간 진입", "todo"))
    else:
        checks.append(("🟡", f"사진 {my_photos}장 (많음)", "35장 초과 — 좋은 사진만 추려서 정리 권장", "quick"))

    if not my_extra_fee:
        checks.append(("✅", "추가 게스트 요금 없음", "요금에 포함 — 최적 구조", "done"))
    else:
        checks.append(("🔴", "추가 게스트 요금 있음",
            "없애고 1박 요금에 통합 → 수익 +25~56% 회복 가능", "quick"))

    if 2 <= my_min_nights <= 3:
        checks.append(("✅", f"최소 {my_min_nights}박 (최적)", "수익 최적 + 리뷰 축적 속도 최적", "done"))
    elif my_min_nights == 1:
        checks.append(("🟡", "최소 1박", "수익 효율 낮음 — 2박으로 변경 추천", "quick"))
    else:
        checks.append(("🟡", f"최소 {my_min_nights}박 (길음)", "리뷰 쌓는 속도 느림 — 2~3박으로 줄이기 검토", "quick"))

    if my_rating >= 4.8:
        checks.append(("✅", f"평점 {my_rating:.1f}", "슈퍼호스트 기준 충족 + 검색 상위 노출 구간", "done"))
    elif my_rating >= 4.5:
        checks.append(("🟡", f"평점 {my_rating:.1f}", "4.8 이상이면 슈퍼호스트 + 검색 부스트", "todo"))
    else:
        checks.append(("🔴", f"평점 {my_rating:.1f} (낮음)", "4.5 미만 — 검색 노출 불이익 구간", "todo"))

    if my_reviews >= 10:
        checks.append(("✅", f"리뷰 {my_reviews}건", "슈퍼호스트 최소 요건(10건) 충족", "done"))
    else:
        checks.append(("🔴", f"리뷰 {my_reviews}건",
            f"슈퍼호스트 최소 10건 필요 — {10 - my_reviews}건 더 받아야 합니다", "todo"))

    col_c1, col_c2 = st.columns(2)
    for i, (icon, title, desc, status) in enumerate(checks):
        col = col_c1 if i % 2 == 0 else col_c2
        bg_c = "#F1F8F4" if status == "done" else "#FFF8E1" if status == "quick" else "#FFF0EE"
        border_c = "#4CAF50" if status == "done" else "#FFB400" if status == "quick" else "#FF5A5F"
        col.markdown(
            f'<div style="background:{bg_c};border-left:3px solid {border_c};border-radius:8px;'
            f'padding:12px 14px;margin-bottom:8px;">'
            f'<span style="font-weight:600;font-size:14px;">{icon} {title}</span><br>'
            f'<span style="font-size:12px;color:#767676;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 즉시 실행 액션 TOP 3
    quick_list = [(icon, title, desc) for icon, title, desc, status in checks if status in ("quick", "todo")]
    if quick_list:
        st.markdown("#### 🎯 지금 당장 실행하면 효과 큰 TOP 3")
        for i, (icon, title, desc) in enumerate(quick_list[:3], 1):
            st.markdown(
                f'<div style="background:white;border:1.5px solid #FFE0DE;border-radius:10px;'
                f'padding:14px 16px;margin-bottom:8px;display:flex;align-items:flex-start;">'
                f'<span style="background:#FF5A5F;color:white;border-radius:50%;min-width:24px;height:24px;'
                f'display:inline-flex;align-items:center;justify-content:center;font-size:12px;'
                f'font-weight:700;margin-right:12px;">{i}</span>'
                f'<div><b style="font-size:14px;">{title}</b><br>'
                f'<span style="font-size:12px;color:#767676;">{desc}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("🎉 모든 운영 레버가 최적 상태입니다!")

    # ── 섹션 E: 요금 시뮬레이션 ────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_title(
        "📊 요금 변경 시뮬레이션",
        f"이 지역({cluster_name})은 요금을 10% 올리면 예약률이 약 {abs(elasticity)*10:.0f}% 변화합니다.",
    )

    delta_pct = st.slider("요금 변화율 (%)", -30, 50, 0, 5,
                          help="오른쪽: 요금 인상 / 왼쪽: 요금 인하")
    delta    = delta_pct / 100
    new_adr  = my_adr * (1 + delta)
    new_occ  = min(1.0, max(0.0, my_occ * (1 + elasticity * delta)))
    new_revp = new_adr * new_occ
    new_net  = new_revp * 30 * 0.97 - total_opex
    p_change = new_net - net_profit

    col_s1, col_s2 = st.columns(2)

    with col_s1:
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
            st.success(f"✅ 요금 인상 효과 있음 — 순이익 ₩{p_change:+,.0f} 증가")
        elif delta_pct > 0:
            st.error(f"❌ 요금 인상이 역효과 — 예약률 하락으로 순이익 ₩{abs(p_change):,.0f} 감소")
        elif p_change > 0:
            st.success(f"✅ 요금 인하로 예약률 상승 → 순이익 ₩{p_change:+,.0f} 증가")
        else:
            st.warning(f"⚠️ 요금 인하 시 순이익 ₩{abs(p_change):,.0f} 감소")

    with col_s2:
        x_range = np.linspace(-0.30, 0.50, 80)
        profits = [
            my_adr*(1+d) * min(1., max(0., my_occ*(1+elasticity*d))) * 30 * 0.97 - total_opex
            for d in x_range
        ]
        fig4, ax4 = plt.subplots(figsize=(5.5, 4))
        ax4.plot(x_range * 100, profits, color="#FF5A5F", linewidth=2.5)
        ax4.axhline(0, color="#767676", linestyle="--", lw=1.2, alpha=0.6, label="손익분기선")
        ax4.axvline(delta_pct, color="#FFB400", linestyle="--", lw=1.5, label=f"현재 ({delta_pct:+d}%)")
        ax4.scatter([delta_pct], [new_net], color="#FFB400", s=70, zorder=6)
        ax4.fill_between(x_range*100, profits, 0, where=[p > 0 for p in profits], alpha=0.07, color="#4CAF50")
        ax4.fill_between(x_range*100, profits, 0, where=[p <= 0 for p in profits], alpha=0.07, color="#FF5A5F")
        ax4.set_xlabel("요금 변화율 (%)")
        ax4.set_ylabel("월 순이익 (원)")
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"₩{y/10000:.0f}만"))
        ax4.legend(fontsize=8)
        ax4.spines["top"].set_visible(False)
        ax4.spines["right"].set_visible(False)
        ax4.set_facecolor("#FAFAFA")
        fig4.patch.set_facecolor("#FAFAFA")
        fig4.tight_layout()
        st.pyplot(fig4)
        plt.close()

        best_idx  = int(np.argmax(profits))
        best_adr  = my_adr * (1 + x_range[best_idx])
        best_prof = profits[best_idx]
        st.success(f"🎯 순이익 최대 요금: ₩{int(best_adr):,} ({x_range[best_idx]*100:+.0f}%) → 월 ₩{int(best_prof):,}")

    # ── 섹션 F: 지역 시장 진단 ──────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_title(
        f"{c_info['emoji']} {d_name} 시장 유형: {cluster_name}",
        c_info["desc"],
    )

    col_m1, col_m2 = st.columns([1, 1.4])

    with col_m1:
        st.markdown(
            f'<div style="background:{c_info["color"]}15;border:2px solid {c_info["color"]};'
            f'border-radius:12px;padding:20px;">'
            f'<div style="font-size:36px;">{c_info["emoji"]}</div>'
            f'<div style="font-weight:700;font-size:16px;color:{c_info["color"]};margin:8px 0;">{cluster_name}</div>'
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

    # ── 다시 시작 버튼 ───────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 처음부터 다시 입력하기", key="restart", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ── 푸터 ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:20px 0;color:#BBBBBB;font-size:12px;">
      서울 Airbnb 수익 최적화 · 데이터 기간: 2024-10 ~ 2025-09 · 32,061개 리스팅 기반
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 라우터
# ═══════════════════════════════════════════════════════════════════════════════
step = st.session_state.get("step", 1)
if step == 1:
    step1()
elif step == 2:
    step2()
elif step == 3:
    step3()
elif step == 4:
    step4()
else:
    step5()
