"""Share prices and market caps from Yahoo Finance (via the yfinance package)."""
import yfinance as yf


def quote(ticker):
    t = yf.Ticker(ticker)
    fi = t.fast_info
    price = float(fi["last_price"])
    def safe(key):
        try:
            v = fi[key]
            return float(v) if v else None
        except Exception:
            return None
    return {"price": price, "market_cap": safe("market_cap"), "shares": safe("shares")}


def history(ticker, period="3y", interval="1wk"):
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    return df["Close"].dropna()
