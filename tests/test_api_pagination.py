"""Tests for pagination of telemetry API responses."""

from api_server import _paginate_telemetry


def test_pagination_returns_requested_page_and_total_count():
    response = {
        "status": "success",
        "count": 5,
        "packets": [{"node_id": f"node-{i}"} for i in range(5)],
    }

    result = _paginate_telemetry(response, limit=2, offset=1)

    assert result["status"] == "success"
    assert result["packets"] == [{"node_id": "node-1"}, {"node_id": "node-2"}]
    assert result["count"] == 2
    assert result["total_count"] == 5
    assert result["limit"] == 2
    assert result["offset"] == 1


def test_pagination_offset_past_end_returns_empty_page():
    response = {"status": "success", "count": 1, "packets": [{"node_id": "node-1"}]}

    result = _paginate_telemetry(response, limit=10, offset=5)

    assert result["packets"] == []
    assert result["count"] == 0
    assert result["total_count"] == 1


def test_pagination_without_limit_returns_from_offset():
    response = {
        "status": "success",
        "count": 3,
        "packets": [{"node_id": f"node-{i}"} for i in range(3)],
    }

    result = _paginate_telemetry(response, limit=None, offset=1)

    assert result["packets"] == [{"node_id": "node-1"}, {"node_id": "node-2"}]
    assert result["count"] == 2
    assert result["total_count"] == 3
