import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform
import warnings

warnings.filterwarnings('ignore')

# ── 페이지 설정 (반드시 첫 번째 st 명령) ─────────────────────────────────────
st.set_page_config(
    page_title="서울 Airbnb RevPAR 최적화",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 한글 폰트 설정 ─────────────────────────────────────────────────────────────
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
else:
    plt.rc('font', family='NanumGothic')
plt.rc('axes', unicode_minus=False)

# ── CSS 스타일 ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin: 4px 0;
        border-left: 4px solid #667eea;
    }
    .grade-box {
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        color: white;
        margin-bottom: 12px;
    }
    .checklist-item {
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 (캐싱으로 1번만 읽음) ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data/raw/seoul_airbnb_cleaned.csv')
    cluster_df = pd.read_csv('data/processed/district_clustered.csv')
    # 군집 정보 병합
    df = df.merge(
        cluster_df[['district', 'cluster', 'cluster_name']],
        on='district', how='left'
    )
    return df, cluster_df

df, cluster_df = load_data()

# Active + Operating 서브셋 (벤치마크 모집단)
active_df = df[
    (df['refined_status'] == 'Active') &
    (df['operation_status'] == 'Operating')
].copy()

# ── 군집별 전략 정의 ───────────────────────────────────────────────────────────
CLUSTER_INFO = {
    '프리미엄 관광거점': {
        'emoji': '🏆',
        'color': '#FF6B35',
        'elasticity': -0.7,
        'tag': 'ADR 인상 여지 있음',
        'description': '외국인 관광객 수요가 높고 ADR 인상 여지가 있는 시장입니다. 가격보다 퀄리티 차별화가 핵심입니다.',
        'strategy': [
            '💰 ADR 10~20% 인상 테스트 (수요 가격 탄력성 낮음)',
            '🌍 외국인 타겟 리스팅 영문 최적화',
            '⚡ 즉시예약(Instant Book) 반드시 활성화',
            '📸 사진 20~35장 + 주변 관광지 포함 촬영',
            '⭐ 슈퍼호스트 배지 우선 달성 후 ADR 프리미엄 적용',
        ],
    },
    '성장형 주거상권': {
        'emoji': '📈',
        'color': '#4CAF50',
        'elasticity': -0.8,
        'tag': 'RevPAR 프리미엄 구조',
        'description': '높은 RevPAR와 안정적 수요를 보유한 프리미엄 주거·상업 복합 시장입니다.',
        'strategy': [
            '💰 ADR 프리미엄 유지 — 가격 방어 전략',
            '⭐ 슈퍼호스트 + 게스트 선호 배지 달성 목표',
            '📝 리뷰 품질 관리 (평점 4.8+ 목표)',
            '🏠 Entire Home 전환 검토 (동일 구 Private Room 대비 2.7배 RevPAR)',
            '📍 관광지·문화시설 근접성 리스팅 제목에 명시',
        ],
    },
    '중가 균형시장': {
        'emoji': '⚖️',
        'color': '#2196F3',
        'elasticity': -1.1,
        'tag': '점유율 + ADR 균형 전략',
        'description': '공급과 수요가 균형을 이루는 안정적 시장입니다. 운영 최적화가 핵심입니다.',
        'strategy': [
            '📸 사진 최적화 (20~35장) — 점유율 방어 1순위',
            '📅 최소숙박 2~3박 설정 — 리뷰 축적 가속화',
            '⚡ 즉시예약 ON — 무료 점유율 레버',
            '💵 추가요금 제거 — ADR에 통합하여 총비용 투명화',
            '⭐ 슈퍼호스트 달성 후 ADR 소폭 인상 시도',
        ],
    },
    '가격민감 외곽형': {
        'emoji': '🛡️',
        'color': '#9C27B0',
        'elasticity': -1.5,
        'tag': '점유율 방어 최우선',
        'description': '가격 경쟁이 치열한 시장입니다. ADR 인상보다 점유율 유지가 최우선입니다.',
        'strategy': [
            '🛡️ 가격 인상 자제 — 점유율 방어가 RevPAR 보호',
            '📸 사진 수 확대로 클릭률 개선',
            '⭐ 슈퍼호스트 배지로 가격 외 차별화',
            '📅 최소숙박 단축 — 예약 가능 일정 확대',
            '💵 추가요금 제거로 총 비용 투명화 — 선택 유인 강화',
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# 사이드바 — 사용자 입력
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🏠 내 숙소 정보 입력")
    st.caption("입력값에 따라 우측 대시보드가 실시간으로 업데이트됩니다.")
    st.markdown("---")

    # ── 자치구 & 숙소 유형 ─────────────────────────────────────────────────────
    st.subheader("📍 숙소 위치 · 유형")

    ROOM_TYPE_KR = {
        'entire_home': '전체 숙소 (Entire Home)',
        'private_room': '개인실 (Private Room)',
        'hotel_room': '호텔 객실 (Hotel Room)',
        'shared_room': '다인실 (Shared Room)',
    }

    districts = sorted(df['district'].unique())
    selected_district = st.selectbox("자치구", districts, index=districts.index('Mapo-gu'))

    room_type_labels = [ROOM_TYPE_KR[r] for r in sorted(df['room_type'].unique())]
    room_type_values = sorted(df['room_type'].unique())
    selected_rt_label = st.selectbox("숙소 유형", room_type_labels)
    selected_room_type = room_type_values[room_type_labels.index(selected_rt_label)]

    # 벤치마크 계산 (동일 자치구 + 동일 유형 Active+Operating)
    bench = active_df[
        (active_df['district'] == selected_district) &
        (active_df['room_type'] == selected_room_type)
    ]

    def bench_val(col, default, pct=50):
        if len(bench) > 0 and col in bench.columns:
            return float(np.percentile(bench[col].dropna(), pct))
        return default

    bench_adr     = bench_val('ttm_avg_rate', 100000)
    bench_occ     = bench_val('ttm_occupancy', 0.40)
    bench_revpar  = bench_val('ttm_revpar', 40000)
    bench_photos  = bench_val('photos_count', 22)
    bench_reviews = bench_val('num_reviews', 20)
    bench_rating  = bench_val('rating_overall', 4.70)
    bench_minn    = bench_val('min_nights', 2)
    bench_poi     = bench_val('nearest_poi_dist_km', 0.10)
    bench_500m    = bench_val('nearest_500m', 19)

    st.caption(f"비교 기준: {selected_district} Active+Operating **{len(bench):,}건** 중위값")

    st.markdown("---")

    # ── 내 숙소 성과 ───────────────────────────────────────────────────────────
    st.subheader("📊 내 숙소 성과")

    my_adr = st.number_input(
        "현재 ADR — 평균 1박 요금 (원)",
        min_value=0, max_value=2_000_000,
        value=int(bench_adr), step=5_000, format="%d"
    )
    my_occ_pct = st.slider(
        "현재 점유율 (%)",
        min_value=0, max_value=100,
        value=int(bench_occ * 100)
    )
    my_occ = my_occ_pct / 100

    st.markdown("---")

    # ── 운영 설정 ──────────────────────────────────────────────────────────────
    st.subheader("⚙️ 운영 설정")

    my_photos      = st.number_input("등록 사진 수 (장)", 0, 300, int(bench_photos))
    my_superhost   = st.checkbox("슈퍼호스트 여부")
    my_instant     = st.checkbox("즉시예약(Instant Book) 활성화")
    my_extra_fee   = st.checkbox("추가 게스트 요금 설정 중")
    my_min_nights  = st.number_input("최소 숙박일 (박)", 1, 365, int(bench_minn))
    my_rating      = st.slider("평점", 0.0, 5.0, round(bench_rating, 1), 0.1)
    my_reviews     = st.number_input("리뷰 수 (건)", 0, 5000, int(bench_reviews))

    st.markdown("---")

    # ── 위치 정보 ──────────────────────────────────────────────────────────────
    st.subheader("📍 위치 정보")

    my_poi_dist = st.number_input(
        "가장 가까운 관광지까지 거리 (km)",
        0.0, 5.0, round(bench_poi, 2), 0.01
    )
    my_500m = st.number_input("반경 500m 이내 관광지 수", 0, 300, int(bench_500m))
    poi_types = ['관광지', '문화시설', '쇼핑', '음식점', '숙박', '축제공연행사', '레포츠', '여행코스']
    my_poi_type = st.selectbox("가장 가까운 관광지 유형", poi_types)

    st.markdown("---")

    # ── 월 운영비 (OPEX) ──────────────────────────────────────────────────────
    st.subheader("💸 월 운영비 (OPEX)")
    st.caption("숙소 운영에 매달 나가는 비용을 입력하세요.")

    opex_elec  = st.number_input("전기세 (원)",    0, 500_000,   80_000, 5_000)
    opex_water = st.number_input("수도세 (원)",    0, 200_000,   30_000, 5_000)
    opex_mgmt  = st.number_input("관리비 (원)",    0, 1_000_000, 150_000, 10_000)
    opex_net   = st.number_input("인터넷 (원)",    0, 100_000,   30_000, 5_000)
    opex_clean = st.number_input("청소비 (원)",    0, 1_000_000, 200_000, 10_000)
    opex_loan  = st.number_input("대출이자 (원)",  0, 5_000_000, 0,       50_000)
    opex_etc   = st.number_input("기타 (원)",      0, 500_000,   50_000, 10_000)

    total_opex = opex_elec + opex_water + opex_mgmt + opex_net + opex_clean + opex_loan + opex_etc

    st.markdown(f"**총 OPEX: ₩{total_opex:,}**")

# ══════════════════════════════════════════════════════════════════════════════
# 핵심 계산값
# ══════════════════════════════════════════════════════════════════════════════
my_revpar       = my_adr * my_occ
monthly_revenue = my_revpar * 30
airbnb_fee      = monthly_revenue * 0.03
net_profit      = monthly_revenue - airbnb_fee - total_opex
bep_adr         = (total_opex / 0.97) / (30 * my_occ) if my_occ > 0 else 0

# 군집 정보
d_cluster = cluster_df[cluster_df['district'] == selected_district]
cluster_name = d_cluster['cluster_name'].values[0] if len(d_cluster) > 0 else '중가 균형시장'
c_info       = CLUSTER_INFO.get(cluster_name, CLUSTER_INFO['중가 균형시장'])
elasticity   = c_info['elasticity']

# ══════════════════════════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════════════════════════
st.title("🏠 서울 Airbnb RevPAR 최적화 대시보드")
col_h1, col_h2, col_h3 = st.columns(3)
col_h1.metric("선택 자치구", selected_district)
col_h2.metric("숙소 유형", ROOM_TYPE_KR[selected_room_type].split(' ')[0])
col_h3.metric("비교 대상 (Active+Operating)", f"{len(bench):,}건")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 4개 탭
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🏙️ 1단계: 시장 진단",
    "💰 2단계: 수익 진단",
    "📋 3단계: 전략 체크리스트",
    "📊 4단계: 가격 시뮬레이션",
])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — 시장 유형 진단
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    st.header(f"{c_info['emoji']} 시장 유형: {cluster_name}")

    col1, col2 = st.columns([1, 1.4])

    with col1:
        # 시장 유형 카드
        st.markdown(
            f'<div class="grade-box" style="background:{c_info["color"]};">'
            f'<h2 style="margin:0;">{c_info["emoji"]} {cluster_name}</h2>'
            f'<p style="margin:8px 0 0;">{c_info["tag"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.info(c_info['description'])

        # 자치구 핵심 지표
        if len(d_cluster) > 0:
            row = d_cluster.iloc[0]
            m1, m2 = st.columns(2)
            m1.metric("자치구 중위 RevPAR", f"₩{int(row['median_revpar_ao']):,}")
            m2.metric("Dormant 비율", f"{row['dormant_ratio']:.1%}")
            m3, m4 = st.columns(2)
            m3.metric("공급 점유율", f"{row['supply_share']:.1%}")
            m4.metric("슈퍼호스트 비율", f"{row['superhost_rate']:.1%}")

    with col2:
        st.subheader("📌 이 시장에서 권장하는 전략")
        for s in c_info['strategy']:
            st.markdown(f"- {s}")

        # 4개 시장 중위 RevPAR 바차트
        st.markdown("---")
        st.subheader("서울 시장 유형별 중위 RevPAR 비교")
        summary = (
            cluster_df.groupby('cluster_name')['median_revpar_ao']
            .median()
            .reset_index()
            .sort_values('median_revpar_ao')
        )
        bar_colors = [
            c_info['color'] if c == cluster_name else '#D3D3D3'
            for c in summary['cluster_name']
        ]
        fig, ax = plt.subplots(figsize=(7, 3))
        bars = ax.barh(summary['cluster_name'], summary['median_revpar_ao'], color=bar_colors)
        for bar, val in zip(bars, summary['median_revpar_ao']):
            ax.text(
                bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f'₩{int(val):,}', va='center', fontsize=10
            )
        ax.set_xlabel('중위 RevPAR (원)')
        ax.set_xlim(0, summary['median_revpar_ao'].max() * 1.35)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='y', labelsize=10)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close()

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — 수익 진단
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("💰 현재 수익 구조 진단")

    # KPI 3개
    k1, k2, k3 = st.columns(3)
    k1.metric(
        "내 ADR",
        f"₩{my_adr:,}",
        delta=f"벤치마크 대비 ₩{my_adr - bench_adr:+,.0f}",
    )
    k2.metric(
        "내 점유율",
        f"{my_occ:.0%}",
        delta=f"벤치마크 대비 {(my_occ - bench_occ):+.0%}",
    )
    k3.metric(
        "내 RevPAR",
        f"₩{my_revpar:,.0f}",
        delta=f"벤치마크 대비 ₩{my_revpar - bench_revpar:+,.0f}",
    )

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        # ADR × 점유율 4분면
        st.subheader("📊 ADR × 점유율 포지셔닝")

        fig2, ax2 = plt.subplots(figsize=(6, 5))
        sample = bench.sample(min(300, len(bench)), random_state=42) if len(bench) > 0 else bench
        if len(sample) > 0:
            ax2.scatter(
                sample['ttm_occupancy'], sample['ttm_avg_rate'],
                alpha=0.25, color='steelblue', s=18, label='동일 구·유형 숙소'
            )
        # 내 숙소
        ax2.scatter(my_occ, my_adr, color='#FF4444', s=200, zorder=6,
                    marker='*', label='내 숙소')
        # 중위 기준선
        ax2.axvline(bench_occ, color='gray', linestyle='--', alpha=0.5, lw=1)
        ax2.axhline(bench_adr, color='gray', linestyle='--', alpha=0.5, lw=1)
        # 4분면 텍스트
        xmax = ax2.get_xlim()[1] if ax2.get_xlim()[1] > 0 else 1.0
        ymax = ax2.get_ylim()[1] if ax2.get_ylim()[1] > 0 else 200000
        ax2.text(0.01, bench_adr * 1.04, '저점유·고가', fontsize=8, color='gray')
        ax2.text(bench_occ + 0.01, bench_adr * 1.04, '고점유·고가 ✅', fontsize=8, color='green')
        ax2.text(0.01, bench_adr * 0.25, '저점유·저가', fontsize=8, color='gray')
        ax2.text(bench_occ + 0.01, bench_adr * 0.25, '고점유·저가', fontsize=8, color='gray')
        ax2.set_xlabel('점유율')
        ax2.set_ylabel('ADR (원)')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'₩{y/10000:.0f}만'))
        ax2.legend(fontsize=8)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close()

    with col_right:
        # 월 손익 계산서
        st.subheader("📋 월 손익 계산서")

        pnl = pd.DataFrame({
            '항목': ['월 매출 (RevPAR × 30일)', '에어비앤비 수수료 (3%)', '운영비 (OPEX)', '월 순이익'],
            '금액': [
                f'₩{monthly_revenue:,.0f}',
                f'-₩{airbnb_fee:,.0f}',
                f'-₩{total_opex:,}',
                f'₩{net_profit:,.0f}',
            ]
        }).set_index('항목')
        st.table(pnl)

        # BEP
        st.markdown("---")
        bep_delta = my_adr - bep_adr
        bep_icon = "🟢" if bep_delta >= 0 else "🔴"
        st.metric(
            f"{bep_icon} 손익분기 최소 ADR (BEP)",
            f"₩{bep_adr:,.0f}",
            delta=f"현재 ADR과 ₩{bep_delta:+,.0f} 차이",
            delta_color="normal" if bep_delta >= 0 else "inverse",
        )

        if net_profit > 0:
            st.success(f"✅ 월 **₩{net_profit:,.0f}** 순이익 발생 중")
        elif net_profit == 0:
            st.warning("⚠️ 정확히 손익분기점 상태입니다.")
        else:
            st.error(f"❌ 월 **₩{abs(net_profit):,.0f}** 적자 발생 중")

        # OPEX 파이차트
        st.markdown("---")
        st.subheader("💸 OPEX 구성")
        opex_items = {
            '전기세': opex_elec, '수도세': opex_water, '관리비': opex_mgmt,
            '인터넷': opex_net, '청소비': opex_clean, '대출이자': opex_loan, '기타': opex_etc
        }
        opex_nonzero = {k: v for k, v in opex_items.items() if v > 0}
        if opex_nonzero and total_opex > 0:
            fig3, ax3 = plt.subplots(figsize=(5, 4))
            ax3.pie(
                opex_nonzero.values(), labels=opex_nonzero.keys(),
                autopct='%1.1f%%', startangle=90,
                colors=plt.cm.Set2.colors[:len(opex_nonzero)]
            )
            ax3.set_title(f'총 OPEX: ₩{total_opex:,}', fontsize=11)
            fig3.tight_layout()
            st.pyplot(fig3)
            plt.close()
        else:
            st.caption("운영비를 입력하면 구성 차트가 표시됩니다.")

# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — 전략 체크리스트
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    st.header("📋 운영 레버 점검 — 지금 당장 바꿀 수 있는 것들")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚙️ 운영 설정 체크리스트")

        checks = []

        # 슈퍼호스트
        if my_superhost:
            checks.append(("✅", "슈퍼호스트", "이미 달성! RevPAR +83.1% 프리미엄 유지 중"))
        else:
            est = my_revpar * 1.831
            checks.append(("❌", "슈퍼호스트 미달성",
                f"달성 시 RevPAR ₩{my_revpar:,.0f} → ₩{est:,.0f} 잠재"))

        # 즉시예약
        if my_instant:
            checks.append(("✅", "즉시예약 활성화", "점유율 최대화 레버 작동 중"))
        else:
            checks.append(("⚠️", "즉시예약 비활성화", "Instant Book ON → 점유율 +5~10% 효과 (설정 1분)"))

        # 사진 수
        if 20 <= my_photos <= 35:
            checks.append(("✅", f"사진 {my_photos}장 (최적)", "최적 구간(20~35장) — 클릭률 최대화 유지 중"))
        elif my_photos < 20:
            checks.append(("❌", f"사진 {my_photos}장 (부족)", f"{20 - my_photos}장 추가 필요 → 점유율 상승 구간 진입"))
        else:
            checks.append(("⚠️", f"사진 {my_photos}장 (과다)", "35장 초과 시 한계효용 체감 — 품질 점검 권장"))

        # 추가요금
        if not my_extra_fee:
            checks.append(("✅", "추가 게스트 요금 없음", "ADR에 통합 — RevPAR 최적 구조"))
        else:
            checks.append(("❌", "추가 게스트 요금 설정 중",
                f"제거 시 RevPAR +25~56% 회복 가능 (1~6인: -25%, 7인+: -56%)"))

        # 최소숙박
        if 2 <= my_min_nights <= 3:
            checks.append(("✅", f"최소숙박 {my_min_nights}박 (최적)", "RevPAR 최적 구간 + 리뷰 축적 속도 최적"))
        elif my_min_nights == 1:
            checks.append(("⚠️", "최소숙박 1박", "점유율은 높으나 RevPAR 효율 낮음 — 2박 시도 권장"))
        else:
            checks.append(("⚠️", f"최소숙박 {my_min_nights}박",
                f"리뷰 축적 속도 저하 → 2~3박 단축 검토"))

        # 평점
        if my_rating >= 4.8:
            checks.append(("✅", f"평점 {my_rating:.1f}", "슈퍼호스트 기준 충족 + 검색 최상위 노출 구간"))
        elif my_rating >= 4.5:
            checks.append(("⚠️", f"평점 {my_rating:.1f}", "4.8+ 달성 시 슈퍼호스트 기준 충족 + 검색 부스트"))
        else:
            checks.append(("❌", f"평점 {my_rating:.1f} (임계점 미달)", "4.5 미만 → 검색 노출 불이익 구간"))

        # 리뷰 수
        if my_reviews >= 10:
            checks.append(("✅", f"리뷰 {my_reviews}건", "슈퍼호스트 최소 요건 충족"))
        else:
            checks.append(("❌", f"리뷰 {my_reviews}건",
                f"{10 - my_reviews}건 더 필요 → 슈퍼호스트 최소 요건 미달"))

        # 체크리스트 출력
        for icon, title, desc in checks:
            with st.container():
                st.markdown(f"**{icon} {title}**")
                st.caption(f"　{desc}")
                st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

    with col2:
        # 위치 프리미엄 등급
        st.subheader("📍 위치 프리미엄 등급")

        if my_poi_dist < 0.1 and my_500m >= 30:
            grade, g_color = 'A', '#4CAF50'
            grade_msg = "최상급 위치 — 주변 관광 인프라 밀집 + 도보 이동 가능"
        elif my_poi_dist < 0.2 or my_500m >= 15:
            grade, g_color = 'B', '#2196F3'
            grade_msg = "우수 위치 — 관광 접근성 양호"
        elif my_poi_dist < 0.3 or my_500m >= 7:
            grade, g_color = 'C', '#FF9800'
            grade_msg = "보통 위치 — 리스팅에서 교통 편의성 강조 필요"
        else:
            grade, g_color = 'D', '#F44336'
            grade_msg = "관광 접근성 낮음 — 숙소 자체 퀄리티로 차별화 필요"

        st.markdown(
            f'<div class="grade-box" style="background:{g_color};">'
            f'<span style="font-size:64px; font-weight:bold;">{grade}</span>'
            f'<p style="font-size:16px; margin:8px 0 0;">위치 프리미엄 등급</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**{grade_msg}**")

        lm1, lm2 = st.columns(2)
        lm1.metric(
            "관광지까지 거리",
            f"{my_poi_dist:.3f}km",
            delta=f"서울 중위 0.102km 대비 {my_poi_dist - 0.102:+.3f}km",
            delta_color="inverse",
        )
        lm2.metric(
            "500m 이내 관광지",
            f"{my_500m}개",
            delta=f"서울 중위 19개 대비 {my_500m - 19:+.0f}개",
        )
        st.metric("가장 가까운 관광지 유형", my_poi_type)

        if my_poi_type in ['관광지', '문화시설']:
            st.success("✅ 고RevPAR 유형 근접 — 리스팅 제목에 명시 권장")
        elif my_poi_type in ['음식점', '쇼핑']:
            st.info("ℹ️ 생활 편의 유형 근접 — 장기 숙박 타겟 문구 활용 권장")
        else:
            st.info(f"ℹ️ {my_poi_type} 근접 — 특화 타겟 게스트 설정 검토")

        # 개선 우선순위 TOP 3
        st.markdown("---")
        st.subheader("🎯 지금 당장 실행할 액션 TOP 3")

        priorities = []
        if not my_instant:
            priorities.append(("즉시 (1분)", "즉시예약 활성화", "점유율 즉시 개선 — 비용 없음"))
        if my_extra_fee:
            priorities.append(("즉시 (1분)", "추가요금 제거",
                f"RevPAR +₩{my_revpar * 0.25:,.0f} 회복 가능"))
        if my_photos < 20:
            priorities.append(("단기 (1주)", f"사진 {20 - my_photos}장 추가 촬영",
                "20장 달성 시 클릭률 상승 구간 진입"))
        if my_min_nights > 3:
            priorities.append(("단기 (1주)", f"최소숙박 {my_min_nights}박 → 2박 조정",
                "리뷰 축적 속도 2~3배 가속"))
        if my_rating < 4.5:
            priorities.append(("중기 (3개월)", "평점 4.5+ 달성",
                "검색 노출 증가 + 슈퍼호스트 기반"))
        if not my_superhost:
            priorities.append(("중기 (3~12개월)", "슈퍼호스트 달성",
                f"RevPAR +₩{my_revpar * 0.831:,.0f} 잠재"))

        if priorities:
            for i, (timing, action, effect) in enumerate(priorities[:3], 1):
                st.markdown(f"**{i}. {action}** `{timing}`")
                st.caption(f"　기대 효과: {effect}")
                st.markdown("")
        else:
            st.success("🎉 모든 운영 레버가 최적 상태입니다!")

# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — 가격 시뮬레이션
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.header("📊 가격 변경 시 순이익 시뮬레이션")
    st.info(
        f"**{cluster_name}** 시장의 가격 탄력성 **{elasticity}** 적용 — "
        f"ADR 10% 인상 시 점유율 **{abs(elasticity) * 10:.0f}%** 변화를 가정합니다."
    )

    delta_pct = st.slider("ADR 변화율 (%)", -30, 50, 0, 5,
                           help="오른쪽: 가격 인상 / 왼쪽: 가격 인하")
    delta = delta_pct / 100

    # 시뮬레이션 계산
    new_adr        = my_adr * (1 + delta)
    new_occ        = min(1.0, max(0.0, my_occ * (1 + elasticity * delta)))
    new_revpar     = new_adr * new_occ
    new_revenue    = new_revpar * 30
    new_fee        = new_revenue * 0.03
    new_net        = new_revenue - new_fee - total_opex
    profit_change  = new_net - net_profit

    col1, col2 = st.columns(2)

    with col1:
        # Before/After 표
        st.subheader("Before / After 비교")
        comparison = pd.DataFrame({
            '항목': ['ADR', '점유율', 'RevPAR', '월 매출', '수수료(3%)', 'OPEX', '월 순이익'],
            '현재': [
                f'₩{my_adr:,}', f'{my_occ:.0%}', f'₩{my_revpar:,.0f}',
                f'₩{monthly_revenue:,.0f}', f'-₩{airbnb_fee:,.0f}',
                f'-₩{total_opex:,}', f'₩{net_profit:,.0f}',
            ],
            '변경 후': [
                f'₩{new_adr:,.0f}', f'{new_occ:.0%}', f'₩{new_revpar:,.0f}',
                f'₩{new_revenue:,.0f}', f'-₩{new_fee:,.0f}',
                f'-₩{total_opex:,}', f'₩{new_net:,.0f}',
            ],
            '변화': [
                f'{delta_pct:+d}%',
                f'{(new_occ - my_occ) * 100:+.1f}%p',
                f'{(new_revpar / my_revpar - 1) * 100:+.1f}%' if my_revpar > 0 else '-',
                f'{(new_revenue / monthly_revenue - 1) * 100:+.1f}%' if monthly_revenue > 0 else '-',
                '-', '-',
                f'₩{profit_change:+,.0f}',
            ],
        }).set_index('항목')
        st.table(comparison)

        # 결론 메시지
        if delta_pct == 0:
            st.info("슬라이더를 움직여 가격 변화 효과를 확인하세요.")
        elif delta_pct > 0 and profit_change > 0:
            st.success(f"✅ 가격 인상이 유효합니다. 순이익 **₩{profit_change:+,.0f}** 증가")
        elif delta_pct > 0 and profit_change <= 0:
            st.error(f"❌ 가격 인상이 역효과입니다. 점유율 하락으로 순이익 **₩{abs(profit_change):,.0f}** 감소")
        elif delta_pct < 0 and profit_change > 0:
            st.success(f"✅ 가격 인하로 점유율 상승 → 순이익 **₩{profit_change:+,.0f}** 증가")
        else:
            st.warning(f"⚠️ 가격 인하 시 순이익 **₩{abs(profit_change):,.0f}** 감소. 점유율 개선이 먼저 필요합니다.")

    with col2:
        # 순이익 곡선
        st.subheader("📈 ADR 변화에 따른 월 순이익 곡선")

        x_range = np.linspace(-0.30, 0.50, 80)
        profits = []
        for d in x_range:
            n_adr  = my_adr * (1 + d)
            n_occ  = min(1.0, max(0.0, my_occ * (1 + elasticity * d)))
            n_rev  = n_adr * n_occ * 30
            profits.append(n_rev * 0.97 - total_opex)

        fig4, ax4 = plt.subplots(figsize=(6, 4))
        ax4.plot(x_range * 100, profits, color='steelblue', linewidth=2.5)
        ax4.axhline(0, color='red', linestyle='--', lw=1.2, alpha=0.8, label='손익분기선')
        ax4.axvline(delta_pct, color='#FF9800', linestyle='--', lw=1.5,
                    label=f'현재 설정 ({delta_pct:+d}%)')
        ax4.scatter([delta_pct], [new_net], color='#FF9800', s=100, zorder=6)
        ax4.fill_between(
            x_range * 100, profits, 0,
            where=[p > 0 for p in profits], alpha=0.1, color='green', label='흑자 구간'
        )
        ax4.fill_between(
            x_range * 100, profits, 0,
            where=[p <= 0 for p in profits], alpha=0.1, color='red', label='적자 구간'
        )
        ax4.set_xlabel('ADR 변화율 (%)')
        ax4.set_ylabel('월 순이익 (원)')
        ax4.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda y, _: f'₩{y/10000:.0f}만')
        )
        ax4.legend(fontsize=8)
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)
        fig4.tight_layout()
        st.pyplot(fig4)
        plt.close()

        # 최적 ADR 표시
        best_idx    = int(np.argmax(profits))
        best_delta  = x_range[best_idx]
        best_adr    = my_adr * (1 + best_delta)
        best_profit = profits[best_idx]

        st.success(
            f"🎯 **순이익 최대화 ADR: ₩{best_adr:,.0f}** ({best_delta * 100:+.0f}%)\n\n"
            f"예상 월 순이익: **₩{best_profit:,.0f}**"
        )

# ── 푸터 ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "서울 Airbnb RevPAR 최적화 프로젝트 | "
    "데이터 기간: 2024-10 ~ 2025-09 (TTM 12개월) | "
    "32,061개 리스팅 기반 | Active+Operating 14,399건 벤치마크"
)
