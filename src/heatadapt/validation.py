"""Command-line validation for source catalogues and GeoJSON boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from heatadapt.catalogue import load_catalogue
from heatadapt.geojson import validate_boundary_geojson


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="heatadapt-validate",
        description="Validate Urban Heat Intelligence project input files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    catalogue_parser = subparsers.add_parser(
        "catalogue", help="Validate the JSON dataset catalogue"
    )
    catalogue_parser.add_argument("path", help="Path to catalogue.json")
    boundary_parser = subparsers.add_parser("boundary", help="Validate a GeoJSON boundary file")
    boundary_parser.add_argument("path", help="Path to a GeoJSON FeatureCollection")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a validation command and return a process exit code."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "catalogue":
            records = load_catalogue(args.path)
            result = {"valid": True, "dataset_count": len(records)}
        else:
            summary = validate_boundary_geojson(args.path)
            result = {
                "valid": True,
                "feature_count": summary.feature_count,
                "geometry_types": list(summary.geometry_types),
                "bounds_wgs84": summary.bounds,
            }
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
