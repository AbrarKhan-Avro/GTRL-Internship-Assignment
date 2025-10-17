import argparse
from dataclasses import dataclass
import os
import logging
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("TradingStrategy")


@dataclass
class Trade:
    date: pd.Timestamp
    action: str
    price: float
    quantity: int
    cash_after: float
    position_value: float
    total_value: float


class TradingStrategy:
    def __init__(self, symbol: str, start_date: str, end_date: str, budget: float = 5000):
        self.symbol = symbol.upper()
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget

        self.data = None
        self.cash = budget
        self.position = 0
        self.trades = []

    def download_data(self):
        logger.info(f"Downloading data for {self.symbol} from {self.start_date} to {self.end_date} ...")

        df = yf.download(
            self.symbol,
            start=self.start_date,
            end=self.end_date,
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            raise ValueError("No data found — please check the symbol or date range.")

        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]

        df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        df.index = pd.to_datetime(df.index)
        self.data = df
        logger.info(f"Downloaded {len(df)} rows successfully.")

    
    def clean_data(self):
        df = self.data.copy()
        df = df[~df.index.duplicated(keep="first")]
        df = df.sort_index()
        df = df.ffill()
        self.data = df
        logger.info("Data cleaned (duplicates removed, NaNs forward-filled).")

    
    def compute_indicators(self, ma_short=50, ma_long=200):
        df = self.data
        df["MA50"] = df["Adj Close"].rolling(window=ma_short, min_periods=1).mean()
        df["MA200"] = df["Adj Close"].rolling(window=ma_long, min_periods=1).mean()

        df["Prev_MA50"] = df["MA50"].shift(1)
        df["Prev_MA200"] = df["MA200"].shift(1)
        df["Signal"] = 0

        # Golden cross
        df.loc[(df["Prev_MA50"] <= df["Prev_MA200"]) & (df["MA50"] > df["MA200"]), "Signal"] = 1
        # Death cross
        df.loc[(df["Prev_MA50"] >= df["Prev_MA200"]) & (df["MA50"] < df["MA200"]), "Signal"] = -1

        self.data = df
        logger.info(f"Indicators computed using MA{ma_short} & MA{ma_long}.")

    
    def _record_trade(self, date, action, price, quantity):
        if isinstance(price, pd.Series):
            price = float(price.iloc[0])

        pos_value = self.position * price
        total_value = self.cash + pos_value
        trade = Trade(date, action, price, quantity, self.cash, pos_value, total_value)
        self.trades.append(trade)
        logger.info(
            f"{date.date()} | {action:4s} | Price ${price:8.2f} | Qty {quantity:4d} | "
            f"Cash ${self.cash:10.2f} | Total ${total_value:10.2f}"
        )

    
    def run_backtest(self):
        logger.info("Starting backtest simulation...")
        df = self.data

        for date, row in df.iterrows():
            signal = row["Signal"]
            if isinstance(signal, pd.Series):
                signal = int(signal.iloc[0])
            else:
                signal = int(signal) if not pd.isna(signal) else 0

            price = row["Adj Close"]
            if isinstance(price, pd.Series):
                price = float(price.iloc[0])
            else:
                price = float(price)

            # BUY condition
            if signal == 1 and self.position == 0:
                qty = int(self.cash // price)
                if qty > 0:
                    self.cash -= qty * price
                    self.position += qty
                    self._record_trade(date, "BUY", price, qty)

            # SELL condition
            elif signal == -1 and self.position > 0:
                self.cash += self.position * price
                self._record_trade(date, "SELL", price, self.position)
                self.position = 0

        if self.position > 0:
            last_date = df.index[-1]
            last_price = df.iloc[-1]["Adj Close"]
            if isinstance(last_price, pd.Series):
                last_price = float(last_price.iloc[0])
            else:
                last_price = float(last_price)

            self.cash += self.position * last_price
            self._record_trade(last_date, "SELL", last_price, self.position)
            self.position = 0
            logger.info("Force-closed remaining position at end of data.")

        logger.info("Backtest completed successfully.")


    def compute_metrics(self):
        """Compute advanced performance metrics like drawdown, Sharpe ratio, etc."""
        df = self.data.copy()
        portfolio_values = []
        cash = self.budget
        position = 0

        trade_dict = {t.date.strftime("%Y-%m-%d"): t for t in self.trades}

        for date, row in df.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            price = float(row["Adj Close"]) if not np.isscalar(row["Adj Close"]) else row["Adj Close"]

            for t in self.trades:
                if t.date.strftime("%Y-%m-%d") == date_str:
                    if t.action == "BUY":
                        cash -= t.quantity * float(t.price)
                        position += t.quantity
                    elif t.action == "SELL":
                        cash += t.quantity * float(t.price)
                        position -= t.quantity

            total_value = float(cash + position * price)
            portfolio_values.append(total_value)

        df["Portfolio"] = portfolio_values
        df["Daily_Return"] = df["Portfolio"].pct_change().fillna(0)

        # Compute metrics
        total_trades = len(self.trades)
        buy_trades = [t for t in self.trades if t.action == "BUY"]
        sell_trades = [t for t in self.trades if t.action == "SELL"]
        win_trades = 0
        if sell_trades:
            for i in range(min(len(buy_trades), len(sell_trades))):
                if sell_trades[i].price > buy_trades[i].price:
                    win_trades += 1
        win_rate = (win_trades / len(sell_trades)) * 100 if sell_trades else 0

        # Max Drawdown
        cummax = df["Portfolio"].cummax()
        drawdown = (df["Portfolio"] - cummax) / cummax
        max_drawdown = drawdown.min() * 100

        # Sharpe Ratio
        sharpe = (df["Daily_Return"].mean() / df["Daily_Return"].std() * np.sqrt(252)
                if df["Daily_Return"].std() != 0 else 0)

        metrics = {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe
        }
        return df, metrics


    def results(self):
        final_value = self.cash
        pnl = final_value - self.budget
        pnl_pct = (pnl / self.budget) * 100
        df, metrics = self.compute_metrics()

        logger.info("\n=== RESULTS SUMMARY ===")
        logger.info(f"Initial Budget : ${self.budget:,.2f}")
        logger.info(f"Final Value    : ${final_value:,.2f}")
        logger.info(f"Net P&L        : ${pnl:,.2f} ({pnl_pct:.2f}%)")
        logger.info(f"Total Trades   : {metrics['total_trades']}")
        logger.info(f"Win Rate       : {metrics['win_rate']:.2f}%")
        logger.info(f"Max Drawdown   : {metrics['max_drawdown']:.2f}%")
        logger.info(f"Sharpe Ratio   : {metrics['sharpe_ratio']:.2f}")
        return {"final_value": final_value, "pnl": pnl, "pnl_pct": pnl_pct, **metrics}


    def plot_portfolio_value(self, df, path="portfolio_value.png", show=False):
        plt.figure(figsize=(14, 6))
        plt.plot(df.index, df["Portfolio"], label="Portfolio Value", linewidth=2)
        plt.plot(df.index, df["Adj Close"] / df["Adj Close"].iloc[0] * self.budget, 
                label=f"{self.symbol} (Normalized)", linestyle="--")
        plt.title(f"Portfolio Value vs. {self.symbol} Price")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value (USD)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        logger.info(f"Portfolio value plot saved to {path}")
        if show:
            plt.show()
        plt.close()


    def generate_markdown_report(self, path="report.md"):
        if not self.trades:
            logger.warning("No trades executed — no report generated.")
            return

        lines = [f"# {self.symbol} Backtest Report\n",
                "| Date | Action | Price | Quantity | Cash After | Position Value | Total Value | Rationale |",
                "|------|--------|-------|---------|------------|----------------|------------|"]

        for t in self.trades:
            rationale = "Golden Cross detected" if t.action == "BUY" else "Death Cross detected"
            lines.append(f"| {t.date.date()} | {t.action} | {t.price:.2f} | {t.quantity} | {t.cash_after:.2f} | "
                        f"{t.position_value:.2f} | {t.total_value:.2f} | {rationale} |")

        with open(path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Markdown trade report saved to {path}")




    def save_trade_log(self, path="trade_log.csv"):
        if not self.trades:
            logger.warning("No trades executed — nothing to save.")
            return
        df = pd.DataFrame([t.__dict__ for t in self.trades])
        df.to_csv(path, index=False)
        logger.info(f"Trade log saved to {path}")

    def plot_results(self, path="strategy_plot.png"):
        df = self.data
        plt.figure(figsize=(14, 7))
        plt.plot(df.index, df["Adj Close"], label=f"{self.symbol} Adj Close", linewidth=1)
        plt.plot(df.index, df["MA50"], label="MA50", linewidth=1)
        plt.plot(df.index, df["MA200"], label="MA200", linewidth=1)

        buys = [t for t in self.trades if t.action == "BUY"]
        sells = [t for t in self.trades if t.action == "SELL"]

        if buys:
            plt.scatter([t.date for t in buys], [t.price for t in buys],
                        marker="^", color="green", label="BUY", s=100)
        if sells:
            plt.scatter([t.date for t in sells], [t.price for t in sells],
                        marker="v", color="red", label="SELL", s=100)

        plt.title(f"{self.symbol} - Golden Cross Strategy")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        logger.info(f"Plot saved to {path}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="AAPL")
    p.add_argument("--start", default="2018-01-01")
    p.add_argument("--end", default="2023-12-31")
    p.add_argument("--budget", type=float, default=5000.0)
    p.add_argument("--outdir", default="outputs")
    p.add_argument("--show", action="store_true", help="Display chart interactively after backtest")
    p.add_argument("--ma_short", type=int, default=50, help="Short moving average window")
    p.add_argument("--ma_long", type=int, default=200, help="Long moving average window")

    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    strat = TradingStrategy(args.symbol, args.start, args.end, args.budget)
    strat.download_data()
    strat.clean_data()
    strat.compute_indicators()
    strat.run_backtest()
    summary = strat.results()

    # Save files
    trade_log_path = os.path.join(args.outdir, f"{args.symbol}_trades.csv")
    plot_path = os.path.join(args.outdir, f"{args.symbol}_chart.png")
    portfolio_plot_path = os.path.join(args.outdir, f"{args.symbol}_portfolio.png")

    strat.save_trade_log(trade_log_path)
    strat.plot_results(plot_path)
    df, _ = strat.compute_metrics()
    strat.plot_portfolio_value(df, portfolio_plot_path, show=args.show)

    logger.info("\nOutputs:")
    logger.info(f"  - Trade Log: {trade_log_path}")
    logger.info(f"  - Chart    : {plot_path}")
    logger.info(f"  - Portfolio: {portfolio_plot_path}")

if __name__ == "__main__":
    main()