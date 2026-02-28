"""
predict_utils.py — 서울 에어비앤비 RevPAR 예측 헬퍼
=====================================================

사용법:
    from predict_utils import load_models, predict_revpar

    artifacts = load_models()               # models/ 폴더에서 pkl 일괄 로드
    result = predict_revpar(listing, 500_000, **artifacts)

입력 dict (listing_features) 구조:
    필수 — Model A (ADR):
        cluster                 : int   (0~3)
        nearest_poi_dist_km     : float (km)
        poi_dist_category       : str   ('초근접'|'근접'|'보통'|'원거리')
                                        # <0.2km|0.2-0.5|0.5-1.0|1.0+
        bedrooms                : int
        baths                   : float
        guests                  : int
        room_type               : str   ('entire_home'|'private_room'|'hotel_room'|'shared_room')
        nearest_poi_type_name   : str   ('관광지'|'문화시설'|...)
        district_median_revpar  : float (원)
        district_listing_count  : int
        district_superhost_rate : float (0~1)
        district_entire_home_rate: float (0~1)
        ttm_pop                 : int   (자치구 인구)

    필수 — Model B (Occupancy):
        min_nights              : int
        instant_book            : int   (0/1)
        superhost               : int   (0/1)
        rating_overall          : float
        photos_count            : int
        num_reviews             : int
        extra_guest_fee_policy  : str   ('0'=요금없음 | '1'=요금있음)  # 문자열!
        photos_tier             : str   ('하'|'중하'|'중상'|'상')
                                        # <14장|14-22|23-35(최적)|36+
        is_active_operating     : int   (0/1)

    선택 — 자치구 내 상대적 경쟁력 (없으면 1.0으로 자동 설정):
        photos_rel_dist         : float (내 사진수 / 자치구 평균)
        rating_rel_dist         : float (내 평점 / 자치구 평균)
        reviews_rel_dist        : float (내 리뷰수 / 자치구 평균)
        min_nights_rel_dist     : float (내 최소박 / 자치구 평균)

    선택 — revpar_trend 계산용 (없으면 None 반환):
        ttm_revpar              : float (TTM RevPAR, 원)
        l90d_revpar             : float (최근 90일 RevPAR, 원)

    선택:
        ttm_avg_rate            : float (TTM 평균 ADR, 없으면 ADR 예측값 사용)

revpar_trend 해석 기준:
    > 0.1   → "최근 성과 상승 중"   (green)
    -0.1~0.1 → "안정 구간"          (yellow)
    < -0.1  → "최근 성과 부진"      (red)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import json

_MODELS_DIR = Path(__file__).parent / "models"

_REL_DIST_COLS = [
    "photos_rel_dist",
    "rating_rel_dist",
    "reviews_rel_dist",
    "min_nights_rel_dist",
]


def load_models(models_dir: str | Path | None = None) -> dict:
    """models/ 폴더에서 pkl 파일을 일괄 로드합니다.

    Returns
    -------
    dict with keys:
        model_A, model_B, iso_reg, encoders, feature_config
    """
    d = Path(models_dir) if models_dir else _MODELS_DIR
    if not d.exists():
        raise FileNotFoundError(
            f"models/ 폴더를 찾을 수 없습니다: {d}\n"
            "notebooks/07_cluster_modeling.ipynb 마지막 셀을 실행해 pkl을 생성하세요."
        )

    model_A = joblib.load(d / "model_a.pkl")
    model_B = joblib.load(d / "model_b.pkl")
    iso_reg = joblib.load(d / "iso_reg.pkl")
    encoders = joblib.load(d / "encoders.pkl")

    with open(d / "feature_config.json", encoding="utf-8") as f:
        feature_config = json.load(f)

    return dict(
        model_A=model_A,
        model_B=model_B,
        iso_reg=iso_reg,
        encoders=encoders,
        feature_config=feature_config,
    )


def predict_revpar(
    listing_features: dict,
    opex_per_month: float,
    *,
    model_A,
    model_B,
    iso_reg,
    encoders: dict,
    feature_config: dict,
) -> dict:
    """단일 리스팅 RevPAR 예측 + 순이익 계산.

    Parameters
    ----------
    listing_features : dict
        리스팅 피처 값. 위 docstring 참조.
    opex_per_month : float
        월 운영비 합계 (원).
    **artifacts
        load_models() 반환값을 그대로 언패킹해서 전달.

    Returns
    -------
    dict with keys:
        ADR_pred         : float  — 시장 적정 ADR (원)
        Occ_pred         : float  — 예측 예약률 (0~1)
        RevPAR_pred      : float  — Isotonic 보정 RevPAR (원)
        monthly_revenue  : float  — 월 예상 수익 (원)
        net_profit       : float  — 월 순이익 = revenue - opex (원)
        revpar_trend     : float | None  — 모멘텀 지표 (ttm/l90d 입력 시)
        trend_label      : str | None    — '상승'|'안정'|'하락'
    """
    FEATURES_A = feature_config["FEATURES_A"]
    FEATURES_B_BASE = feature_config["FEATURES_B_BASE"]

    row = pd.DataFrame([listing_features])

    # ── 카테고리 인코딩 ─────────────────────────────────────────────────────
    for col, le in encoders.items():
        if col in row.columns:
            try:
                row[col] = le.transform(row[col].astype(str))
            except ValueError:
                row[col] = -1  # unseen label → -1 (LightGBM handles gracefully)

    # ── rel_dist 컬럼 기본값 (자치구 평균 = 1.0) ────────────────────────────
    for col in _REL_DIST_COLS:
        if col not in row.columns:
            row[col] = 1.0

    # ── Model A: ADR 예측 ────────────────────────────────────────────────────
    adr_pred = float(np.expm1(model_A.predict(row[FEATURES_A])[0]))

    # ── price_gap: 현재 호스트 ADR과 시장 적정 ADR의 차이 ───────────────────
    ttm_avg_rate = listing_features.get("ttm_avg_rate", adr_pred)
    price_gap = ttm_avg_rate - adr_pred

    # ── Model B: Occupancy 예측 ──────────────────────────────────────────────
    X_b = row[FEATURES_B_BASE].copy()
    X_b["price_gap_oof"] = price_gap
    occ_pred = float(np.clip(model_B.predict(X_b)[0], 0, 1))

    # ── RevPAR 통합 & Isotonic 보정 ─────────────────────────────────────────
    revpar_raw = adr_pred * occ_pred
    revpar_cal = float(iso_reg.predict([revpar_raw])[0])

    # ── revpar_trend 계산 (입력값 있을 때만) ────────────────────────────────
    ttm_revpar = listing_features.get("ttm_revpar")
    l90d_revpar = listing_features.get("l90d_revpar")

    if ttm_revpar is not None and l90d_revpar is not None:
        revpar_trend = (l90d_revpar - ttm_revpar / 4) / (ttm_revpar / 4 + 1e-6)
        if revpar_trend > 0.1:
            trend_label = "상승"
        elif revpar_trend < -0.1:
            trend_label = "하락"
        else:
            trend_label = "안정"
    else:
        revpar_trend = None
        trend_label = None

    return {
        "ADR_pred": adr_pred,
        "Occ_pred": occ_pred,
        "RevPAR_pred": revpar_cal,
        "monthly_revenue": revpar_cal * 30,
        "net_profit": revpar_cal * 30 - opex_per_month,
        "revpar_trend": revpar_trend,
        "trend_label": trend_label,
    }


def compute_health_score(user_vals: dict, cluster_listings) -> dict:
    """클러스터 내 백분위 기반 5-컴포넌트 헬스 스코어 (0~100).

    Parameters
    ----------
    user_vals : dict
        호스트 입력값. 필수 키:
            my_reviews    : int   — 리뷰 수
            my_rating     : float — 평점 (0~5)
            my_photos     : int   — 사진 수
            my_instant    : bool  — 즉시예약 여부
            my_min_nights : int   — 최소 숙박일
            my_extra_fee  : bool  — 추가 게스트 요금 여부
            my_poi_dist   : float — 가장 가까운 POI까지 거리 (km)
            my_bedrooms   : int   — 침실 수
            my_baths      : float — 욕실 수

    cluster_listings : pd.DataFrame
        동일 클러스터 내 Active+Operating 리스팅.
        cluster_listings_ao.csv를 district의 cluster로 필터링해 전달.
        필요 컬럼: num_reviews, rating_overall, min_nights,
                   nearest_poi_dist_km, bedrooms, baths

    Returns
    -------
    dict with keys:
        composite  : float  — 종합 점수 (0~100)
        grade      : str    — 'A'|'B'|'C'|'D'|'F'
        components : dict   — 5개 컴포넌트 점수
            review_signal   : float
            listing_quality : float
            booking_policy  : float
            location        : float
            listing_config  : float
        actions    : list[str] — 개선 권장 액션

    Example
    -------
    import pandas as pd
    from predict_utils import compute_health_score

    ao = pd.read_csv("cluster_listings_ao.csv")
    cluster_id = 0   # district_lookup.csv 에서 확인
    cluster_df = ao[ao["cluster"] == cluster_id]

    user_vals = {
        "my_reviews": 30, "my_rating": 4.7, "my_photos": 25,
        "my_instant": True, "my_min_nights": 2,
        "my_extra_fee": False, "my_poi_dist": 0.3,
        "my_bedrooms": 2, "my_baths": 1.0,
    }
    result = compute_health_score(user_vals, cluster_df)
    print(result["composite"], result["grade"])
    """

    def pct_rank(value, series):
        s = series.dropna()
        return float(np.mean(s <= value) * 100) if len(s) > 0 else 50.0

    # 1. Review Signal
    reviews_pct   = pct_rank(user_vals["my_reviews"], cluster_listings["num_reviews"])
    rating_pct    = pct_rank(user_vals["my_rating"],  cluster_listings["rating_overall"])
    review_signal = (reviews_pct + rating_pct) / 2

    # 2. Listing Quality — 사진 최적 구간 23-35장
    n = user_vals["my_photos"]
    if 23 <= n <= 35:
        photos_score = 100.0
    elif n < 23:
        photos_score = (n / 23) * 100
    else:
        photos_score = max(0.0, 100.0 - (n - 35) * 2.5)
    listing_quality = photos_score

    # 3. Booking Policy
    instant_score    = 100.0 if user_vals["my_instant"] else 0.0
    min_nights_pct   = (
        pct_rank(user_vals["my_min_nights"], cluster_listings["min_nights"])
        if "min_nights" in cluster_listings.columns else 50.0
    )
    no_extra_fee_score = 100.0 if not user_vals["my_extra_fee"] else 0.0
    booking_policy   = (
        0.4 * instant_score
        + 0.4 * (100 - min_nights_pct)
        + 0.2 * no_extra_fee_score
    )

    # 4. Location — 거리 낮을수록 좋음
    poi_dist_pct = (
        pct_rank(user_vals["my_poi_dist"], cluster_listings["nearest_poi_dist_km"])
        if "nearest_poi_dist_km" in cluster_listings.columns else 50.0
    )
    location = 100 - poi_dist_pct

    # 5. Listing Config
    bedrooms_pct = (
        pct_rank(user_vals["my_bedrooms"], cluster_listings["bedrooms"])
        if "bedrooms" in cluster_listings.columns else 50.0
    )
    baths_pct = (
        pct_rank(user_vals["my_baths"], cluster_listings["baths"])
        if "baths" in cluster_listings.columns else 50.0
    )
    listing_config = (bedrooms_pct + baths_pct) / 2

    composite = (review_signal + listing_quality + booking_policy + location + listing_config) / 5

    if composite >= 80:   grade = "A"
    elif composite >= 60: grade = "B"
    elif composite >= 40: grade = "C"
    elif composite >= 20: grade = "D"
    else:                 grade = "F"

    actions = []
    if review_signal   < 40: actions.append("📝 리뷰 수집 강화 — 게스트에게 리뷰 요청 메시지 발송")
    if booking_policy  < 40: actions.append("⚡ 즉시예약 활성화 또는 최소박 단축 검토")
    if listing_quality < 40: actions.append("📸 사진 21~35장 최적 구간으로 보정")
    if listing_config  < 30: actions.append("🛏️ 침실·욕실 정보 정확도 검토")
    if location        < 30: actions.append("📍 근처 POI 설명 보강 — 위치 어필 강화")
    if not actions:          actions.append("✅ 현재 상태 유지 — 주기적 가격 재검토 권장")

    return {
        "composite": round(composite, 1),
        "grade": grade,
        "components": {
            "review_signal":   round(review_signal,   1),
            "listing_quality": round(listing_quality, 1),
            "booking_policy":  round(booking_policy,  1),
            "location":        round(location,        1),
            "listing_config":  round(listing_config,  1),
        },
        "actions": actions,
    }


# ── 사용 예시 (직접 실행 시) ──────────────────────────────────────────────────
if __name__ == "__main__":
    example = {
        "cluster": 2,
        "nearest_poi_dist_km": 0.5,
        "poi_dist_category": "초근접",
        "bedrooms": 2,
        "baths": 1,
        "guests": 4,
        "room_type": "entire_home",
        "nearest_poi_type_name": "관광지",
        "district_median_revpar": 50000,
        "district_listing_count": 800,
        "district_superhost_rate": 0.25,
        "district_entire_home_rate": 0.70,
        "ttm_pop": 100000,
        "min_nights": 2,
        "instant_book": 1,
        "superhost": 1,
        "rating_overall": 4.8,
        "photos_count": 25,
        "num_reviews": 50,
        "extra_guest_fee_policy": "1",
        "photos_tier": "중상",
        "is_active_operating": 1,
        "ttm_avg_rate": 120000,
        "ttm_revpar": 80000,
        "l90d_revpar": 90000,
    }

    artifacts = load_models()
    res = predict_revpar(example, 500_000, **artifacts)

    print("[호스트 진단 리포트]")
    print(f"  시장 적정 ADR  : ₩{res['ADR_pred']:,.0f}")
    print(f"  현재 ADR       : ₩{example['ttm_avg_rate']:,.0f}")
    print(f"  예측 Occupancy : {res['Occ_pred']:.1%}")
    print(f"  예측 RevPAR    : ₩{res['RevPAR_pred']:,.0f}")
    print(f"  월 예상 수익   : ₩{res['monthly_revenue']:,.0f}")
    print(f"  월 순이익      : ₩{res['net_profit']:,.0f}")
    print(f"  RevPAR 트렌드  : {res['revpar_trend']:.3f} ({res['trend_label']})")
