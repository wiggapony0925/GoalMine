import pytest
from unittest.mock import MagicMock, patch
from services.data_scout import DataScoutService


@pytest.mark.asyncio
async def test_data_scout_sync_success():
    # Mock API and DB
    mock_api = MagicMock()
    mock_api.fetch_matches.return_value = [
        {
            "utcDate": "2026-06-11T15:00:00Z",
            "status": "TIMED",
            "homeTeam": {"name": "Mexico"},
            "awayTeam": {"name": "South Africa"},
            "score": {"fullTime": {"home": None, "away": None}},
        }
    ]

    mock_db = MagicMock()
    mock_db.load_live_schedule.return_value = None

    # Initialize Service
    service = DataScoutService(db_client=mock_db)
    service.api = mock_api

    # Run Sync
    with patch(
        "services.data_scout.STATIC_SCHEDULE",
        [
            {
                "match_label": "Mexico vs South Africa",
                "team_home": "Mexico",
                "team_away": "TBD",
                "date_iso": "2026-06-11T15:00:00",
                "venue": "Estadio Azteca, Mexico City",
                "stage": "Group Stage",
                "group": "Group A",
            }
        ],
    ):
        result = await service.sync_now()

        # Assertions
        assert result is not None
        assert len(result) == 1
        assert result[0]["team_away"] == "South Africa"  # TBD replaced by South Africa
        assert result[0]["live_status"] == "TIMED"

        # Verify DB save was called
        mock_db.save_live_schedule.assert_called_once_with(result)


@pytest.mark.asyncio
async def test_data_scout_no_matches_from_api():
    mock_api = MagicMock()
    mock_api.fetch_matches.return_value = None

    service = DataScoutService()
    service.api = mock_api

    result = await service.sync_now()
    assert result is None


def test_data_scout_initial_load_from_db():
    mock_db = MagicMock()
    mock_db.load_live_schedule.return_value = [{"match": "test"}]

    service = DataScoutService(db_client=mock_db)
    assert service.cached_merged_schedule == [{"match": "test"}]
