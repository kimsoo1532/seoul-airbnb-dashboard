# RevPAR ML 모델 통합 가이드

## 패키지 구성

```
revpar_model_package/
├── predict_utils.py              # 예측 헬퍼 (import 1개로 사용)
├── models/
│   ├── model_a.pkl               # LightGBM ADR 예측 모델
│   ├── model_b.pkl               # LightGBM 예약률 예측 모델
│   ├── iso_reg.pkl               # Isotonic Regression (RevPAR 보정)
│   ├── encoders.pkl              # LabelEncoder (카테고리 컬럼용)
│   └── feature_config.json       # 피처 목록 정의
├── district_lookup.csv           # 자치구별 모델 입력 통계 (25개 자치구)
└── cluster_listings_ao.csv       # 헬스스코어 백분위 비교용 (14,399개 리스팅)
```

## 설치 의존성

```bash
pip install lightgbm scikit-learn joblib pandas numpy
```

---

## 1. RevPAR 예측 (`predict_revpar`)

```python
import pandas as pd
from predict_utils import load_models, predict_revpar

# 앱 시작 시 1회 로드 (Streamlit: @st.cache_resource 권장)
artifacts = load_models("models/")

# 자치구 룩업 로드
district_lookup = pd.read_csv("district_lookup.csv").set_index("district")

# 자치구 선택 → 통계 자동 채우기
district = "Mapo-gu"          # district_lookup.csv의 district 컬럼값 (영문)
row = district_lookup.loc[district]

listing = {
    # ── 자치구 통계 (district_lookup에서 자동 채움) ──────────────────────
    "cluster":                    int(row["cluster"]),
    "district_median_revpar":     float(row["district_median_revpar"]),
    "district_listing_count":     int(row["district_listing_count"]),
    "district_superhost_rate":    float(row["district_superhost_rate"]),
    "district_entire_home_rate":  float(row["district_entire_home_rate"]),
    "ttm_pop":                    int(row["ttm_pop"]),

    # ── 호스트 입력값 ────────────────────────────────────────────────────
    "room_type":               "entire_home",  # entire_home | private_room | hotel_room | shared_room
    "bedrooms":                2,
    "baths":                   1.0,
    "guests":                  4,
    "min_nights":              2,
    "instant_book":            1,              # 1=즉시예약 ON
    "superhost":               1,              # 1=슈퍼호스트
    "rating_overall":          4.8,
    "photos_count":            25,
    "num_reviews":             50,
    "extra_guest_fee_policy":  "1",            # "0"=없음 | "1"=있음 (문자열!)
    "is_active_operating":     1,

    # ── POI 거리 ─────────────────────────────────────────────────────────
    "nearest_poi_dist_km":     0.3,
    "poi_dist_category":       "근접",         # 초근접(<0.2) | 근접(0.2-0.5) | 보통(0.5-1.0) | 원거리(1.0+)
    "nearest_poi_type_name":   "관광지",

    # ── 사진 티어 (아래 헬퍼 함수로 자동 계산 가능) ──────────────────────
    "photos_tier":             "중상",         # 하(<14) | 중하(14-22) | 중상(23-35) | 상(36+)
}

result = predict_revpar(listing, opex_per_month=500_000, **artifacts)

print(f"예측 ADR:      ₩{result['ADR_pred']:,.0f}")
print(f"예측 예약률:   {result['Occ_pred']:.1%}")
print(f"예측 RevPAR:   ₩{result['RevPAR_pred']:,.0f}")
print(f"월 예상 수익:  ₩{result['monthly_revenue']:,.0f}")
print(f"월 순이익:     ₩{result['net_profit']:,.0f}")
```

### predict_revpar 반환값

| 키 | 타입 | 설명 |
|----|------|------|
| `ADR_pred` | float | 시장 적정 ADR (원) |
| `Occ_pred` | float | 예측 예약률 (0~1) |
| `RevPAR_pred` | float | Isotonic 보정 RevPAR (원) |
| `monthly_revenue` | float | 월 예상 수익 = RevPAR × 30 (원) |
| `net_profit` | float | 월 순이익 = monthly_revenue - opex (원) |
| `revpar_trend` | float \| None | 모멘텀 지표 (ttm_revpar + l90d_revpar 입력 시) |
| `trend_label` | str \| None | '상승' \| '안정' \| '하락' |

---

## 2. 숙소 헬스 스코어 (`compute_health_score`)

클러스터 내 동일 유형 숙소와 비교한 **5가지 운영 건강도 지표** (0~100).

```python
import pandas as pd
from predict_utils import compute_health_score

# 클러스터 비교 데이터 로드 (앱 시작 시 1회)
ao_df = pd.read_csv("cluster_listings_ao.csv")

# 자치구의 cluster 번호 → cluster_listings_ao 필터링
cluster_id = int(district_lookup.loc[district, "cluster"])   # 0~3
cluster_listings = ao_df[ao_df["cluster"] == cluster_id]

# 호스트 입력값
user_vals = {
    "my_reviews":    50,     # 리뷰 수
    "my_rating":     4.8,    # 평점 (0~5)
    "my_photos":     25,     # 사진 수
    "my_instant":    True,   # 즉시예약 여부
    "my_min_nights": 2,      # 최소 숙박일
    "my_extra_fee":  False,  # 추가 게스트 요금 여부
    "my_poi_dist":   0.3,    # 가장 가까운 POI까지 거리 (km)
    "my_bedrooms":   2,      # 침실 수
    "my_baths":      1.0,    # 욕실 수
}

hs = compute_health_score(user_vals, cluster_listings)

print(f"종합 점수 : {hs['composite']} / 100")
print(f"등급      : {hs['grade']}")
print("컴포넌트  :")
for name, score in hs["components"].items():
    print(f"  {name:20s}: {score:.1f}")
print("개선 액션 :")
for action in hs["actions"]:
    print(f"  {action}")
```

### compute_health_score 반환값

| 키 | 타입 | 설명 |
|----|------|------|
| `composite` | float | 종합 점수 (0~100) |
| `grade` | str | 'A'(≥80) \| 'B'(≥60) \| 'C'(≥40) \| 'D'(≥20) \| 'F' |
| `components` | dict | 5개 컴포넌트 점수 (아래 참조) |
| `actions` | list[str] | 개선 권장 액션 목록 |

### 5개 컴포넌트

| 키 | 표시명 | 계산 기준 |
|----|--------|---------|
| `review_signal` | 리뷰 신호 | (리뷰 수 백분위 + 평점 백분위) / 2 |
| `listing_quality` | 사진 품질 | 사진 23~35장=100점, 범위 벗어날수록 감점 |
| `booking_policy` | 예약 정책 | 즉시예약(40%) + 최소박 유연성(40%) + 추가요금 없음(20%) |
| `location` | 위치 | 100 − POI 거리 백분위 (가까울수록 높음) |
| `listing_config` | 숙소 구성 | (침실 수 백분위 + 욕실 수 백분위) / 2 |

### 헬스 스코어 UI 예시 (app.py 스타일)

```python
import streamlit as st

grade_colors = {"A": "#2E7D32", "B": "#00A699", "C": "#FFB400", "D": "#FF8C00", "F": "#C62828"}
gc = grade_colors.get(hs["grade"], "#767676")

# 왼쪽: 점수 카드
st.markdown(
    f'<div style="background:{gc}18;border:2.5px solid {gc};border-radius:16px;'
    f'padding:28px 20px;text-align:center;">'
    f'<div style="font-size:52px;font-weight:800;color:{gc};">{int(hs["composite"])}</div>'
    f'<div style="font-size:13px;color:#767676;margin-top:2px;">/ 100</div>'
    f'<div style="background:{gc};color:white;border-radius:50%;width:48px;height:48px;'
    f'display:inline-flex;align-items:center;justify-content:center;'
    f'font-size:22px;font-weight:800;margin-top:12px;">{hs["grade"]}</div>'
    f'<div style="font-size:12px;color:#767676;margin-top:8px;">클러스터 내 백분위 기준</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# 오른쪽: 컴포넌트 바
comp_labels = {
    "review_signal":   "리뷰 신호",
    "listing_quality": "사진 품질",
    "booking_policy":  "예약 정책",
    "location":        "위치",
    "listing_config":  "숙소 구성",
}
bar_html = ""
for key, label in comp_labels.items():
    v = hs["components"][key]
    color = "#2E7D32" if v >= 70 else "#FFB400" if v >= 40 else "#C62828"
    bar_html += (
        f'<div style="margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">'
        f'<span style="color:#484848;">{label}</span>'
        f'<span style="font-weight:600;color:{color};">{int(v)}/100</span></div>'
        f'<div style="background:#EBEBEB;border-radius:6px;height:8px;">'
        f'<div style="background:{color};width:{v:.0f}%;height:8px;border-radius:6px;"></div></div></div>'
    )
st.markdown(bar_html, unsafe_allow_html=True)

# 개선 액션
if hs["actions"] and not hs["actions"][0].startswith("✅"):
    actions_html = '<div style="margin-top:8px;background:#FFF5F5;border-radius:8px;padding:12px 14px;">'
    actions_html += '<div style="font-size:11px;font-weight:700;color:#C62828;margin-bottom:6px;">개선 액션</div>'
    for a in hs["actions"]:
        actions_html += f'<div style="font-size:12px;color:#484848;margin-bottom:4px;">{a}</div>'
    actions_html += "</div>"
    st.markdown(actions_html, unsafe_allow_html=True)
```

---

## 헬퍼 함수

```python
def get_photos_tier(photos_count: int) -> str:
    if photos_count < 14:   return "하"
    elif photos_count < 23: return "중하"
    elif photos_count <= 35: return "중상"
    else:                   return "상"

def get_poi_dist_category(dist_km: float) -> str:
    if dist_km < 0.2:   return "초근접"
    elif dist_km < 0.5: return "근접"
    elif dist_km < 1.0: return "보통"
    else:               return "원거리"
```

---

## Streamlit 전체 캐싱 패턴

```python
import streamlit as st
import pandas as pd
from predict_utils import load_models, predict_revpar, compute_health_score

@st.cache_resource
def load_ml_models():
    return load_models("models/")

@st.cache_data
def load_district_lookup():
    return pd.read_csv("district_lookup.csv").set_index("district")

@st.cache_data
def load_cluster_listings():
    return pd.read_csv("cluster_listings_ao.csv")

# 앱 전역에서 사용
artifacts        = load_ml_models()
district_lookup  = load_district_lookup()
ao_df            = load_cluster_listings()
```

---

## district_lookup.csv 컬럼

| 컬럼 | 설명 |
|------|------|
| `district` | 자치구 영문명 (예: Mapo-gu) |
| `cluster` | K-Means 군집 번호 (0~3) |
| `cluster_name` | 핫플 수익형 / 로컬 주거형 / 가성비 신흥형 / 프리미엄 비즈니스 |
| `district_median_revpar` | 자치구 RevPAR 중위값 (Active+Operating 기준, 원) |
| `district_listing_count` | 자치구 내 Active+Operating 리스팅 수 |
| `district_superhost_rate` | 자치구 내 슈퍼호스트 비율 |
| `district_entire_home_rate` | 자치구 내 전체 객실(entire_home) 비율 |
| `ttm_pop` | 자치구 인구 (TTM 중위값) |

## cluster_listings_ao.csv 컬럼

| 컬럼 | 설명 |
|------|------|
| `cluster` | K-Means 군집 번호 (헬스스코어 필터 기준) |
| `cluster_name` | 군집 이름 |
| `district` | 자치구 영문명 |
| `num_reviews` | 리뷰 수 (review_signal 백분위 기준) |
| `rating_overall` | 평점 (review_signal 백분위 기준) |
| `photos_count` | 사진 수 |
| `instant_book` | 즉시예약 여부 (0/1) |
| `min_nights` | 최소 숙박일 |
| `extra_guest_fee_policy` | 추가 게스트 요금 (0/1 문자열) |
| `nearest_poi_dist_km` | 가장 가까운 POI까지 거리 (km) |
| `bedrooms` | 침실 수 |
| `baths` | 욕실 수 |
