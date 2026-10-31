"""KRX(한국거래소) 종목 마스터 수집.

FinanceDataReader의 두 리스팅을 코드 기준으로 합쳐서 쓴다.
- "KRX": 코드/이름/시장 구분 (전 종목, 우선주 포함)
- "KRX-DESC": 업종/섹터 설명 (일부 종목은 결측)
"""
import logging
from dataclasses import dataclass

import FinanceDataReader as fdr
import pandas as pd

logger = logging.getLogger("apps.trender_stock")

_MARKET_MAP = {
    "KOSPI": "KOSPI",
    "KOSDAQ": "KOSDAQ",
    "KOSDAQ GLOBAL": "KOSDAQ",
    "KONEX": "KONEX",
}

_TICKER_SUFFIX = {
    "KOSPI": ".KS",
    "KOSDAQ": ".KQ",
    "KONEX": ".KN",
}


@dataclass
class KrxStock:
    code: str
    ticker: str
    name: str
    market: str
    sector: str
    industry: str


def fetch_krx_stocks() -> list[KrxStock]:
    """KRX 전 종목 마스터 목록을 가져온다. 알 수 없는 시장 구분은 건너뛴다.

    "KRX-DESC"(업종/섹터 보강용) 소스는 별도 외부 캐시라 KRX 리스팅과
    별개로 실패할 수 있다 — 그 경우 업종/섹터 없이(빈 문자열) 핵심 정보만 동기화한다.
    """
    listing = fdr.StockListing("KRX")[["Code", "Name", "Market"]]

    try:
        desc = fdr.StockListing("KRX-DESC")[["Code", "Sector", "Industry"]]
        merged = listing.merge(desc, on="Code", how="left")
    except Exception as exc:
        logger.warning("KRX-DESC(업종/섹터) 조회 실패, 업종 정보 없이 진행: %s", exc)
        merged = listing.assign(Sector=pd.NA, Industry=pd.NA)

    stocks = []
    for row in merged.itertuples(index=False):
        market = _MARKET_MAP.get(row.Market)
        if market is None:
            continue
        stocks.append(KrxStock(
            code=row.Code,
            ticker=f"{row.Code}{_TICKER_SUFFIX[market]}",
            name=row.Name,
            market=market,
            sector=_clean(row.Sector),
            industry=_clean(row.Industry),
        ))
    return stocks


def _clean(value) -> str:
    return "" if pd.isna(value) else str(value)
