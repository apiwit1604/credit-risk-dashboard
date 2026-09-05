# -*- coding: utf-8 -*-
"""
Utilities for carrying the 1-year transition matrix and the credit-spread
curve over to a *new* rating scale — used by the Settings page's
"Confirm rating scale" action so adding, removing, renaming, or reordering
a rating doesn't require manually resizing the matrix/curve by hand.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd

# Placeholder spread for a rating that has no prior data to carry over —
# meant to be edited afterward on the Settings page, not treated as
# calibrated.
DEFAULT_NEW_RATING_SPREAD_BPS: float = 100.0


def reshape_transition_matrix(
    old_matrix: np.ndarray,
    old_labels: Sequence[str],
    new_labels: Sequence[str],
) -> np.ndarray:
    """Carry a transition matrix over to a new rating scale.

    Ratings present in both `old_labels` and `new_labels` keep their
    existing row/column values — row order, column order, and the number
    of ratings can all change at once. A rating with no counterpart in
    `old_labels` (new, or a renamed one — renaming isn't distinguished
    from remove+add here, since matching is by label text) gets a neutral
    "100% stays in the same rating" row as a starting point. A rating
    that's removed just drops out, which can leave surviving rows summing
    to less than 1 — that's caught by the row-sum check already on the
    Settings page, not silently re-normalized here.
    """
    old_labels, new_labels = list(old_labels), list(new_labels)
    old_df = pd.DataFrame(np.asarray(old_matrix, dtype=float), index=old_labels, columns=old_labels)
    new_df = pd.DataFrame(0.0, index=new_labels, columns=new_labels)

    common = [r for r in new_labels if r in old_labels]
    for row in common:
        new_df.loc[row, common] = old_df.loc[row, common]

    for row in new_labels:
        if row not in old_labels:
            new_df.loc[row, row] = 1.0

    return new_df.to_numpy()


def reshape_credit_spread_data(
    old_credit_spread_data: Sequence[Tuple[float, ...]],
    old_non_default_labels: Sequence[str],
    new_non_default_labels: Sequence[str],
    default_spread_bps: float = DEFAULT_NEW_RATING_SPREAD_BPS,
) -> List[Tuple[float, ...]]:
    """Carry the credit-spread curve over to a new (non-default) rating
    scale, keeping the same tenor grid untouched. A rating with no
    counterpart in `old_non_default_labels` gets a flat placeholder spread
    across every tenor.
    """
    old_non_default_labels = list(old_non_default_labels)
    new_non_default_labels = list(new_non_default_labels)
    tenors = [row[0] for row in old_credit_spread_data]
    old_df = pd.DataFrame(
        [row[1:] for row in old_credit_spread_data], index=tenors, columns=old_non_default_labels,
    )

    new_df = pd.DataFrame(index=tenors, columns=new_non_default_labels, dtype=float)
    for col in new_non_default_labels:
        new_df[col] = old_df[col] if col in old_non_default_labels else default_spread_bps

    return [tuple([tenor] + list(new_df.loc[tenor])) for tenor in tenors]


def confirm_rating_scale(draft_rating_labels: Sequence[str], session_state) -> List[str]:
    """Validate a candidate rating scale and, if valid, apply it: reshape
    the transition matrix and credit-spread curve in `session_state` to
    match, and update `session_state["rating_labels"]`.

    `session_state` only needs to support item access/assignment (a plain
    dict works fine, which is what makes this testable without a running
    Streamlit script) — in the app it's `st.session_state`.

    Returns a list of validation error messages. An empty list means the
    new scale was valid and has already been applied; a non-empty list
    means nothing was changed.
    """
    draft_rating_labels = [str(r).strip() for r in draft_rating_labels if str(r).strip()]

    errors: List[str] = []
    if len(draft_rating_labels) < 2:
        errors.append("Need at least 2 ratings (one non-default rating plus \"D\").")
    if not draft_rating_labels or draft_rating_labels[-1] != "D":
        errors.append("The last rating must be \"D\" (the absorbing default state).")
    if len(draft_rating_labels) != len(set(draft_rating_labels)):
        errors.append("Rating names must be unique — no duplicates.")
    if errors:
        return errors

    old_labels = list(session_state["rating_labels"])
    old_non_default = [r for r in old_labels if r != "D"]
    new_non_default = [r for r in draft_rating_labels if r != "D"]

    session_state["transition_matrix"] = reshape_transition_matrix(
        session_state["transition_matrix"], old_labels, draft_rating_labels,
    )
    session_state["credit_spread_data"] = reshape_credit_spread_data(
        session_state["credit_spread_data"], old_non_default, new_non_default,
    )
    session_state["rating_labels"] = draft_rating_labels
    return []
