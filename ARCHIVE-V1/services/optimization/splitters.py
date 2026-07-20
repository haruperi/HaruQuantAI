"""Time-series splitting tools for optimization workflows.

Purpose:
    Provide rolling and expanding split helpers used by optimization and
    walk-forward validation workflows.

Classes and functions:
    SplitterResult: Class. Holds split index windows and plotting behavior.
    splitter_from_rolling: Function. Create rolling train/test windows.
    splitter_from_expanding: Function. Create expanding train/test windows.
    splitter_rolling_split: Function. Split DataFrame windows into train/test parts.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class SplitterResult:
    """Hold time-series split windows and plotting behavior."""

    def __init__(
        self,
        index: pd.Index,
        splits: list[dict[str, pd.Index]],
        set_labels: list[str],
    ) -> None:
        """Initialize a split result container."""
        self.index = index
        self.splits = splits
        self.set_labels = set_labels

    def __len__(self) -> int:
        """Return the number of generated split windows."""
        return len(self.splits)

    def __getitem__(self, index: int) -> dict[str, pd.Index]:
        """Return one split window by position."""
        return self.splits[index]

    def plots(self) -> Any:
        """Visualize split windows with matplotlib.

        Purpose:
            Plot rolling or expanding split windows for inspection.

        Tool class:
            read_only

        Risk level:
            low

        Approval required:
            none

        Side effects:
            Creates a matplotlib axis object.
        """
        import matplotlib.patches as mpatches
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 6))
        colors = {"train": "steelblue", "test": "orange", "valid": "green"}

        for row_index, split in enumerate(self.splits[::-1]):
            for label, sub_index in split.items():
                if len(sub_index) == 0:
                    continue
                start_pos = self.index.get_loc(sub_index[0])
                end_pos = self.index.get_loc(sub_index[-1])
                ax.barh(
                    row_index,
                    end_pos - start_pos,
                    left=start_pos,
                    color=colors.get(label, "gray"),
                    alpha=0.8,
                )

        ax.set_yticks(range(len(self.splits)))
        ax.set_yticklabels(
            [
                f"Split {len(self.splits) - row_index}"
                for row_index in range(len(self.splits))
            ]
        )
        ax.set_xlabel("Bars")
        ax.set_title("Time Series Splits Visualization")
        patches = [
            mpatches.Patch(color=colors.get(label, "gray"), label=label.capitalize())
            for label in self.set_labels
        ]
        ax.legend(handles=patches, loc="upper right")
        return ax


def _to_int_window(value: int | str, index: pd.Index) -> int:
    """Convert integer or timedelta-like windows to row counts."""
    if isinstance(value, str):
        delta = pd.to_timedelta(value)
        avg_delta = (index[-1] - index[0]) / (len(index) - 1)
        return int(delta / avg_delta)
    return int(value)


def splitter_from_rolling(
    index: pd.Index,
    length: int | str,
    split: float | str = 0.5,
    step: int | str = 1,
    set_labels: list[str] | None = None,
    freq: str | None = None,
) -> SplitterResult:
    """Create rolling time-series train/test windows.

    Purpose:
        Build deterministic rolling windows for validation and optimization.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """
    labels = set_labels or ["train", "test"]
    split_index = pd.to_datetime(index) if freq else index
    window_length = _to_int_window(length, split_index)
    step_length = _to_int_window(step, split_index)
    split_idx = (
        int(window_length * split)
        if isinstance(split, float)
        else _to_int_window(split, split_index)
    )

    splits: list[dict[str, pd.Index]] = []
    for start in range(0, len(split_index) - window_length + 1, step_length):
        window = split_index[start : start + window_length]
        splits.append({labels[0]: window[:split_idx], labels[1]: window[split_idx:]})

    return SplitterResult(split_index, splits, labels)


def splitter_from_expanding(
    index: pd.Index,
    min_length: int | str,
    split: float | str = 0.5,
    step: int | str = 1,
    set_labels: list[str] | None = None,
) -> SplitterResult:
    """Create expanding time-series train/test windows.

    Purpose:
        Build deterministic expanding windows for validation and optimization.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """
    return splitter_from_rolling(index, min_length, split, step, set_labels)


def splitter_rolling_split(
    data: Any,
    window_len: int,
    set_lens: tuple[int, ...] = (1, 1),
    left_to_right: bool = False,
    step: int = 1,
) -> list[dict[str, pd.DataFrame]]:
    """Split tabular data into rolling train/test or train/valid/test windows.

    Purpose:
        Produce deterministic DataFrame slices for optimization validation.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """
    df = data.df if hasattr(data, "df") else data
    splits: list[dict[str, pd.DataFrame]] = []
    total_set_len = sum(set_lens)
    unit = window_len / total_set_len
    actual_lens = [int(length * unit) for length in set_lens]
    indices = (
        range(0, len(df) - window_len + 1, step)
        if left_to_right
        else range(len(df) - window_len, -1, -step)
    )

    for start_index in indices:
        current_window = df.iloc[start_index : start_index + window_len]
        split: dict[str, pd.DataFrame] = {}
        cursor = 0
        names = ["train", "valid", "test"] if len(set_lens) == 3 else ["train", "test"]
        for name, length in zip(names, actual_lens, strict=False):
            split[name] = current_window.iloc[cursor : cursor + length]
            cursor += length
        splits.append(split)

    return splits if left_to_right else splits[::-1]


__all__ = [
    "SplitterResult",
    "splitter_from_expanding",
    "splitter_from_rolling",
    "splitter_rolling_split",
]
