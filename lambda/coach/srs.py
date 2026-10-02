# -*- coding: utf-8 -*-
"""Spaced review for every quizzed item: German phrases and vocabulary.

Leitner boxes rather than FSRS: FSRS's gains come from tuning on large
review histories, and this learner has about 150 items and four weeks
(docs/LEARNING_DESIGN.md 4.2). A miss sends an item back to box 1; the
drill also re-asks it later in the same session (successive relearning).

Store format, kept small for DynamoDB:
    store[item_id] = [correct, wrong, last_seen_iso, box]
"""

from datetime import date, timedelta

INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14}     # box -> days until due
MAX_BOX = 4
MAX_ITEMS = 400


def review(store, item_id, correct, today):
    c, w, _, box = store.get(item_id, [0, 0, None, 0])
    box = min(box + 1, MAX_BOX) if correct else 1
    store[item_id] = [c + int(correct), w + int(not correct),
                      today.isoformat(), box]


def due_date(entry, cap=None):
    """When the item is due. cap (e.g. two days before the exam) pulls the
    date in, so everything gets one more review before the exam."""
    last = date.fromisoformat(entry[2])
    due = last + timedelta(INTERVALS.get(entry[3], 1))
    if cap is not None and last < cap:
        due = min(due, cap)
    return due


def _wrong_rate(entry):
    total = entry[0] + entry[1]
    return entry[1] / float(total) if total else 0.0


def pick(store, candidates, today, n, cap=None, new_ok=True):
    """Up to n ids: due items (most overdue, then lowest box, then most
    missed), then unseen candidates in their given order."""
    due = []
    for cid in candidates:
        if cid in store:
            overdue = (today - due_date(store[cid], cap)).days
            if overdue >= 0:
                due.append((-overdue, store[cid][3], -_wrong_rate(store[cid]),
                            cid))
    picks = [cid for _, _, _, cid in sorted(due)][:n]
    if new_ok:
        picks += [cid for cid in candidates if cid not in store][:n - len(picks)]
    return picks


def due_count(store, ids, today, cap=None):
    return sum(1 for i in ids if i in store and due_date(store[i], cap) <= today)


def prune(store, cap=MAX_ITEMS):
    """Drop the best-known items first if the store grows too big."""
    if len(store) <= cap:
        return
    ranked = sorted(store, key=lambda k: (-store[k][3], _wrong_rate(store[k]),
                                          store[k][2]))
    for k in ranked[:len(store) - cap]:
        del store[k]
