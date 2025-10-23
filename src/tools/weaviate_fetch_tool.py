from __future__ import annotations
import json, logging, re, unicodedata
from typing import Any, Dict, List

try:
    from crewai_tools.tools import tool
except Exception:
    from crewai.tools import tool  # type: ignore

from src.vector_store.helpers import get_data_from_objects

logger = logging.getLogger(__name__)

TEXT_KEYS = ("page_text","text","content","page_content","chunk","raw_text","markdown","body")
META_KEYS = ("filename","page","page_number","title","id","uuid")

def _extract_props(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "properties"):
        props = obj.properties() if callable(obj.properties) else obj.properties
        if isinstance(props, dict): return props
    if isinstance(obj, dict):
        return obj["properties"] if isinstance(obj.get("properties"), dict) else obj
    try:
        return dict(obj)
    except Exception:
        return {"_repr": repr(obj)}

def _is_pdf(props: Dict[str, Any]) -> bool:
    fn = (props.get("filename") or props.get("file_name") or "")
    return isinstance(fn, str) and fn.lower().endswith(".pdf")

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii").lower()

def _sentences(text: str) -> List[str]:
    # separa por saltos de línea o puntuación; conserva trozos legibles
    parts = re.split(r'(?<=[\.\!\?])\s+|\n{1,}', text.strip())
    return [p.strip() for p in parts if p.strip()]

def _first_text(props: Dict[str, Any]) -> str | None:
    for k in TEXT_KEYS:
        v = props.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None

def _build_kw(query: str) -> List[str]:
    # palabras de la query (>=4 chars) + sinónimos relevantes PT/ES
    base = [
        "água","agua","esgoto","saneamento","alcantarillado","saneamiento",
        "tarifa","taxa","serviços de água e esgoto","servicos de agua e esgoto","ipca"
    ]
    qwords = [w for w in re.findall(r"\w+", query, flags=re.UNICODE) if len(w) >= 4]
    kws = { _norm(w) for w in (qwords + base) }
    # colapsa acentos (água→agua, serviços→servicos)
    return sorted(kws)

def _filter_on_topic(text: str, kws_norm: List[str]) -> List[str]:
    ntext = _norm(text)
    sents = _sentences(text)
    out: List[str] = []
    for s in sents:
        ns = _norm(s)
        if any(kw in ns for kw in kws_norm):
            # capamos longitud para evitar ruido gigante
            out.append(s if len(s) <= 600 else s[:600] + " …")
    # dedup conservando orden
    seen = set()
    dedup = []
    for s in out:
        k = _norm(s)
        if k not in seen:
            seen.add(k); dedup.append(s)
    return dedup

@tool("weaviate_fetch_append")
def weaviate_fetch_append(query: str) -> str:
    """Fetch PDF text snippets from Weaviate ('PDFDocument') using BM25 for `query`.
    Output:
      - QUERY
      - APPENDED_TEXT: ONLY sentences that match water/sewer/IPCA keywords (accent-insensitive)
      - SUMMARY_JSON: minimal metadata + matched text
    Rules:
      * Use only textual fields (no JSON fallbacks).
      * Skip objects without PDF filename or without matches.
    """
    kws = _build_kw(query)
    objects = get_data_from_objects(query=query, collection_name="PDFDocument", limit=50)

    items: List[Dict[str, Any]] = []
    appended_chunks: List[str] = []

    for obj in (objects or []):
        props = _extract_props(obj)
        if not _is_pdf(props):
            continue
        raw = _first_text(props)
        if not raw:
            continue

        hits = _filter_on_topic(raw, kws)
        if not hits:
            continue

        meta = {k: props.get(k) for k in META_KEYS if k in props}
        items.append({"meta": meta, "hits": hits})

        header = []
        if meta.get("filename"): header.append(f"**File:** {meta['filename']}")
        pg = meta.get("page", meta.get("page_number"))
        if pg is not None: header.append(f"**Page:** {pg}")
        h = " | ".join(header) if header else "**Item**"

        appended_chunks.append(h + "\n- " + "\n- ".join(hits) + "\n")

    appended_text = "\n---\n".join(appended_chunks) if appended_chunks else "(no on-topic passages found)"
    summary_json = json.dumps(items, ensure_ascii=False, indent=2)

    logger.info("weaviate_fetch_append: %d pdf items; appended %d chunks", len(items), len(appended_chunks))
    return (
        f"### QUERY\n{query}\n\n"
        f"### APPENDED_TEXT\n{appended_text}\n\n"
        f"### SUMMARY_JSON\n```json\n{summary_json}\n```\n"
    )
