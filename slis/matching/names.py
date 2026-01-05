import re
import os
import warnings
from typing import Any, Sequence

from rapidfuzz import fuzz, distance

try:
    import cudf  # type: ignore
except Exception:  # pragma: no cover
    cudf = None

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None

NOISE_TITLES_RE = re.compile(r"\b(pt|cv|mr|mrs|haji|hj)\b", re.IGNORECASE)


class HybridNameIndex:
    """Index untuk 2-stage matching: filtering cepat (GPU cuDF bila ada) lalu scoring presisi (CPU RapidFuzz).

    Backend dipilih dari:
    - env `SLIS_MATCHER_BACKEND`: 'auto' | 'cudf' | 'pandas'
    - jika 'auto': pakai cuDF bila tersedia, fallback ke pandas.
    """

    def __init__(
        self,
        name_norms: Sequence[str],
        backend: str | None = None,
    ) -> None:
        self._names: list[str] = list(name_norms)
        selected = (backend or os.getenv("SLIS_MATCHER_BACKEND", "auto")).lower().strip()

        if selected not in {"auto", "cudf", "pandas"}:
            selected = "auto"

        self._df = None
        self._series = None

        if selected == "cudf" and cudf is None:
            raise RuntimeError("SLIS_MATCHER_BACKEND=cudf but cuDF is not installed/available")

        if selected in {"auto", "cudf"} and cudf is not None:
            try:
                self._df = cudf.DataFrame({"name_norm": self._names})
                # Force a tiny GPU interaction early so driver/runtime mismatch surfaces here.
                _ = self._df["name_norm"].str.len().head(1).to_pandas()
                self.backend = "cudf"
                return
            except Exception as e:
                if selected == "cudf":
                    raise RuntimeError(
                        f"cuDF backend requested but failed to initialize ({type(e).__name__}: {e})"
                    ) from e
                warnings.warn(
                    f"cuDF backend unavailable ({type(e).__name__}: {e}); falling back to pandas.",
                    RuntimeWarning,
                )

        self.backend = "pandas"
        if pd is None:
            raise RuntimeError("pandas is required for CPU matching backend")
        self._series = pd.Series(self._names, dtype="string")

    def filter_indices(
        self,
        query_norm: str,
        max_candidates: int = 1000,
        tokens_limit: int | None = None,
        length_ratio: float | None = None,
        prefix_len: int = 0,
    ) -> list[int]:
        """Stage-1 filter kandidat (GPU cuDF bila tersedia, fallback pandas).

        Konsep mengikuti HybridMatcher:
        - Split query menjadi token
        - Skip token < 3 chars
        - Gunakan substring token[:4] untuk `contains` (OR)
        - Jika tidak ada token valid -> return []
        """

        q = (query_norm or "").strip()
        if not q:
            return []

        tokens = [t for t in q.split() if t]
        if tokens_limit is not None:
            tokens = tokens[: max(int(tokens_limit), 0)]
        q_len = len(q)
        prefix = q[:prefix_len] if prefix_len and q_len >= prefix_len else ""

        if self.backend == "cudf":
            try:
                if self._df is None:
                    raise RuntimeError("cuDF dataframe not initialized")

                col = self._df["name_norm"]
                mask = None

                # Menggunakan substring matching (4 huruf pertama) agar typo lolos filter.
                for t in tokens:
                    if len(t) < 3: continue  # Skip kata terlalu pendek

                    # Ambil 4 huruf pertama (atau full token jika <4)
                    search_pat = t[:4]

                    # GPU contains (substring match)
                    m = col.str.contains(search_pat, regex=False)
                    mask = m if mask is None else (mask | m)
                if mask is None:
                    return []

                # Length filter optional
                if q_len > 0 and length_ratio is not None:
                    lens = col.str.len()
                    allowed = int(max(1, q_len * float(length_ratio)))
                    mask = mask & ((lens - q_len).abs() <= allowed)

                filtered = self._df[mask]
                
                # [TUNING] Pastikan kandidat cukup banyak untuk CPU Scoring
                if max_candidates and max_candidates > 0:
                    filtered = filtered.head(int(max_candidates))
                
                return filtered.index.to_pandas().tolist()

            except Exception as e:
                warnings.warn(
                    f"cuDF filtering failed ({type(e).__name__}: {e}); switching to pandas backend.",
                    RuntimeWarning,
                )
                self.backend = "pandas"
                if pd is None:
                    raise RuntimeError("pandas is required for CPU matching backend")
                self._series = pd.Series(self._names, dtype="string")

        # pandas backend (CPU Fallback)
        if self._series is None:
            if pd is None:
                raise RuntimeError("pandas is required for CPU matching backend")
            self._series = pd.Series(self._names, dtype="string")
        s = self._series
        mask = None
        for t in tokens:
            if len(t) < 3:
                continue
            search_pat = t[:4]
            m = s.str.contains(search_pat, regex=False, na=False)
            mask = m if mask is None else (mask | m)

        if mask is None:
            return []

        if q_len > 0 and length_ratio is not None:
            lens = s.str.len().fillna(0)
            allowed = int(max(1, q_len * float(length_ratio)))
            mask = mask & (lens.sub(q_len).abs() <= allowed)

        idx = s[mask].index
        if max_candidates and max_candidates > 0:
            idx = idx[: int(max_candidates)]
        return idx.astype(int).tolist()


def normalize_name(name: str) -> str:
    """
    Normalisasi nama (HybridMatcher):
    - lower
    - hilangkan simbol non alfanumerik
    - hilangkan gelar/entitas umum (PT, CV, Mr, Mrs, Haji, Hj)
    - rapikan spasi
    """
    if not isinstance(name, str):
        return ""

    name = name.lower().strip()
    
    # 1. Hapus simbol
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # 2. Hapus gelar/noise words
    name = NOISE_TITLES_RE.sub('', name)
    
    # 3. Rapikan spasi
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


class HybridMatcher:
    """Hybrid matcher untuk name matching (GPU filter + CPU scoring).

    Adaptasi langsung dari konsep yang kamu berikan:
    - Precompute `__norm_name` dari `primary_name`
    - Stage 1: filter kandidat pakai cuDF `contains(token[:4])`
    - Stage 2: score pakai RapidFuzz (JW 60% + TokenSort 40%)
    """

    def __init__(self, sanctions_data: Sequence[dict[str, Any]], name_key: str = "primary_name") -> None:
        self.sanctions: list[dict[str, Any]] = list(sanctions_data)

        self.sanction_norms: list[str] = []
        for s in self.sanctions:
            raw = s.get(name_key) or s.get("primary_name") or s.get("name") or ""
            norm = normalize_name(str(raw))
            s["__norm_name"] = norm
            self.sanction_norms.append(norm)

        self.index = HybridNameIndex(self.sanction_norms)

    def stage1_gpu_filter(self, query_norm: str) -> list[int]:
        return self.index.filter_indices(query_norm)

    def stage2_cpu_scoring(self, query_norm: str, sanction_norm: str) -> dict[str, float]:
        jw_score = distance.JaroWinkler.similarity(query_norm, sanction_norm) * 100.0
        sort_score = float(fuzz.token_sort_ratio(query_norm, sanction_norm))
        final_score = (0.60 * jw_score) + (0.40 * sort_score)
        return {
            "final": round(float(final_score), 2),
            "jw": round(float(jw_score), 2),
            "sort": round(float(sort_score), 2),
        }

    def best_match_normed(self, query_norm: str, threshold: float = 70.0) -> dict[str, Any] | None:
        if not query_norm:
            return None
        candidate_indices = self.stage1_gpu_filter(query_norm)
        best_idx: int | None = None
        best_score = 0.0
        best_scores: dict[str, float] | None = None

        for idx in candidate_indices:
            s_data = self.sanctions[idx]
            scores = self.stage2_cpu_scoring(query_norm, str(s_data.get("__norm_name", "")))
            if scores["final"] >= threshold and scores["final"] > best_score:
                best_score = float(scores["final"])
                best_idx = int(idx)
                best_scores = scores

        if best_idx is None or best_scores is None:
            return None

        return {
            "index": best_idx,
            "scores": best_scores,
        }


def calculate_advanced_name_score(
    name1: str,
    name2: str,
    common_token_weight: float = 0.3
) -> float:
    """
    Wrapper function untuk kalkulasi skor.
    Input strings belum dinormalisasi.
    """
    if not isinstance(name1, str) or not isinstance(name2, str) or not name1 or not name2:
        return 0.0

    norm_name1 = normalize_name(name1)
    norm_name2 = normalize_name(name2)

    if not norm_name1 or not norm_name2:
        return 0.0

    return calculate_advanced_name_score_normed(
        norm_name1,
        norm_name2,
        common_token_weight=common_token_weight,
    )


def calculate_advanced_name_score_normed(
    norm_name1: str,
    norm_name2: str,
    common_token_weight: float = 0.3,
) -> float:
    """
    SCIENTIST APPROVED ALGORITHM:
    Menggunakan kombinasi Jaro-Winkler dan Token Sort Ratio.
    
    Kenapa?
    - Jaro-Winkler: Sangat akurat untuk typo karakter dan singkatan di awal nama.
    - Token Sort: Sangat akurat untuk urutan kata yang terbalik (Joko Widodo vs Widodo Joko).
    
    Bobot:
    - 60% Jaro-Winkler (Prioritas Ejaan)
    - 40% Token Sort (Fleksibilitas Urutan)
    """

    if not norm_name1 or not norm_name2:
        return 0.0

    # 1. Jaro-Winkler Similarity (RapidFuzz implementation is standardized & fast)
    # Mengatasi typo: "Usama" vs "Osama" -> Skor Tinggi
    jw_score = distance.JaroWinkler.similarity(norm_name1, norm_name2) * 100.0

    # 2. Token Sort Ratio
    # Mengatasi urutan: "Widodo Joko" vs "Joko Widodo" -> Skor 100
    sort_score = fuzz.token_sort_ratio(norm_name1, norm_name2)

    # 3. Weighted Average
    # Kita beri bobot lebih ke JW karena akurasi karakter/ejaan adalah kunci di AML.
    final = (0.60 * jw_score) + (0.40 * sort_score)

    return float(final)