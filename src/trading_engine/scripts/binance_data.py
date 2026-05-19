import polars as pl
import requests
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from tqdm import trange, tqdm

from typing import Optional


def download_and_unzip_data(
    ticker_symbol: str, date: str | datetime, download_dir: Path, cache_dir: Path
) -> pl.DataFrame:
    # Convert date to string
    date_string = date.strftime("%Y-%m-%d") if isinstance(date, datetime) else date

    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / f"{ticker_symbol}-trades-{date_string}.parquet"

    if cache_path.exists():
        return pl.read_parquet(source=cache_path)

    url = f"https://data.binance.vision/data/futures/um/daily/trades/{ticker_symbol}/{ticker_symbol}-trades-{date_string}.zip"

    download_dir.mkdir(exist_ok=True)
    zip_file_path = download_dir / f"{ticker_symbol}-trades-{date_string}.zip"

    # Download zip files
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(zip_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Extract files
    with zipfile.ZipFile(zip_file_path, "r") as zf:
        zf.extractall(download_dir)

    csv_path = download_dir / f"{ticker_symbol}-trades-{date_string}.csv"

    # Load into dataframe
    df = pl.read_csv(
        csv_path,
        schema={
            "id": pl.Int64,
            "price": pl.Float64,
            "qty": pl.Float64,
            "quoteQty": pl.Float64,
            "time": pl.Int64,
            "isBuyMarker": pl.Boolean,
        },
    ).with_columns(pl.from_epoch("time", time_unit="ms").alias("datetime"))

    df.write_parquet(cache_path)
    zip_file_path.unlink(missing_ok=True)
    csv_path.unlink(missing_ok=True)

    return df


def download_trades(
    ticker_symbol: str,
    num_days: int,
    download_dir: str,
    cache_dir: str,
    return_trades: bool = False,
) -> Optional[pl.DataFrame]:
    yesterday = datetime.now() - timedelta(days=1)
    start_date = yesterday - timedelta(days=num_days - 1)

    dfs: list[pl.DataFrame] = []

    for i in trange(num_days, desc=f"Downloading {ticker_symbol}..."):
        current_date = start_date + timedelta(days=i)
        try:
            if return_trades:
                dfs.append(
                    download_and_unzip_data(
                        ticker_symbol, current_date, Path(download_dir), Path(cache_dir)
                    )
                )
            else:
                download_and_unzip_data(
                    ticker_symbol, current_date, Path(download_dir), Path(cache_dir)
                )
        except Exception as e:
            tqdm.write(f"[ERROR] {ticker_symbol} {current_date.date()}: {e}")

    return pl.concat(dfs) if return_trades else None
