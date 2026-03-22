"""
main.py — FinPulse Orchestrator

Runs the full pipeline:
1. Load portfolio from CSV
2. Fetch live prices from Yahoo Finance
3. Fetch recent news for each holding
4. Generate AI-powered analysis via Groq
5. Build beautiful HTML report
6. Send via email (or save locally)

Usage:
    python main.py              # Run once (for testing)
    # Automated via GitHub Actions for daily delivery
"""

from portfolio import load_portfolio, fetch_live_data, fetch_news, get_portfolio_summary
from report import generate_analysis, build_html_report
from email_sender import send_report


def run():
    print("=" * 60)
    print("📊 FinPulse — Daily Portfolio Report Agent")
    print("=" * 60 + "\n")

    # Step 1: Load portfolio
    print("Step 1/5: Loading portfolio...")
    portfolio = load_portfolio()

    # Step 2: Fetch live prices
    print("\nStep 2/5: Fetching live market data...")
    portfolio_df = fetch_live_data(portfolio)
    summary = get_portfolio_summary(portfolio_df)

    print(f"\n   💰 Portfolio Value: ₹{summary['total_value']:,.2f}")
    print(f"   📈 Day Change: ₹{summary['total_day_change']:+,.2f} ({summary['day_change_pct']:+.2f}%)")
    print(f"   📊 Total P&L: ₹{summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")

    # Step 3: Fetch news
    print("\nStep 3/5: Fetching news...")
    news = fetch_news(portfolio)

    # Step 4: Generate AI analysis
    print("\nStep 4/5: Generating AI analysis...")
    analysis = generate_analysis(portfolio_df, summary, news)

    # Step 5: Build and send report
    print("\nStep 5/5: Building and sending report...")
    html = build_html_report(portfolio_df, summary, news, analysis)

    # Build subject line
    day_arrow = "▲" if summary["total_day_change"] >= 0 else "▼"
    subject = (
        f"📊 FinPulse — {summary['date']} | "
        f"{day_arrow} ₹{abs(summary['total_day_change']):,.0f} "
        f"({summary['day_change_pct']:+.2f}%)"
    )

    send_report(html, subject)

    print("\n" + "=" * 60)
    print("🎉 Done!")
    print("=" * 60)


if __name__ == "__main__":
    run()
