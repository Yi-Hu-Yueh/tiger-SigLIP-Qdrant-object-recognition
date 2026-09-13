from pathlib import Path

from app.services.indexing import deterministic_point_id, resolve_object_id


def test_nested_directory_groups_references(tmp_path: Path):
    raw = tmp_path / "rawpics"
    path = raw / "object-A" / "side" / "01.jpg"
    path.parent.mkdir(parents=True)
    path.touch()
    object_id, object_name = resolve_object_id(path, raw)
    assert object_id == "object-A"
    assert object_name == "object-A"


def test_flat_double_underscore_groups_references(tmp_path: Path):
    raw = tmp_path / "rawpics"
    raw.mkdir()
    path = raw / "object-B__03.jpg"
    path.touch()
    object_id, _ = resolve_object_id(path, raw)
    assert object_id == "object-B"


def test_flat_file_is_own_object(tmp_path: Path):
    raw = tmp_path / "rawpics"
    raw.mkdir()
    path = raw / "zebra_01.jpg"
    path.touch()
    object_id, _ = resolve_object_id(path, raw)
    assert object_id == "zebra_01"


def test_point_id_is_stable():
    assert deterministic_point_id("a/01.jpg") == deterministic_point_id("a/01.jpg")
    assert deterministic_point_id("a/01.jpg") != deterministic_point_id("a/02.jpg")
