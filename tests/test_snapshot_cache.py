import json
from market_data_provider import provide_historical_market_data
from market_data_provider.snapshot_cache import VerifiedSnapshotCache
from model_flows import MarketDataRequest
from tests.synthetic_market import write_synthetic_snapshot


def test_cache_hit_matches_current_provider_and_is_not_mutable(tmp_path):
    write_synthetic_snapshot(tmp_path, days=20, symbols=['VTI'])
    req = MarketDataRequest(['VTI']); events = []
    cache = VerifiedSnapshotCache(lambda s, a, b: events.append(s))
    first = cache(req, snapshot_directory=tmp_path)
    expected = provide_historical_market_data(req, snapshot_directory=tmp_path)
    assert first == expected
    first.series['VTI'].adjusted_closes[0] = -1
    assert cache(req, snapshot_directory=tmp_path) == expected
    assert cache.hits == 1 and cache.misses == 1
    assert events == ['SIM.C.12.1', 'SIM.C.12.2', 'SIM.C.12.3', 'SIM.C.12.4',
                      'SIM.C.12.5', 'SIM.C.12.1', 'SIM.C.12.6', 'SIM.C.12.5']


def test_cache_invalidates_on_file_tampering(tmp_path):
    m = write_synthetic_snapshot(tmp_path, days=20, symbols=['VTI'])
    req = MarketDataRequest(['VTI']); cache = VerifiedSnapshotCache()
    assert cache(req, snapshot_directory=tmp_path).series
    with (tmp_path / m['file']).open('a') as f:
        f.write('VTI,2026-11-02,123\n')
    result = cache(req, snapshot_directory=tmp_path)
    assert not result.series
    assert 'fingerprint' in result.limitations[0]
    assert cache._data is None


def test_cache_key_includes_admission_threshold_and_symbols(tmp_path):
    write_synthetic_snapshot(tmp_path, days=20, symbols=['VTI'])
    cache = VerifiedSnapshotCache()
    assert cache(MarketDataRequest(['VTI']), snapshot_directory=tmp_path).series
    assert not cache(MarketDataRequest(['VTI']), snapshot_directory=tmp_path,
                     minimum_observations=100).series
    assert not cache(MarketDataRequest(['MISSING']), snapshot_directory=tmp_path).series
    assert cache.misses == 3


def test_cache_refreshes_changed_manifest_and_snapshot(tmp_path):
    write_synthetic_snapshot(tmp_path, days=20, seed=1, symbols=['VTI'])
    cache = VerifiedSnapshotCache(); req = MarketDataRequest(['VTI'])
    first = cache(req, snapshot_directory=tmp_path)
    write_synthetic_snapshot(tmp_path, days=20, seed=2, symbols=['VTI'])
    second = cache(req, snapshot_directory=tmp_path)
    assert second != first
    assert second == provide_historical_market_data(req, snapshot_directory=tmp_path)
    assert cache.misses == 2


def test_missing_manifest_does_not_reuse_prior_data(tmp_path):
    write_synthetic_snapshot(tmp_path, days=20, symbols=['VTI'])
    cache = VerifiedSnapshotCache(); req = MarketDataRequest(['VTI'])
    cache(req, snapshot_directory=tmp_path)
    (tmp_path / 'manifest.json').unlink()
    assert not cache(req, snapshot_directory=tmp_path).series
