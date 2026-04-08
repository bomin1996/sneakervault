import json
import logging

import redis
from openai import AsyncOpenAI

from app.config import get_settings
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.schemas.price import AIAnalysisResponse

logger = logging.getLogger(__name__)

_settings = get_settings()
_redis_client = redis.from_url(_settings.REDIS_URL, decode_responses=True)

AI_CACHE_TTL_SECONDS = 3600  # 1시간
AI_REQUEST_TIMEOUT_SECONDS = 30


def _cache_key(product_id: int) -> str:
    return f"ai_analysis:{product_id}"


async def analyze_price_trend(
    product: Product,
    histories: list[PriceHistory],
) -> AIAnalysisResponse:
    cached = _redis_client.get(_cache_key(product.id))
    if cached:
        logger.info(f"AI analysis cache hit for product {product.id}")
        return AIAnalysisResponse(**json.loads(cached))

    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        return _fallback_analysis(product, histories)

    price_data = "\n".join(
        f"- {h.recorded_at.strftime('%Y-%m-%d %H:%M')}: {h.price:,}원"
        + (f" (이전: {h.previous_price:,}원)" if h.previous_price else "")
        for h in histories
    )

    prompt = f"""다음 리셀 상품의 시세 데이터를 분석해주세요.

상품명: {product.name}
모델번호: {product.model_number}
발매가: {product.release_price:,}원
현재가: {product.current_price:,}원

시세 이력:
{price_data}

다음 형식으로 분석해주세요:
1. 요약: 전체 시세 흐름을 2-3문장으로 요약
2. 트렌드: "상승" / "하락" / "횡보" 중 하나
3. 추천: 판매자에게 1-2문장으로 가격 전략 추천"""

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "리셀 시장 시세 분석 전문가입니다. 간결하고 실용적인 분석을 제공합니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=AI_REQUEST_TIMEOUT_SECONDS,
        )
    except Exception as e:
        logger.error(f"OpenAI API call failed for product {product.id}: {e}")
        return _fallback_analysis(product, histories)

    content = response.choices[0].message.content
    lines = content.strip().split("\n")

    summary, trend, recommendation = "", "횡보", ""
    section = ""
    for line in lines:
        if "요약" in line:
            section = "summary"
            summary = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif "트렌드" in line:
            section = "trend"
            trend = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif "추천" in line:
            section = "recommendation"
            recommendation = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif section == "summary":
            summary += " " + line.strip()
        elif section == "recommendation":
            recommendation += " " + line.strip()

    result = AIAnalysisResponse(
        product_id=product.id,
        product_name=product.name,
        summary=summary.strip() or content,
        trend=trend.strip(),
        recommendation=recommendation.strip(),
    )

    _redis_client.setex(
        _cache_key(product.id),
        AI_CACHE_TTL_SECONDS,
        result.model_dump_json(),
    )

    return result


def _fallback_analysis(
    product: Product,
    histories: list[PriceHistory],
) -> AIAnalysisResponse:
    """Fallback when OpenAI API key is not configured."""
    if len(histories) < 2:
        return AIAnalysisResponse(
            product_id=product.id,
            product_name=product.name,
            summary="시세 데이터가 부족하여 분석이 어렵습니다.",
            trend="데이터 부족",
            recommendation="더 많은 시세 데이터가 수집된 후 분석을 시도해주세요.",
        )

    prices = [h.price for h in histories]
    avg_price = sum(prices) / len(prices)
    change_rate = (prices[0] - prices[-1]) / prices[-1] * 100 if prices[-1] > 0 else 0

    if change_rate > 5:
        trend = "상승"
    elif change_rate < -5:
        trend = "하락"
    else:
        trend = "횡보"

    premium_rate = (product.current_price - product.release_price) / product.release_price * 100

    return AIAnalysisResponse(
        product_id=product.id,
        product_name=product.name,
        summary=(
            f"최근 {len(histories)}건의 거래에서 평균가 {avg_price:,.0f}원, "
            f"변동률 {change_rate:+.1f}%. "
            f"발매가 대비 프리미엄 {premium_rate:+.1f}%."
        ),
        trend=trend,
        recommendation=(
            f"현재 시세가 {'상승' if change_rate > 0 else '하락'} 추세입니다. "
            f"{'가격 유지 또는 소폭 인상을 권장합니다.' if change_rate > 0 else '시장 상황을 지켜보며 가격 조정을 고려해주세요.'}"
        ),
    )
