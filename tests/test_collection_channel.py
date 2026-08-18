from sqlalchemy import inspect

from app.models.collection_channel import CollectionChannel


def test_collection_channel_has_expected_columns():
    mapper = inspect(CollectionChannel)

    columns = {
        column.key
        for column in mapper.columns
    }

    assert columns == {
        "id",
        "guild_id",
        "channel_id",
        "channel_name",
        "enabled",
    }


def test_collection_channel_has_composite_unique_constraint():
    table = CollectionChannel.__table__

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ]

    assert any(
        {
            column.name
            for column in constraint.columns
        }
        == {
            "guild_id",
            "channel_id",
        }
        for constraint in unique_constraints
    )


def test_collection_channel_enabled_defaults_to_true():
    column = CollectionChannel.__table__.c.enabled

    assert column.default is not None
    assert column.default.arg is True