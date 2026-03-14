from aw_server.checkins import build_checkins_payload
from aw_server.server import AWFlask


def test_build_checkins_payload_groups_sessions_and_ignores_repeated_questions(
    tmp_path, monkeypatch
):
    data_dir = tmp_path / "checkins"
    data_dir.mkdir()
    (data_dir / "2026-03-14").write_text(
        "\n".join(
            [
                "2026-03-14 09:00:00 CURRENT QUESTION: SLEEP",
                "2026-03-14 09:00:00 FEEDBACK LEVEL: 5",
                "2026-03-14 09:03:00 CURRENT QUESTION: 1",
                "2026-03-14 09:03:01 CURRENT QUESTION: 1",
                "2026-03-14 09:03:02 FEEDBACK LEVEL: 2",
                "2026-03-14 09:03:10 CURRENT QUESTION: 2",
                "2026-03-14 09:03:12 QUESTION SKIPPED",
                "2026-03-14 09:25:00 CURRENT QUESTION: 1",
                "2026-03-14 09:25:03 FEEDBACK LEVEL: 4",
                "",
            ]
        )
    )
    monkeypatch.setenv("TRUSTME_CHECKINS_DIR", str(data_dir))

    payload = build_checkins_payload()

    assert payload["available_dates"] == ["2026-03-14"]
    assert len(payload["sessions"]) == 2

    latest_session, first_session = payload["sessions"]
    assert latest_session["id"] == "2026-03-14-02"
    assert latest_session["answers"][0]["label"] == "Focus"
    assert latest_session["answers"][0]["value_label"] == "4/5"

    assert first_session["id"] == "2026-03-14-01"
    assert [answer["question_id"] for answer in first_session["answers"]] == [
        "SLEEP",
        "1",
        "2",
    ]
    assert first_session["answers"][1]["value_label"] == "2/5"
    assert first_session["answers"][2]["value_label"] == "Skipped"


def test_checkins_route_returns_backend_payload(monkeypatch):
    app = AWFlask("127.0.0.1", testing=True)
    flask_client = app.test_client()
    expected = {"available_dates": ["2026-03-14"], "sessions": [{"id": "session-1"}]}

    def fake_get_checkins(*, date_filter=None):
        assert date_filter == "2026-03-14"
        return expected

    app.api.get_checkins = fake_get_checkins

    response = flask_client.get("/api/0/dashboard/checkins?date=2026-03-14")
    assert response.status_code == 200
    assert response.json == expected
