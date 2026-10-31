"""KRX 현재 시세 스냅샷 수집.

FinanceDataReader의 StockListing('KRX')에 이미 당일 시세(종가/등락/거래량/시총)가
포함되어 있어서 별도 시세 API 없이 이 한 번의 호출로 전 종목 스냅샷을 가져온다.
"""
from dataclasses import dataclass

import FinanceDataReader as fdr


@dataclass
class KrxQuote:
    code: str
    current_price: int
    previous_close: int
    change_amount: int
    change_rate: float
    open_price: int
    day_high: int
    day_low: int
    volume: int
    market_cap: int


def fetch_krx_quotes() -> list[KrxQuote]:
    """KRX 전 종목의 현재 시세 스냅샷을 가져온다."""
    listing = fdr.StockListing("KRX")

    quotes = []
    for row in listing.itertuples(index=False):
        quotes.append(KrxQuote(
            code=row.Code,
            current_price=row.Close,
            previous_close=row.Close - row.Changes,
            change_amount=row.Changes,
            change_rate=row.ChagesRatio,
            open_price=row.Open,
            day_high=row.High,
            day_low=row.Low,
            volume=row.Volume,
            market_cap=row.Marcap,
        ))
    return quotes
