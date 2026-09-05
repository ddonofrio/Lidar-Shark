from lidar_sdk.errors import DataTimeout, SubscriptionClosed

from lidar_shark.acquisition import AcquisitionController


class FakeSubscription:
    def __init__(self, values):
        self.values = iter(values)
        self.closed = False

    def get(self, timeout_s):
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        self.closed = True


class FakeSource:
    def __init__(self, subscription):
        self.subscription = subscription
        self.started = False
        self.stopped = False
        self.closed = False

    def subscribe_scans(self, max_queue):
        assert max_queue == 2
        return self.subscription

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def test_data_timeout_is_polling_and_end_of_stream_is_not_a_failure():
    subscription = FakeSubscription([DataTimeout("poll"), SubscriptionClosed("done")])
    source = FakeSource(subscription)
    controller = AcquisitionController(source)
    failures = []
    finished = []
    controller.failure.connect(failures.append)
    controller.finished.connect(lambda: finished.append(True))

    controller.start()
    controller._thread.join(timeout=1)

    assert controller._thread.is_alive() is False
    assert failures == []
    assert source.started is True


def test_stop_closes_subscription_and_source():
    subscription = FakeSubscription([DataTimeout("poll")])
    source = FakeSource(subscription)
    controller = AcquisitionController(source)

    controller.start()
    controller.stop()

    assert subscription.closed is True
    assert source.stopped is True
    assert source.closed is True
