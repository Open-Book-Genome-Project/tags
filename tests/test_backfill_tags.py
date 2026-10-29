import pytest

from scripts.backfill_tags import work_field_for_tag_type


@pytest.mark.parametrize(
    ("tag_type", "work_field"),
    [
        ("genres", "genres"),
        ("subgenres", "subgenres"),
        ("audience", "audiences"),
    ],
)
def test_work_field_for_tag_type(tag_type, work_field):
    assert work_field_for_tag_type(tag_type) == work_field
