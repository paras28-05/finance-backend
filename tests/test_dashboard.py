"""
Tests for dashboard / analytics endpoints:
  GET /dashboard/summary
  GET /dashboard/categories
  GET /dashboard/trends
  GET /dashboard/recent
"""


def test_summary_returns_correct_shape(client, auth_headers, sample_records):
    r = client.get("/dashboard/summary", headers=auth_headers["viewer"])
    assert r.status_code == 200
    body = r.json()
    for field in ("total_income", "total_expense", "net_balance", "total_records",
                  "income_records", "expense_records"):
        assert field in body


def test_summary_net_balance_is_correct(client, auth_headers, sample_records):
    r = client.get("/dashboard/summary", headers=auth_headers["viewer"])
    body = r.json()
    expected_net = round(body["total_income"] - body["total_expense"], 2)
    assert body["net_balance"] == expected_net


def test_all_roles_can_access_summary(client, auth_headers, sample_records):
    for role, headers in auth_headers.items():
        r = client.get("/dashboard/summary", headers=headers)
        assert r.status_code == 200, f"Role {role} blocked from summary"


def test_category_totals_returns_list(client, auth_headers, sample_records):
    r = client.get("/dashboard/categories", headers=auth_headers["analyst"])
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    if body:
        assert "category" in body[0]
        assert "total" in body[0]
        assert "count" in body[0]


def test_category_filter_by_type(client, auth_headers, sample_records):
    r = client.get("/dashboard/categories?type=expense", headers=auth_headers["analyst"])
    assert r.status_code == 200
    for item in r.json():
        assert item["type"] == "expense"


def test_monthly_trends_returns_list(client, auth_headers, sample_records):
    r = client.get("/dashboard/trends?granularity=monthly", headers=auth_headers["viewer"])
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    if body:
        entry = body[0]
        assert "period" in entry
        assert "income" in entry
        assert "expense" in entry
        assert "net" in entry
        # Monthly period format: YYYY-MM
        assert len(entry["period"]) == 7
        assert entry["period"][4] == "-"


def test_weekly_trends_returns_list(client, auth_headers, sample_records):
    r = client.get("/dashboard/trends?granularity=weekly", headers=auth_headers["viewer"])
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    if body:
        entry = body[0]
        assert "period" in entry
        # Weekly period format: YYYY-Www
        assert "W" in entry["period"]


def test_trends_filter_by_year(client, auth_headers, sample_records):
    r = client.get("/dashboard/trends?granularity=monthly&year=2024",
                   headers=auth_headers["viewer"])
    assert r.status_code == 200
    for entry in r.json():
        assert entry["period"].startswith("2024")


def test_recent_activity_default_limit(client, auth_headers, sample_records):
    r = client.get("/dashboard/recent", headers=auth_headers["viewer"])
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) <= 10


def test_recent_activity_custom_limit(client, auth_headers, sample_records):
    r = client.get("/dashboard/recent?limit=3", headers=auth_headers["viewer"])
    assert r.status_code == 200
    assert len(r.json()) <= 3


def test_recent_activity_max_limit_enforced(client, auth_headers):
    r = client.get("/dashboard/recent?limit=999", headers=auth_headers["viewer"])
    assert r.status_code == 422  # page_size > 50 is rejected


def test_unauthenticated_dashboard_access_returns_401(client):
    r = client.get("/dashboard/summary")
    assert r.status_code == 401
