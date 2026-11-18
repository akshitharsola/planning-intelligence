from scripts.ingest_decision_documents import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.authority == "Galway County Council"
    assert args.since_year == 2023
    assert args.from_date is None
    assert args.limit is None
    assert args.sample is None
    assert args.seed == 42
    assert args.refs is None
    assert args.dry_run is False


def test_parse_args_custom():
    args = parse_args([
        "--authority", "Galway County Council",
        "--from-date", "2023-06-01",
        "--sample", "100",
        "--seed", "123",
        "--refs", "2360654,2260277",
        "--dry-run",
    ])
    assert args.authority == "Galway County Council"
    assert args.from_date == "2023-06-01"
    assert args.sample == 100
    assert args.seed == 123
    assert args.refs == "2360654,2260277"
    assert args.dry_run is True



def test_parse_args_skip_known_default_on_and_refresh_turns_it_off():
    assert parse_args([]).refresh is False
    assert parse_args(["--refresh"]).refresh is True


def test_parse_args_until_year():
    assert parse_args([]).until_year is None
    args = parse_args(["--since-year", "2026", "--until-year", "2026"])
    assert args.since_year == 2026
    assert args.until_year == 2026
