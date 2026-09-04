#!/usr/bin/env python3
"""
Konvertiert einen BayernAtlas-KML-Export ("Zeichnung") in eine overlay.geojson
fuer das Grist Map Widget - inklusive Farbe je Objekt.

Jedes Placemark wird 1:1 in ein GeoJSON-Feature uebersetzt, mit seinen EIGENEN
Koordinaten, seinem EIGENEN Namen (falls vergeben) und seiner EIGENEN Farbe.
Es findet KEINE Zuordnung/Verknuepfung zwischen unterschiedlichen Placemarks statt
(z.B. Flaeche <-> separater Text-Punkt) - das sind bewusst unabhaengige Objekte.

Text-Placemarks (im BayernAtlas per "unsichtbarem Icon", <IconStyle><scale>0</scale>
erkennbar) werden als Punkt-Feature mit "labelOnly": true markiert. Das Widget zeigt
fuer solche Punkte NUR die Beschriftung an ihrer exakten Position, ohne farbigen
Marker-Punkt - da die Position ja bereits manuell/bewusst gewaehlt wurde.

Verwendung:
    python3 kml_to_overlay.py eingabe.kml ausgabe.geojson

GPX wird bewusst nicht unterstuetzt: GPX kennt keine Flaechen/Polygone und
transportiert keine Farbinformationen - fuer dieses Widget ungeeignet.
"""
import sys
import json
import xml.etree.ElementTree as ET

NS = {'kml': 'http://www.opengis.net/kml/2.2'}


def kml_color_to_hex(kml_color):
    """KML-Farbformat ist aabbggrr (Alpha, Blau, Gruen, Rot) - zu CSS #rrggbb konvertieren."""
    if not kml_color or len(kml_color) != 8:
        return None
    rr = kml_color[6:8]
    gg = kml_color[4:6]
    bb = kml_color[2:4]
    return f"#{rr}{gg}{bb}"


def parse_coords(coord_text):
    """'lng,lat,alt lng,lat,alt ...' -> [[lng, lat], ...] (Hoehe wird verworfen)."""
    points = []
    for token in coord_text.split():
        parts = token.split(',')
        points.append([float(parts[0]), float(parts[1])])
    return points


def convert(input_path, output_path):
    tree = ET.parse(input_path)
    root = tree.getroot()

    features = []
    for pm in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        name_el = pm.find('kml:name', NS)
        name = name_el.text.strip() if name_el is not None and name_el.text else None
        desc_el = pm.find('kml:description', NS)
        description = desc_el.text.strip() if desc_el is not None and desc_el.text else None

        line_color_el = pm.find('.//kml:LineStyle/kml:color', NS)
        label_color_el = pm.find('.//kml:LabelStyle/kml:color', NS)
        icon_scale_el = pm.find('.//kml:IconStyle/kml:scale', NS)
        icon_scale = icon_scale_el.text if icon_scale_el is not None else None

        # Farbe bevorzugt von der eigentlichen Zeichenfarbe (Linie/Flaeche), sonst
        # von der Label-/Textfarbe uebernehmen.
        color = kml_color_to_hex(line_color_el.text if line_color_el is not None else
                                  (label_color_el.text if label_color_el is not None else None))

        props = {}
        if name:
            props['name'] = name
        if description:
            props['description'] = description
        if color:
            props['color'] = color

        polygon_el = pm.find('kml:Polygon', NS)
        point_el = pm.find('kml:Point', NS)
        linestring_el = pm.find('kml:LineString', NS)

        if polygon_el is not None:
            coords_el = polygon_el.find('.//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', NS)
            ring = parse_coords(coords_el.text)
            geometry = {'type': 'Polygon', 'coordinates': [ring]}
        elif linestring_el is not None:
            coords_el = linestring_el.find('kml:coordinates', NS)
            line = parse_coords(coords_el.text)
            geometry = {'type': 'LineString', 'coordinates': line}
        elif point_el is not None:
            coords_el = point_el.find('kml:coordinates', NS)
            lng, lat = parse_coords(coords_el.text)[0]
            geometry = {'type': 'Point', 'coordinates': [lng, lat]}
            # "Text-Placemark" (unsichtbares Icon, scale=0) -> nur Beschriftung anzeigen,
            # keinen farbigen Marker-Punkt. Position wurde bereits bewusst gewaehlt.
            if icon_scale == '0':
                props['labelOnly'] = True
        else:
            continue  # unbekannte/leere Geometrie ueberspringen

        features.append({'type': 'Feature', 'properties': props, 'geometry': geometry})

    geojson = {'type': 'FeatureCollection', 'features': features}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"{len(features)} Feature(s) geschrieben nach {output_path}")
    for feat in features:
        p = feat['properties']
        print(f"  {feat['geometry']['type']:10s} name={p.get('name')!r} "
              f"color={p.get('color')!r} labelOnly={p.get('labelOnly', False)}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Verwendung: python3 kml_to_overlay.py eingabe.kml ausgabe.geojson")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
