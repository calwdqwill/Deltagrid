"""Regression tests for SymbolMapper default alias seeding."""

from sqlalchemy import func

from app.adapters.data.symbol_mapper import DEFAULT_PERP_INSTRUMENTS, SymbolMapper
from app.domain.models import Instrument, InstrumentAlias


def test_seed_defaults_is_idempotent_and_adds_expansion_aliases() -> None:
    mapper = SymbolMapper(db_url="sqlite:///:memory:")

    mapper.seed_defaults()
    mapper.seed_defaults()

    assert mapper.to_provider("HYPE", "okx") == "HYPE-USDT-SWAP"
    assert mapper.to_provider("XRP", "okx") == "XRP-USDT-SWAP"
    assert mapper.to_provider("DOGE", "coinglass") == "DOGE"
    assert mapper.to_provider("ADA", "coingecko", alias_type="cg_id") == "cardano"
    assert mapper.to_provider("LINK", "coingecko", alias_type="cg_id") == "chainlink"
    assert mapper.from_provider("LINK-USDT-SWAP", "okx") == "LINK"

    session = mapper.Session()
    try:
        instrument_count = session.query(func.count()).select_from(Instrument).scalar()
        alias_count = session.query(func.count()).select_from(InstrumentAlias).scalar()
    finally:
        session.close()

    expected_alias_count = sum(len(item["aliases"]) for item in DEFAULT_PERP_INSTRUMENTS)
    assert instrument_count == len(DEFAULT_PERP_INSTRUMENTS)
    assert alias_count == expected_alias_count
