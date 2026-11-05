"""Share prices and market caps from Yahoo Finance (via the yfinance package)."""
import yfinance as yf


def quote(ticker):
    t = yf.Ticker(ticker)
    fi = t.fast_info
    price = float(fi["last_price"])
    mcap = fi.get("market_cap")
    return {"price": price, "market_cap": float(mcap) if mcap else None}


def history(ticker, period="3y", interval="1wk"):
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    return df["Close"].dropna()
