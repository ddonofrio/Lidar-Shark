import sys
from pathlib import Path

from lidar_sdk.models import SampleStatus

sys.path.insert(0, str(Path(__file__).parents[1] / "fixture-provider"))

from fixture_provider import FixtureProvider


def test_independent_fixture_publishes_sdk_scan_without_hardware():
    provider = FixtureProvider()
    descriptor = provider.list_sources()[0]
    source = provider.create_source(descriptor.source_id, provider.validate_config(descriptor.source_id, {}))
    subscription = source.subscribe_scans(1)

    source.start()
    try:
        scan = subscription.get(1.0)
    finally:
        source.stop()

    assert scan.source.provider_id == "fixture"
    assert scan.sample_count == 8
    assert sum(status == SampleStatus.VALID for status in scan.sample_status) == 7
    assert scan.sample_status[2] == SampleStatus.NO_RETURN
