from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from world_synthesis.schema import WorldSpec, load_world_spec

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "world_synthesis" / "glasswind_region.yaml"


def test_sample_world_spec_is_typed_and_reviewed() -> None:
    world = load_world_spec(SPEC)
    assert world.metadata.authoring_status == "reviewed"
    assert world.region.id == "glasswind_marches"
    assert {item.id for item in world.region.maps} == {
        "fernwake_threshold",
        "brasshaven_threshold",
        "glasswind_causeway",
    }


def test_missing_warp_reference_is_rejected() -> None:
    raw = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    raw["region"]["maps"][0]["warps"][0]["target_map"] = "missing_map"
    with pytest.raises(ValidationError, match="missing warp targets"):
        WorldSpec.model_validate(raw)


def test_out_of_bounds_authored_coordinate_is_rejected() -> None:
    raw = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    raw["region"]["maps"][2]["player_spawn"] = {"x": 900, "y": 2}
    with pytest.raises(ValidationError, match="outside its bounds"):
        WorldSpec.model_validate(raw)
