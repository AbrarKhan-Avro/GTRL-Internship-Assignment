# Task 1 - Algorithmic Trading Adventure (Golden Cross)

## Requirements

* Python 3.10+
* pip install -r requirements.txt

## Setup Instructions

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   # Linux/Mac
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Strategy via `main.py`

1. Example command to run the trading strategy:

   ```bash
   python main.py --symbol AAPL --start 2018-01-01 --end 2023-12-31 --budget 5000 --outdir outputs --show
   ```

2. Optional arguments:

   * `--symbol` : Stock ticker symbol (default: AAPL)
   * `--start`  : Start date in YYYY-MM-DD format (default: 2018-01-01)
   * `--end`    : End date in YYYY-MM-DD format (default: 2023-12-31)
   * `--budget` : Initial capital (default: 5000)
   * `--outdir` : Output directory for logs and charts (default: outputs)
   * `--show`   : Display plots interactively
   * `--ma_short` : Short moving average window (default: 50)
   * `--ma_long`  : Long moving average window (default: 200)

3. Outputs generated:

   * `outputs/AAPL_trades.csv`        -> Trade history
   * `outputs/AAPL_chart.png`         -> Chart with price, MA lines, and buy/sell markers
   * `outputs/AAPL_portfolio.png`     -> Portfolio value over time
   * `outputs/AAPL_report.md`         -> Markdown trade report

## Running the Demo Notebook `demo.ipynb`

1. Launch Jupyter Notebook in your project directory:

   ```bash
   jupyter notebook
   ```

2. Open `demo.ipynb`.

3. Step through each cell in order:

   * **Cell 1:** Set up imports, parameters, and output directory
   * **Cell 2:** Initialize and prepare the strategy
   * **Cell 3:** Inspect the dataset
   * **Cell 4:** Run the backtest
   * **Cell 5:** Display metrics (P&L, trades, win rate, Sharpe ratio, drawdown)
   * **Cell 6:** Plot price, MA lines, and trades
   * **Cell 7:** Plot portfolio value over time
   * **Cell 8:** Save trade log and Markdown report
   * **Cell 9:** Compare multiple MA window performances

4. Outputs from the notebook will be saved in the `outputs` directory, similar to running `main.py`.

## Notes

* The `--show` flag in `main.py` will display plots interactively, which is useful for testing and analysis.
* Adjust `--ma_short` and `--ma_long` to experiment with different moving average strategies.
* The notebook provides a step-by-step interactive demonstration, ideal for understanding the strategy and visualizing trades.
