from engine.common import PROFILES, GROUPS, FEATURE_NAMES, FEATURES, CRITERIA, CRITERION_NAMES

def test_profiles_sum_to_100():
    for name, w in PROFILES.items():
        assert len(w) == 16, name
        assert abs(sum(w) - 100) < 1e-9, name

def test_groups_cover_features_once():
    seen = [i for r in GROUPS.values() for i in r]
    assert sorted(seen) == list(range(1, 35))

def test_feature_names():
    assert len(FEATURE_NAMES) == 34 == len(FEATURES)
    assert len(CRITERION_NAMES) == 16 == len(CRITERIA)
