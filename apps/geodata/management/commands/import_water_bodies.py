import json

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand, CommandError

from apps.geodata.models import WaterBody


class Command(BaseCommand):
    help = "Import water body features from a GeoJSON file into the WaterBody model."

    def add_arguments(self, parser):
        parser.add_argument(
            "geojson_path",
            type=str,
            help="Path to the GeoJSON file, e.g. data/raw/assam_water_bodies.geojson",
        )
        parser.add_argument(
            "--source",
            type=str,
            default="OpenStreetMap",
            help="Source label stored on each record.",
        )

    def handle(self, *args, **options):
        path = options["geojson_path"]
        source = options["source"]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid GeoJSON: {e}")

        features = data.get("features", [])
        if not features:
            raise CommandError("No features found in GeoJSON file.")

        created_count = 0
        skipped_count = 0

        for feature in features:
            geometry_data = feature.get("geometry")
            properties = feature.get("properties", {}) or {}

            if not geometry_data:
                skipped_count += 1
                continue

            try:
                geom = GEOSGeometry(json.dumps(geometry_data))
            except Exception:
                skipped_count += 1
                continue

            if isinstance(geom, Polygon):
                geom = MultiPolygon(geom)
            elif not isinstance(geom, MultiPolygon):
                skipped_count += 1
                continue

            geom.srid = 4326

            name = (
                properties.get("name")
                or properties.get("natural")
                or "Unnamed water body"
            )

            WaterBody.objects.create(
                name=name,
                water_type="lake" if "lake" in name.lower() else "river",
                geometry=geom,
                source=source,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created_count} water bodies, skipped {skipped_count}."
            )
        )