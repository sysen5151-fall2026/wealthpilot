"""Opt-in Chapter 10 alternative: verified, single-entry snapshot cache.

The default Planner remains uncached. Each request fingerprints the manifest and
CSV bytes before reuse. Changes to data, request symbols, directory or admission
threshold invalidate the entry. Cached results are copied so callers cannot
mutate later responses. This is a sequential experiment, not a concurrent cache.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns

from . import DEFAULT_SNAPSHOT_DIRECTORY, provide_historical_market_data


class VerifiedSnapshotCache:
    def __init__(self, observer=None):
        self._key = None
        self._data = None
        self.observer = observer
        self.hits = self.misses = 0

    def _stage(self, stage, operation):
        start = perf_counter_ns()
        try:
            return operation()
        finally:
            if self.observer:
                self.observer(stage, start, perf_counter_ns())

    @staticmethod
    def _fingerprint(directory, request, minimum):
        manifest_bytes = (directory / 'manifest.json').read_bytes()
        manifest = json.loads(manifest_bytes)
        contents = (directory / manifest['file']).read_bytes()
        digest = hashlib.sha256(contents).hexdigest()
        if digest != manifest['sha256']:
            raise ValueError('Snapshot fingerprint mismatch')
        return (str(directory.resolve()), tuple(request.symbols), minimum,
                hashlib.sha256(manifest_bytes).hexdigest(), digest)

    def invalidate(self):
        self._key = self._data = None

    def __call__(self, request, *, snapshot_directory=DEFAULT_SNAPSHOT_DIRECTORY,
                 minimum_observations=1):
        directory = Path(snapshot_directory)
        try:
            key = self._stage('SIM.C.12.1', lambda: self._fingerprint(
                directory, request, minimum_observations))
        except (OSError, ValueError, KeyError, TypeError):
            self._stage('SIM.C.12.2', self.invalidate)
            self.misses += 1
            # Preserve the current provider's fail-closed limitation semantics.
            return self._stage('SIM.C.12.3', lambda: provide_historical_market_data(
                request, snapshot_directory=directory,
                minimum_observations=minimum_observations))
        if self._key != key:
            self.misses += 1
            self._stage('SIM.C.12.2', self.invalidate)
            data = self._stage('SIM.C.12.3', lambda: provide_historical_market_data(
                request, snapshot_directory=directory,
                minimum_observations=minimum_observations))
            # Do not publish data if files changed during validation.
            def publish():
                if key != self._fingerprint(directory, request, minimum_observations):
                    raise RuntimeError('Snapshot changed during cache preparation; retry')
                self._key, self._data = key, data
            self._stage('SIM.C.12.4', publish)
        else:
            def hit():
                self.hits += 1
            self._stage('SIM.C.12.6', hit)
        return self._stage('SIM.C.12.5', lambda: deepcopy(self._data))
