# -*- coding: utf-8 -*-
from __future__ import annotations
import re, logging
log = logging.getLogger(__name__)

_SOURCE_PATTERN = re.compile(
    r'\[(?:raster|rainfall|osm|report):[^\]]+\]'
    + r'|'
    + r'\[(?:\w+_r\d+|live_\d+)\]'
)
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?\u0964])\s+')

def _has_source(sentence: str) -> bool:
    return bool(_SOURCE_PATTERN.search(sentence))

def _verify_text(text: str, field_name: str):
    if not text:
        return text, []
    sentences = _SENTENCE_SPLIT.split(text.strip())
    kept, dropped = [], []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if _has_source(s):
            kept.append(s)
        else:
            dropped.append(s)
            log.warning("verify: DROPPED in %s: %r", field_name, s[:80])
    return " ".join(kept), dropped

def run(sitrep):
    all_dropped = []
    updates = {}
    for field in ("summary_en", "summary_hi", "whatsapp_brief_en", "whatsapp_brief_hi"):
        original = getattr(sitrep, field, "")
        cleaned, dropped = _verify_text(original, field)
        all_dropped.extend(dropped)
        if dropped:
            updates[field] = cleaned
    if updates:
        sitrep = sitrep.model_copy(update=updates)
    log.info("verify: dropped %d unsourced sentences", len(all_dropped))
    return sitrep, all_dropped

def inject_unsourced_test(sitrep):
    return sitrep.model_copy(
        update={"summary_en": sitrep.summary_en + " The situation is improving rapidly."}
    )
