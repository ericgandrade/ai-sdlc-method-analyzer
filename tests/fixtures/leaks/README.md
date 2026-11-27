# Leak fixtures

The positive fixtures for `tests/test_leakcheck.py` (home paths, emails,
credential shapes, URLs with userinfo, denylist terms) are assembled from
fragments at test time and written into a temporary directory. They are never
committed, so the repository itself stays clean and no secret scanner fires.

`near-miss.txt` holds text that must not hit any built-in pattern.
