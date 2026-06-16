from __future__ import annotations

import datetime as dt
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import feedparser
import pandas as pd
import requests
import yfinance as yf


US_TICKERS = {
    "NVDA": "NVIDIA",
    "TSM": "台积电 ADR",
}

HK_TICKERS = {
    "9988.HK": "阿里巴巴-W",
    "0700.HK": "腾讯控股",
    "3690.HK": "美团-W",
}

SPCX_TICKER = "SPCX"
SPACEX_CIK = "0001181412"
HKT = dt.timezone(dt.timedelta(hours=8))


@dataclass
class QuoteSummary:
    ticker: str
    name: str
    currency: str
    last_date: str
    close: float
    change_pct: float
    volume: int | None
    day_range: str
    ma20: float | None
    ma50: float | None
    rsi14: float | None


def fmt_num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "N/A"
    return f"{value:,.{digits}f}"


def fmt_volume(value: int | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return str(value)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def download_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    data = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
    if data.empty:
        return data
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.reset_index()
    data["Date"] = pd.to_datetime(data["Date"]).dt.strftime("%Y-%m-%d")
    return data.dropna(subset=["Close"])


def summarize_quote(ticker: str, name: str) -> QuoteSummary | None:
    df = download_history(ticker)
    if df.empty:
        return None

    close = df["Close"].astype(float)
    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()
    df["RSI14"] = rsi(close)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    prev_close = float(prev["Close"])
    change_pct = ((float(latest["Close"]) / prev_close) - 1) * 100 if prev_close else 0

    try:
        currency = yf.Ticker(ticker).fast_info.get("currency") or ""
    except Exception:
        currency = ""
    volume = latest.get("Volume")
    volume_int = None if pd.isna(volume) else int(volume)
    return QuoteSummary(
        ticker=ticker,
        name=name,
        currency=currency,
        last_date=str(latest["Date"]),
        close=float(latest["Close"]),
        change_pct=change_pct,
        volume=volume_int,
        day_range=f"{fmt_num(float(latest['Low']))} - {fmt_num(float(latest['High']))}",
        ma20=None if pd.isna(latest["MA20"]) else float(latest["MA20"]),
        ma50=None if pd.isna(latest["MA50"]) else float(latest["MA50"]),
        rsi14=None if pd.isna(latest["RSI14"]) else float(latest["RSI14"]),
    )


def yahoo_news(symbol: str, limit: int = 4) -> list[tuple[str, str]]:
    feed = feedparser.parse(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US")
    return [(entry.get("title", "").strip(), entry.get("link", "").strip()) for entry in feed.entries[:limit]]


def sec_recent_filings(cik: str) -> list[tuple[str, str, str]]:
    user_agent = os.getenv("SEC_USER_AGENT", "stock-report-bot/1.0 contact@example.com")
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=20)
        resp.raise_for_status()
        recent = resp.json().get("filings", {}).get("recent", {})
        return list(zip(recent.get("form", []), recent.get("filingDate", []), recent.get("accessionNumber", [])))[:8]
    except Exception:
        return []


def quote_table(rows: Iterable[QuoteSummary]) -> str:
    lines = [
        "| 标的 | 数据日 | 收盘 | 日涨跌 | 成交量 | 当日区间 | MA20 | MA50 | RSI14 |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.name} ({row.ticker}) | {row.last_date} | {fmt_num(row.close)} {row.currency} | "
            f"{row.change_pct:+.2f}% | {fmt_volume(row.volume)} | {row.day_range} | "
            f"{fmt_num(row.ma20)} | {fmt_num(row.ma50)} | {fmt_num(row.rsi14)} |"
        )
    return "\n".join(lines)


def build_spcx_section() -> str:
    spcx_quote = summarize_quote(SPCX_TICKER, "SpaceX")
    news = yahoo_news(SPCX_TICKER) or yahoo_news("SPAX.PVT")
    filings = sec_recent_filings(SPACEX_CIK)

    if spcx_quote:
        lead = "SPCX 已取得可用交易数据，本节从 IPO 跟踪切换为上市后行情跟踪。仍需额外关注首发后流动性、锁定期安排、指数纳入预期与估值波动。"
        table = quote_table([spcx_quote])
    else:
        lead = "SPCX 当前未取得可靠日线交易数据，本报告按未上市/即将上市标的处理。不生成股价、涨跌幅、均线或 RSI，重点跟踪 SEC 文件、定价区间、上市日期和承销进展。"
        table = ""

    filing_lines = ["- 暂未取得 SEC 最近文件列表。"]
    if filings:
        filing_lines = [f"- {form}，提交日期 {date}，accession {acc}" for form, date, acc in filings[:5]]

    news_lines = ["- 暂未取得 Yahoo Finance 相关新闻。"]
    if news:
        news_lines = [f"- [{title}]({link})" for title, link in news if title]

    return "\n".join(
        [
            "## SPCX / SpaceX IPO 跟踪",
            "",
            lead,
            "",
            table,
            "",
            "近期 SEC 文件：",
            *filing_lines,
            "",
            "近期新闻：",
            *news_lines,
        ]
    ).strip()


def send_slack(markdown: str, report_path: Path) -> None:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    first_lines = "\n".join(markdown.splitlines()[:12])
    requests.post(
        webhook,
        json={"text": f"每日科技股与港股互联网行情日报已生成：{report_path}\n\n{first_lines}"},
        timeout=20,
    ).raise_for_status()


def now_hkt() -> dt.datetime:
    return dt.datetime.now(HKT)


def main() -> None:
    output_dir = Path(os.getenv("REPORT_OUTPUT_DIR", "reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = now_hkt()
    generated = generated_at.strftime("%Y-%m-%d %H:%M HKT")
    us_rows = [row for ticker, name in US_TICKERS.items() if (row := summarize_quote(ticker, name))]
    hk_rows = [row for ticker, name in HK_TICKERS.items() if (row := summarize_quote(ticker, name))]

    news_symbols = ["NVDA", "TSM", "AMD", "AVGO", "SMCI", "TSLA", "ROK"]
    news_lines: list[str] = []
    for symbol in news_symbols:
        for title, link in yahoo_news(symbol, limit=2):
            if title:
                news_lines.append(f"- {symbol}: [{title}]({link})")
    if not news_lines:
        news_lines.append("- 暂未取得自动新闻源；请检查网络或 Yahoo RSS 可用性。")

    report = "\n\n".join(
        [
            "# 美股与港股科技行情日报",
            f"生成时间：{generated}\n\n说明：本云端版每天 09:00 香港时间运行。SPCX 不再映射为 XPEV；若 SPCX 尚无正式行情，则只做 IPO/上市进展跟踪。",
            "## 摘要\n\n- 美股部分聚焦 NVDA、TSM 与 SPCX/SpaceX。\n- 港股互联网部分跟踪阿里巴巴、腾讯、美团。\n- 技术指标使用最近可取得日线计算，若数据源缺失则明确留空。",
            "## 美股重点标的\n\n" + (quote_table(us_rows) if us_rows else "未取得美股日线数据。"),
            build_spcx_section(),
            "## 美股科技、AI 与机器人播报\n\n" + "\n".join(news_lines[:12]),
            "## 港股互联网\n\n" + (quote_table(hk_rows) if hk_rows else "未取得港股日线数据。"),
            "## 催化剂与风险\n\n- AI 算力资本开支、HBM/先进封装供需、云厂商 CAPEX 指引。\n- SPCX 上市定价、首日流动性、锁定期、SEC 文件更新与估值可比性。\n- 港股互联网关注内需修复、竞争强度、回购、监管预期与南向资金。\n\n本报告为行情复盘与观察清单，不构成投资建议。",
        ]
    )

    report_path = output_dir / f"tech_stock_report_{generated_at.date().isoformat()}.md"
    report_path.write_text(report, encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        Path(summary_path).write_text(report, encoding="utf-8")
    send_slack(report, report_path)
    print(report_path)


if __name__ == "__main__":
    main()
