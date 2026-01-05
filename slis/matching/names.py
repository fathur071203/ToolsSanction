import re
import os
import warnings
from typing import Iterable, Sequence

from rapidfuzz import fuzz, distance

try:
    import cudf  # type: ignore
except Exception:  # pragma: no cover
    cudf = None

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None

# Variants nama dari kode Streamlit
NAME_VARIANTS = {
    'mohammad': 'muhammad', 'mohamad': 'muhammad', 'mohamed': 'muhammad',
    'mochammad': 'muhammad', 'mochamad': 'muhammad', 'mahomet': 'muhammad',
    'mehmed': 'muhammad', 'mohammed': 'muhammad', 'moh': 'muhammad',
    'md': 'muhammad', 'abd': 'abdul', 'bin': '', 'binti': ''
}

COMMON_TOKENS = {'muhammad', 'abdul', 'ali', 'ahmad', 'bin', 'binti'}


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

        if selected in {"auto", "cudf"} and cudf is not None:
            try:
                self._df = cudf.DataFrame({"name_norm": self._names})
                # Force a tiny GPU interaction early so driver/runtime mismatch surfaces here.
                _ = self._df["name_norm"].str.len().head(1).to_pandas()
                self.backend = "cudf"
                return
            except Exception as e:
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
        tokens_limit: int = 3,  # [TUNING] Naikkan limit token agar lebih teliti
        length_ratio: float = 0.30,
        prefix_len: int = 3,
    ) -> list[int]:
        """Return indeks kandidat yang *aman* (toleran typo), tapi drastis mengurangi space."""

        q = (query_norm or "").strip()
        if not q:
            return []

        tokens = [t for t in q.split() if t]
        tokens = tokens[: max(tokens_limit, 0)]
        q_len = len(q)
        prefix = q[:prefix_len] if q_len >= prefix_len else ""

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
                # -----------------------------------------------

                # Fallback: jika mask None (misal kata terlalu pendek semua),
                # gunakan prefix match atau ambil semua (notnull)
                if mask is None:
                    if prefix:
                        m = col.str.contains(prefix, regex=False)
                        mask = m
                    else:
                        mask = col.notnull()

                # Length Filter (Opsional: menjaga agar kandidat tidak terlalu beda panjangnya)
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
            m = s.str.contains(t, regex=False, na=False)
            mask = m if mask is None else (mask | m)

        if prefix:
            m = s.str.contains(prefix, regex=False, na=False)
            mask = m if mask is None else (mask | m)

        if mask is None:
            mask = s.notna()

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
    Normalisasi nama:
    - lower
    - hilangkan simbol non alfanumerik
    - [BARU] hilangkan gelar/entitas (PT, CV, dll)
    - mapping varian (NAME_VARIANTS)
    - buang token kosong
    """
    if not isinstance(name, str):
        return ""

    name = name.lower().strip()
    
    # 1. Hapus simbol
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # 2. [BARU] Hapus Gelar/Noise Words (PT, CV, Mr, Mrs, Haji, dll)
    # Ini penting agar "PT. Maju" vs "Maju" skornya tinggi.
    name = re.sub(r'\b(pt|cv|ltd|inc|mr|mrs|haji|hj|ud)\b', '', name)
    
    # 3. Rapikan spasi
    name = re.sub(r'\s+', ' ', name).strip()
    
    tokens = name.split()

    normalized_tokens = [
        NAME_VARIANTS.get(token, token)
        for token in tokens
        if NAME_VARIANTS.get(token, token)  # buang token yang jadi string kosong (bin/binti)
    ]

    return ' '.join(normalized_tokens)


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