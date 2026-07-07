"""Smart Money Concepts (SMC) Indicator."""

from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.base import BaseIndicator


class SMC(BaseIndicator):
    """Smart Money Concepts (SMC)

    Description:
    Calculates Smart Money Concepts (SMC) structure such as Fair Value Gaps (FVG),
    Swing Highs/Lows, and Break of Structure / Change of Character (BOS/CHoCH).

    Sources:
    https://github.com/joshyattridge/smart-money-concepts/blob/master/smartmoneyconcepts/smc.py

    Calculation:
    FVG: Identifies imbalances where previous candle's high < next candle's low (bullish gap) or previous low > next high (bearish gap).
    Swing Highs/Lows: Identifies local extrema over a lookback range.
    BOS/CHoCH: Identifies when price breaks past a swing level, signaling trend continuation (BOS) or shift (CHoCH).

    Args:
    df (pd.DataFrame): DataFrame containing 'open', 'high', 'low', 'close', and 'volume' columns.
    swing_length (int): Period for swing high/low detection. Default is 50.
    join_consecutive_fvg (bool): Merge adjacent FVGs. Default is False.
    close_break (bool): Confirm structural breaks on candle close instead of high/low. Default is True.

    Returns:
    pd.DataFrame: Original DataFrame with FVG, Swing, and BOS/CHoCH columns added.
    """

    def calculate(
        self,
        df: pd.DataFrame,
        swing_length: int = 50,
        join_consecutive_fvg: bool = False,
        close_break: bool = True,
        **kwargs: Any,
    ) -> pd.DataFrame:
        # Validate input DataFrame
        ohlc = self._validate_and_lowercase(df, "ohlc")

        smc_df = pd.DataFrame(index=df.index)

        # FVG calculation
        fvg_res = self._fvg(ohlc, join_consecutive_fvg)
        smc_df["fvg"] = fvg_res["FVG"].values
        smc_df["fvg_top"] = fvg_res["Top"].values
        smc_df["fvg_bottom"] = fvg_res["Bottom"].values
        smc_df["fvg_mitigated"] = fvg_res["MitigatedIndex"].values

        # Swing Highs/Lows calculation
        swings = self._swing_highs_lows(ohlc, swing_length)
        smc_df["swing_high_low"] = swings["HighLow"].values
        smc_df["swing_level"] = swings["Level"].values

        # BOS / CHoCH calculation
        bc = self._bos_choch(ohlc, swings, close_break)
        smc_df["bos"] = bc["BOS"].values
        smc_df["choch"] = bc["CHOCH"].values
        smc_df["structure_level"] = bc["Level"].values
        smc_df["structure_broken"] = bc["BrokenIndex"].values

        return smc_df

    def _validate_and_lowercase(
        self, df: pd.DataFrame, columns_required: str = "ohlc"
    ) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy.columns = [c.lower() for c in df_copy.columns]

        inputs = {
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        }
        for char in columns_required:
            col_name = inputs[char]
            if col_name not in df_copy.columns:
                raise LookupError(f"Must have a dataframe column named '{col_name}'")
        return df_copy

    def _fvg(self, ohlc: pd.DataFrame, join_consecutive: bool = False) -> pd.DataFrame:
        fvg = np.where(
            (
                (ohlc["high"].shift(1) < ohlc["low"].shift(-1))
                & (ohlc["close"] > ohlc["open"])
            )
            | (
                (ohlc["low"].shift(1) > ohlc["high"].shift(-1))
                & (ohlc["close"] < ohlc["open"])
            ),
            np.where(ohlc["close"] > ohlc["open"], 1, -1),
            np.nan,
        )

        top = np.where(
            ~np.isnan(fvg),
            np.where(
                ohlc["close"] > ohlc["open"],
                ohlc["low"].shift(-1),
                ohlc["low"].shift(1),
            ),
            np.nan,
        )

        bottom = np.where(
            ~np.isnan(fvg),
            np.where(
                ohlc["close"] > ohlc["open"],
                ohlc["high"].shift(1),
                ohlc["high"].shift(-1),
            ),
            np.nan,
        )

        if join_consecutive:
            for i in range(len(fvg) - 1):
                if fvg[i] == fvg[i + 1]:
                    top[i + 1] = max(top[i], top[i + 1])
                    bottom[i + 1] = min(bottom[i], bottom[i + 1])
                    fvg[i] = top[i] = bottom[i] = np.nan

        mitigated_index = np.zeros(len(ohlc), dtype=np.int32)
        for i in np.where(~np.isnan(fvg))[0]:
            mask = np.zeros(len(ohlc), dtype=np.bool_)
            if fvg[i] == 1:
                mask = ohlc["low"][i + 2 :] <= top[i]
            elif fvg[i] == -1:
                mask = ohlc["high"][i + 2 :] >= bottom[i]
            if np.any(mask):
                j = np.argmax(mask) + i + 2
                mitigated_index[i] = j

        mitigated_index = np.where(np.isnan(fvg), np.nan, mitigated_index)

        return pd.concat(
            [
                pd.Series(fvg, name="FVG"),
                pd.Series(top, name="Top"),
                pd.Series(bottom, name="Bottom"),
                pd.Series(mitigated_index, name="MitigatedIndex"),
            ],
            axis=1,
        )

    def _swing_highs_lows(
        self, ohlc: pd.DataFrame, swing_length: int = 50
    ) -> pd.DataFrame:
        swing_length *= 2
        swing_highs_lows = np.where(
            ohlc["high"]
            == ohlc["high"].shift(-(swing_length // 2)).rolling(swing_length).max(),
            1,
            np.where(
                ohlc["low"]
                == ohlc["low"].shift(-(swing_length // 2)).rolling(swing_length).min(),
                -1,
                np.nan,
            ),
        )

        while True:
            positions = np.where(~np.isnan(swing_highs_lows))[0]

            if len(positions) < 2:
                break

            current = swing_highs_lows[positions[:-1]]
            next_val = swing_highs_lows[positions[1:]]

            highs = ohlc["high"].iloc[positions[:-1]].values
            lows = ohlc["low"].iloc[positions[:-1]].values

            next_highs = ohlc["high"].iloc[positions[1:]].values
            next_lows = ohlc["low"].iloc[positions[1:]].values

            index_to_remove = np.zeros(len(positions), dtype=bool)

            consecutive_highs = (current == 1) & (next_val == 1)
            index_to_remove[:-1] |= consecutive_highs & (highs < next_highs)
            index_to_remove[1:] |= consecutive_highs & (highs >= next_highs)

            consecutive_lows = (current == -1) & (next_val == -1)
            index_to_remove[:-1] |= consecutive_lows & (lows > next_lows)
            index_to_remove[1:] |= consecutive_lows & (lows <= next_lows)

            if not index_to_remove.any():
                break

            swing_highs_lows[positions[index_to_remove]] = np.nan

        positions = np.where(~np.isnan(swing_highs_lows))[0]

        if len(positions) > 0:
            if swing_highs_lows[positions[0]] == 1:
                swing_highs_lows[0] = -1
            if swing_highs_lows[positions[0]] == -1:
                swing_highs_lows[0] = 1
            if swing_highs_lows[positions[-1]] == -1:
                swing_highs_lows[-1] = 1
            if swing_highs_lows[positions[-1]] == 1:
                swing_highs_lows[-1] = -1

        level = np.where(
            ~np.isnan(swing_highs_lows),
            np.where(swing_highs_lows == 1, ohlc["high"], ohlc["low"]),
            np.nan,
        )

        return pd.concat(
            [
                pd.Series(swing_highs_lows, name="HighLow"),
                pd.Series(level, name="Level"),
            ],
            axis=1,
        )

    def _bos_choch(
        self,
        ohlc: pd.DataFrame,
        swing_highs_lows: pd.DataFrame,
        close_break: bool = True,
    ) -> pd.DataFrame:
        swing_highs_lows = swing_highs_lows.copy()

        level_order = []
        highs_lows_order = []

        bos = np.zeros(len(ohlc), dtype=np.int32)
        choch = np.zeros(len(ohlc), dtype=np.int32)
        level = np.zeros(len(ohlc), dtype=np.float32)

        last_positions: list[int] = []

        for i in range(len(swing_highs_lows["HighLow"])):
            if not np.isnan(swing_highs_lows["HighLow"][i]):
                level_order.append(swing_highs_lows["Level"][i])
                highs_lows_order.append(swing_highs_lows["HighLow"][i])
                if len(level_order) >= 4:
                    # bullish bos
                    bos[last_positions[-2]] = (
                        1
                        if (
                            np.all(highs_lows_order[-4:] == [-1, 1, -1, 1])
                            and np.all(
                                level_order[-4]
                                < level_order[-2]
                                < level_order[-3]
                                < level_order[-1]
                            )
                        )
                        else 0
                    )
                    level[last_positions[-2]] = (
                        level_order[-3] if bos[last_positions[-2]] != 0 else 0
                    )

                    # bearish bos
                    bos[last_positions[-2]] = (
                        -1
                        if (
                            np.all(highs_lows_order[-4:] == [1, -1, 1, -1])
                            and np.all(
                                level_order[-4]
                                > level_order[-2]
                                > level_order[-3]
                                > level_order[-1]
                            )
                        )
                        else bos[last_positions[-2]]
                    )
                    level[last_positions[-2]] = (
                        level_order[-3] if bos[last_positions[-2]] != 0 else 0
                    )

                    # bullish choch
                    choch[last_positions[-2]] = (
                        1
                        if (
                            np.all(highs_lows_order[-4:] == [-1, 1, -1, 1])
                            and np.all(
                                level_order[-1]
                                > level_order[-3]
                                > level_order[-4]
                                > level_order[-2]
                            )
                        )
                        else 0
                    )
                    level[last_positions[-2]] = (
                        level_order[-3]
                        if choch[last_positions[-2]] != 0
                        else level[last_positions[-2]]
                    )

                    # bearish choch
                    choch[last_positions[-2]] = (
                        -1
                        if (
                            np.all(highs_lows_order[-4:] == [1, -1, 1, -1])
                            and np.all(
                                level_order[-1]
                                < level_order[-3]
                                < level_order[-4]
                                < level_order[-2]
                            )
                        )
                        else choch[last_positions[-2]]
                    )
                    level[last_positions[-2]] = (
                        level_order[-3]
                        if choch[last_positions[-2]] != 0
                        else level[last_positions[-2]]
                    )

                last_positions.append(i)

        broken = np.zeros(len(ohlc), dtype=np.int32)
        for i in np.where(np.logical_or(bos != 0, choch != 0))[0]:
            mask = np.zeros(len(ohlc), dtype=np.bool_)
            if bos[i] == 1 or choch[i] == 1:
                mask = ohlc["close" if close_break else "high"][i + 2 :] > level[i]
            elif bos[i] == -1 or choch[i] == -1:
                mask = ohlc["close" if close_break else "low"][i + 2 :] < level[i]
            if np.any(mask):
                j = np.argmax(mask) + i + 2
                broken[i] = j
                for k in np.where(np.logical_or(bos != 0, choch != 0))[0]:
                    if k < i and broken[k] >= j:
                        bos[k] = 0
                        choch[k] = 0
                        level[k] = 0

        for i in np.where(
            np.logical_and(np.logical_or(bos != 0, choch != 0), broken == 0)
        )[0]:
            bos[i] = 0
            choch[i] = 0
            level[i] = 0

        bos = np.where(bos != 0, bos, np.nan)
        choch = np.where(choch != 0, choch, np.nan)
        level = np.where(level != 0, level, np.nan)
        broken = np.where(broken != 0, broken, np.nan)

        return pd.concat(
            [
                pd.Series(bos, name="BOS"),
                pd.Series(choch, name="CHOCH"),
                pd.Series(level, name="Level"),
                pd.Series(broken, name="BrokenIndex"),
            ],
            axis=1,
        )
