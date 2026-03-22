"""
portfolio.py — Portfolio Data Engine

Loads your holdings from CSV, fetches live prices from Yahoo Finance,
and calculates all P&L metrics. No API key needed — yfinance is free.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime


def load_portfolio(csv_path: str = "portfolio.csv") -> pd.DataFrame:
    """Load holdings from CSV file."""
    df = pd.read_csv(csv_path)
    print(f"📂 Loaded {len(df)} holdings from {csv_path}")
    return df


def fetch_live_data(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch current prices and daily change for each holding.
    Uses yfinance — completely free, no API key needed.
    """
    results = []

    for _, row in portfolio.iterrows():
        ticker = row["ticker"]
        print(f"📈 Fetching data for {row['name']} ({ticker})...")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get current price and previous close
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)

            # Calculate metrics
            shares = row["shares"]
            buy_price = row["buy_price"]

            day_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            day_change_val = (current_price - prev_close) * shares
            total_pl = (current_price - buy_price) * shares
            total_pl_pct = ((current_price - buy_price) / buy_price * 100) if buy_price else 0
            current_value = current_price * shares
            invested_value = buy_price * shares

            results.append({
                "ticker": ticker,
                "name": row["name"],
                "shares": shares,
                "buy_price": buy_price,
                "current_price": round(current_price, 2),
                "prev_close": round(prev_close, 2),
                "day_change_pct": round(day_change_pct, 2),
                "day_change_val": round(day_change_val, 2),
                "total_pl": round(total_pl, 2),
                "total_pl_pct": round(total_pl_pct, 2),
                "current_value": round(current_value, 2),
                "invested_value": round(invested_value, 2),
            })

        except Exception as e:
            print(f"   ⚠️ Error fetching {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "name": row["name"],
                "shares": row["shares"],
                "buy_price": row["buy_price"],
                "current_price": 0,
                "prev_close": 0,
                "day_change_pct": 0,
                "day_change_val": 0,
                "total_pl": 0,
                "total_pl_pct": 0,
                "current_value": 0,
                "invested_value": 0,
            })

    return pd.DataFrame(results)


def fetch_news(portfolio: pd.DataFrame, max_per_stock: int = 3) -> list:
    """
    Fetch recent news headlines for each stock using yfinance.
    Returns a list of dicts with title, link, publisher, and stock name.
    """
    all_news = []

    for _, row in portfolio.iterrows():
        ticker = row["ticker"]
        name = row["name"]
        print(f"📰 Fetching news for {name}...")

        try:
            stock = yf.Ticker(ticker)
            news_items = stock.news or []

            for item in news_items[:max_per_stock]:
                content = item.get("content", {})
                all_news.append({
                    "stock": name,
                    "title": content.get("title", "No title"),
                    "publisher": content.get("provider", {}).get("displayName", "Unknown"),
                    "link": content.get("canonicalUrl", {}).get("url", ""),
                })

        except Exception as e:
            print(f"   ⚠️ Error fetching news for {ticker}: {e}")

    print(f"✅ Found {len(all_news)} news articles total")
    return all_news


def get_portfolio_summary(df: pd.DataFrame) -> dict:
    """Calculate portfolio-level summary metrics."""
    total_value = df["current_value"].sum()
    total_invested = df["invested_value"].sum()
    total_day_change = df["day_change_val"].sum()
    total_pl = df["total_pl"].sum()
    total_pl_pct = ((total_value - total_invested) / total_invested * 100) if total_invested else 0
    day_change_pct = (total_day_change / (total_value - total_day_change) * 100) if total_value else 0

    # Best and worst performers today
    best = df.loc[df["day_change_pct"].idxmax()]
    worst = df.loc[df["day_change_pct"].idxmin()]

    return {
        "total_value": round(total_value, 2),
        "total_invested": round(total_invested, 2),
        "total_day_change": round(total_day_change, 2),
        "day_change_pct": round(day_change_pct, 2),
        "total_pl": round(total_pl, 2),
        "total_pl_pct": round(total_pl_pct, 2),
        "best_performer": f"{best['name']} ({best['day_change_pct']:+.2f}%)",
        "worst_performer": f"{worst['name']} ({worst['day_change_pct']:+.2f}%)",
        "date": datetime.now().strftime("%B %d, %Y"),
    }


if __name__ == "__main__":
    # Quick test
    portfolio = load_portfolio()
    df = fetch_live_data(portfolio)
    summary = get_portfolio_summary(df)
    news = fetch_news(portfolio)

    print("\n" + "=" * 60)
    print(f"Portfolio Value: ₹{summary['total_value']:,.2f}")
    print(f"Day Change: ₹{summary['total_day_change']:,.2f} ({summary['day_change_pct']:+.2f}%)")
    print(f"Total P&L: ₹{summary['total_pl']:,.2f} ({summary['total_pl_pct']:+.2f}%)")
    print(f"Best today: {summary['best_performer']}")
    print(f"Worst today: {summary['worst_performer']}")
    print(f"\nNews articles: {len(news)}")
