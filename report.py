"""
report.py — AI Report Generator

Takes portfolio data and news, sends it to Groq LLM for narrative analysis,
then generates a beautiful HTML email report.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pandas as pd

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"


def generate_analysis(portfolio_df: pd.DataFrame, summary: dict, news: list) -> str:
    """
    Uses Groq LLM to generate a narrative analysis of portfolio performance.
    This is the 'AI' part — it explains WHY your portfolio moved,
    connects news to stock movements, and gives insights.
    """
    llm = ChatGroq(model=GROQ_MODEL, temperature=0.3)

    # Format portfolio data for the LLM
    holdings_text = "\n".join(
        f"- {row['name']} ({row['ticker']}): {row['shares']} shares, "
        f"bought at ₹{row['buy_price']}, now ₹{row['current_price']} "
        f"(today: {row['day_change_pct']:+.2f}%, total P&L: ₹{row['total_pl']:+,.2f})"
        for _, row in portfolio_df.iterrows()
    )

    # Format news
    news_text = "\n".join(
        f"- [{item['stock']}] {item['title']} (via {item['publisher']})"
        for item in news
    ) if news else "No recent news available."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a personal financial analyst writing a daily morning briefing.
Write in a clear, conversational tone — like a smart friend explaining your portfolio over coffee.
Keep it concise (3-4 short paragraphs max). Use specific numbers from the data.

Structure:
1. One sentence summary of the day (how the portfolio did overall)
2. What moved and why (connect stock movements to news if possible)
3. One actionable insight or observation about the portfolio

Do NOT give buy/sell recommendations. Do NOT use generic filler. Be specific to THIS portfolio."""),
        ("human", """Portfolio Summary:
- Total Value: ₹{total_value}
- Day Change: ₹{day_change} ({day_change_pct}%)
- Total P&L: ₹{total_pl} ({total_pl_pct}%)
- Best today: {best}
- Worst today: {worst}

Holdings:
{holdings}

Recent News:
{news}

Write the daily analysis:"""),
    ])

    chain = prompt | llm | StrOutputParser()

    analysis = chain.invoke({
        "total_value": f"{summary['total_value']:,.2f}",
        "day_change": f"{summary['total_day_change']:+,.2f}",
        "day_change_pct": f"{summary['day_change_pct']:+.2f}",
        "total_pl": f"{summary['total_pl']:+,.2f}",
        "total_pl_pct": f"{summary['total_pl_pct']:+.2f}",
        "best": summary["best_performer"],
        "worst": summary["worst_performer"],
        "holdings": holdings_text,
        "news": news_text,
    })

    print("🧠 AI analysis generated")
    return analysis


def build_html_report(portfolio_df: pd.DataFrame, summary: dict, news: list, analysis: str) -> str:
    """
    Builds a beautiful HTML email report.
    Inline CSS because email clients don't support external stylesheets.
    """

    # Build holdings table rows
    holdings_rows = ""
    for _, row in portfolio_df.iterrows():
        day_color = "#22c55e" if row["day_change_pct"] >= 0 else "#ef4444"
        day_arrow = "▲" if row["day_change_pct"] >= 0 else "▼"
        pl_color = "#22c55e" if row["total_pl"] >= 0 else "#ef4444"

        holdings_rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px 8px; font-weight: 600;">{row['name']}</td>
            <td style="padding: 12px 8px; text-align: center;">{row['shares']}</td>
            <td style="padding: 12px 8px; text-align: right;">₹{row['buy_price']:,.2f}</td>
            <td style="padding: 12px 8px; text-align: right;">₹{row['current_price']:,.2f}</td>
            <td style="padding: 12px 8px; text-align: right; color: {day_color}; font-weight: 600;">
                {day_arrow} {row['day_change_pct']:+.2f}%
            </td>
            <td style="padding: 12px 8px; text-align: right; color: {pl_color}; font-weight: 600;">
                ₹{row['total_pl']:+,.2f}
            </td>
        </tr>"""

    # Build news section
    news_html = ""
    if news:
        for item in news[:8]:  # Limit to 8 headlines
            news_html += f"""
            <li style="margin-bottom: 8px;">
                <a href="{item['link']}" style="color: #3b82f6; text-decoration: none;">{item['title']}</a>
                <span style="color: #9ca3af; font-size: 12px;"> — {item['stock']} via {item['publisher']}</span>
            </li>"""
    else:
        news_html = "<li>No recent news available.</li>"

    # Summary colors
    day_color = "#22c55e" if summary["total_day_change"] >= 0 else "#ef4444"
    pl_color = "#22c55e" if summary["total_pl"] >= 0 else "#ef4444"
    day_arrow = "▲" if summary["total_day_change"] >= 0 else "▼"

    # Format analysis paragraphs
    analysis_html = "".join(f"<p style='margin: 0 0 12px 0; line-height: 1.6;'>{p.strip()}</p>"
                           for p in analysis.split("\n") if p.strip())

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 640px; margin: 0 auto; background-color: #ffffff;">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 32px 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">📊 FinPulse</h1>
                <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 14px;">Daily Portfolio Report — {summary['date']}</p>
            </div>

            <!-- Summary Cards -->
            <div style="padding: 24px; display: flex; gap: 12px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="33%" style="padding: 4px;">
                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Portfolio Value</p>
                            <p style="margin: 4px 0 0 0; font-size: 20px; font-weight: 700; color: #1e293b;">₹{summary['total_value']:,.0f}</p>
                        </div>
                    </td>
                    <td width="33%" style="padding: 4px;">
                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Day Change</p>
                            <p style="margin: 4px 0 0 0; font-size: 20px; font-weight: 700; color: {day_color};">{day_arrow} ₹{abs(summary['total_day_change']):,.0f}</p>
                            <p style="margin: 2px 0 0 0; font-size: 12px; color: {day_color};">{summary['day_change_pct']:+.2f}%</p>
                        </div>
                    </td>
                    <td width="33%" style="padding: 4px;">
                        <div style="background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Total P&L</p>
                            <p style="margin: 4px 0 0 0; font-size: 20px; font-weight: 700; color: {pl_color};">₹{summary['total_pl']:+,.0f}</p>
                            <p style="margin: 2px 0 0 0; font-size: 12px; color: {pl_color};">{summary['total_pl_pct']:+.2f}%</p>
                        </div>
                    </td>
                </tr>
                </table>
            </div>

            <!-- AI Analysis -->
            <div style="padding: 0 24px 24px 24px;">
                <h2 style="font-size: 16px; color: #1e293b; margin: 0 0 12px 0;">🧠 AI Analysis</h2>
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 8px 8px 0; color: #1e293b; font-size: 14px;">
                    {analysis_html}
                </div>
            </div>

            <!-- Holdings Table -->
            <div style="padding: 0 24px 24px 24px;">
                <h2 style="font-size: 16px; color: #1e293b; margin: 0 0 12px 0;">📋 Holdings</h2>
                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 13px; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8fafc; border-bottom: 2px solid #e5e7eb;">
                            <th style="padding: 10px 8px; text-align: left; color: #64748b; font-weight: 600;">Stock</th>
                            <th style="padding: 10px 8px; text-align: center; color: #64748b; font-weight: 600;">Qty</th>
                            <th style="padding: 10px 8px; text-align: right; color: #64748b; font-weight: 600;">Avg Cost</th>
                            <th style="padding: 10px 8px; text-align: right; color: #64748b; font-weight: 600;">Current</th>
                            <th style="padding: 10px 8px; text-align: right; color: #64748b; font-weight: 600;">Day</th>
                            <th style="padding: 10px 8px; text-align: right; color: #64748b; font-weight: 600;">P&L</th>
                        </tr>
                    </thead>
                    <tbody>
                        {holdings_rows}
                    </tbody>
                </table>
            </div>

            <!-- News -->
            <div style="padding: 0 24px 24px 24px;">
                <h2 style="font-size: 16px; color: #1e293b; margin: 0 0 12px 0;">📰 News Affecting Your Portfolio</h2>
                <ul style="padding-left: 20px; margin: 0; font-size: 13px; color: #374151;">
                    {news_html}
                </ul>
            </div>

            <!-- Footer -->
            <div style="background: #f8fafc; padding: 20px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                    Generated by FinPulse — AI-powered portfolio monitoring agent<br>
                    ⚠️ This is automated analysis, not financial advice.
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    print("📧 HTML report generated")
    return html
