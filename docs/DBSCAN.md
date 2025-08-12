## DBSCAN Improvements (August 2025)

### Overview

The clustering pipeline now uses a robust DBSCAN parameter search to avoid pathological single-cluster collapse and eps=0 errors. The backend will always return a valid clustering result (never a 400 due to DBSCAN params) and logs detailed debug information for every analyze request.

### Key Changes

- **Multi-Percentile Eps Search:**
  - Instead of a fixed k-distance percentile, DBSCAN now tries eps at percentiles [60, 70, 75, 80, 85, 90, 95] and 1–2 min_samples values.
  - Each candidate is scored by silhouette, cluster count (softly preferring 2–6), and penalizing high noise.
  - The best valid configuration is chosen; if none produce ≥2 clusters, fallback to KMeans.
- **Safety Guards:**
  - All eps values are forced > 0 using a nonzero-distance fallback and a final floor (1e-4).
  - Any DBSCAN ValueError triggers a clean fallback to KMeans (never a 400 error).
- **Observability:**
  - Prints `DBSCAN DEBUG: ...` lines for k-dist quantiles, trial results, chosen eps/min_samples, and cluster count.
  - `ANALYZE DEBUG: ...` summary is printed for every analyze call, showing method, k, eps, min_samples, fallback, and silhouette.
  - The API response metadata includes `eps_percentile` and fallback reasons.

### Example Log Output

```
DBSCAN DEBUG: n_samples=40 n_neighbors=4 kdist q25=0.0123 q50=0.0234 q75=0.0456 q90=0.0789
DBSCAN DEBUG: produced 4 clusters (1-based labels)
ANALYZE DEBUG: method=dbscan k=4 eps=0.0456 min_samples=4 fallback=False clusters=4 silhouette=0.41
```

### User Impact

- DBSCAN will no longer collapse to a single cluster for all playlists unless the data is truly degenerate.
- No more 400 errors for eps=0.0 or other DBSCAN parameter issues.
- Fallback to KMeans is explicit and logged if DBSCAN cannot find a valid multi-cluster solution.

### Implementation Location

- All logic is in `backend/services/clustering.py` (`_apply_clustering_algorithm` method, DBSCAN branch).
- Logging and debug prints are visible in both backend logs and dev console.

---

_Last updated: August 12, 2025_
