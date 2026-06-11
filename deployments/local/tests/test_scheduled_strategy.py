"""
Unit tests for ScheduledStrategy interval gating and the calculate/commit split.

These verify the fix for the "mark run before execute" bug: calculating the
investable amount must NOT consume the interval; only commit_run() (called
after a real execution) may. Pure unit tests - no network, no credentials.
"""

from strategies.scheduled import ScheduledStrategy


def _config():
    """Return a minimal valid daily scheduled-strategy config dict."""
    return {
        "name": "daily_test",
        "type": "scheduled",
        "amount": 5.00,
        "interval": "daily",
        "allocation": {"VOO": 1.0},
    }


def test_first_run_returns_amount(tmp_path):
    """
    Verify the first calculation returns the configured amount (interval gate
    is open because the strategy has never run).

    @PARAMS:
        - tmp_path -> pytest fixture; temp dir holding the JSON state file
    """
    strategy = ScheduledStrategy(state_file=str(tmp_path / "state.json"))
    amount, details = strategy.calculate_investable_amount(_config())
    assert amount == 5.00
    assert details and details[0]["strategy"] == "daily_test"


def test_calculation_does_not_consume_interval(tmp_path):
    """
    Verify calling calculate twice without committing still returns the amount
    both times - i.e. simulating/recomputing does not mark the run.

    @PARAMS:
        - tmp_path -> pytest fixture; temp dir holding the JSON state file
    """
    strategy = ScheduledStrategy(state_file=str(tmp_path / "state.json"))
    first, _ = strategy.calculate_investable_amount(_config())
    second, _ = strategy.calculate_investable_amount(_config())
    assert first == 5.00
    assert second == 5.00


def test_commit_run_consumes_interval(tmp_path):
    """
    Verify that after commit_run() the next calculation returns 0.0, because the
    daily interval has not yet elapsed since the recorded run.

    @PARAMS:
        - tmp_path -> pytest fixture; temp dir holding the JSON state file
    """
    config = _config()
    strategy = ScheduledStrategy(state_file=str(tmp_path / "state.json"))

    amount, _ = strategy.calculate_investable_amount(config)
    assert amount == 5.00

    strategy.commit_run(config)

    amount_after, _ = strategy.calculate_investable_amount(config)
    assert amount_after == 0.0


def test_commit_run_persists_across_instances(tmp_path):
    """
    Verify the committed run is written to durable state: a fresh strategy
    instance reading the same state file also sees the interval as consumed.

    @PARAMS:
        - tmp_path -> pytest fixture; temp dir holding the JSON state file
    """
    state_file = str(tmp_path / "state.json")
    config = _config()

    first = ScheduledStrategy(state_file=state_file)
    first.calculate_investable_amount(config)
    first.commit_run(config)

    second = ScheduledStrategy(state_file=state_file)
    amount, _ = second.calculate_investable_amount(config)
    assert amount == 0.0
