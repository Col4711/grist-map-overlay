# Grist Map Widget mit Overlay-Layer

Erweiterte Version des offiziellen [Grist Map Widgets](https://github.com/gristlabs/grist-widget/tree/master/map)
um einen zusätzlichen, konfigurierbaren GeoJSON-Overlay-Layer (z. B. für markierte Grundstücks-/Gebäudebereiche).

Basis: `gristlabs/grist-widget`, Ordner `map/` (Leaflet-basiert).

## Features gegenüber dem Original

- **Zusätzlicher GeoJSON-Layer** über die normalen Grist-Tabellendaten hinaus, geladen von einer
  frei konfigurierbaren URL.
- **Mehrere Zeichnungen in einer Datei** – beliebig viele Polygone/Linien/Punkte in einer
  `FeatureCollection` werden automatisch alle gezeichnet.
- **Dauerhaft sichtbare Beschriftung** (Leaflet-Tooltip mit `permanent: true`) statt Popup –
  kein Klick nötig.
- **Zoom-abhängige Sichtbarkeit der Labels**, um die Karte im herausgezoomten Zustand nicht
  zuzukleistern.
- **Farbzuordnung pro Fläche**, entweder direkt aus der GeoJSON-Datei oder über eine
  Namens-Zuordnung im Code (praktisch, wenn die Exportquelle – z. B. BayernAtlas – keine
  Farb-Property mitliefert).
- **Overlay-URL über die Widget-Einstellungen konfigurierbar** (kein Code-Update nötig).

## Dateistruktur

```
map/
├── index.html               Haupt-HTML, bindet Leaflet + page.js ein
├── page.js                  Widget-Logik (Karte, Marker, Overlay)
├── screen.css                Styling (inkl. Overlay-Label-Optik)
├── overlay.geojson           Beispiel-/Default-Overlay (wird verwendet, wenn keine
│                             Overlay-URL in den Widget-Einstellungen gesetzt ist)
├── marker-icon*.png          Standard-Leaflet-Marker-Icons
├── marker-shadow.png
└── package.json
```

## Hosting

Das Widget muss komplett (alle Dateien) über HTTPS erreichbar sein, z. B. via **GitHub Pages**.

### Wichtig: `raw.githubusercontent.com` funktioniert NICHT für `index.html`

`raw.githubusercontent.com` setzt `X-Frame-Options: deny` und lässt sich daher nicht im
`<iframe>` einbetten, in dem Grist Custom Widgets anzeigt. Für die Widget-URL selbst
**immer GitHub Pages verwenden**:

1. Im Repo unter **Settings → Pages** die Quelle auf den gewünschten Branch/Ordner setzen.
2. Nach ein bis zwei Minuten ist das Widget erreichbar unter:
   ```
   https://<user>.github.io/<repo>/index.html
   ```
3. Diese URL als Custom-Widget-URL in Grist eintragen.

`raw.githubusercontent.com` (oder ebenfalls GitHub Pages) darf hingegen problemlos für die
**Overlay-GeoJSON-Datei** verwendet werden, da diese nur per `fetch()` aus dem Code geladen
wird (kein Framing, nur ein normaler HTTP-Request mit CORS).

## Konfiguration in Grist

Beim Hinzufügen als Custom Widget:

1. **Spalten zuordnen**: `Name`, `Longitude`, `Latitude` (Pflicht), optional `Geocode`,
   `Address`, `GeocodedAddress` für automatische Geocodierung.
2. Über das **Zahnrad-Icon** (Widget-Einstellungen) öffnen sich zusätzliche Optionen:
   - **All locations / Single location** – ob alle Zeilen oder nur die ausgewählte gezeigt wird.
   - **Source / Copyright** – Kartenkachel-Quelle und Copyright-Hinweis.
   - **Overlay-URL** – URL zur GeoJSON-Datei mit der zusätzlichen Zeichnung. Leer lassen,
     um die mitgelieferte lokale `overlay.geojson` zu verwenden.

## Overlay-GeoJSON-Format

Standard-`FeatureCollection` mit beliebig vielen Features:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [[[lng, lat], ...]] },
      "properties": { "name": "Bereich A", "color": "#2a9d8f" }
    },
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [lng, lat] },
      "properties": { "name": "Bereich A" }
    }
  ]
}
```

- **Label-Text**: `properties.name`, ersatzweise `properties.description`. Ist beides leer/nicht
  vorhanden, wird kein Label angezeigt (nur die Fläche/der Punkt selbst).
- **Farbe pro Feature**: optionale `properties.color` (z. B. `"#2a9d8f"`). Fehlt sie, greift die
  Namens-Zuordnung `OVERLAY_COLORS_BY_NAME` in `page.js` (siehe unten), sonst Standard-Rot.
- Exportquellen wie der **BayernAtlas** liefern i. d. R. kein `color`-Feld – dafür ist die
  Namens-Zuordnung im Code gedacht.
- Dritte Koordinate (Höhe, z. B. `[lng, lat, 0]`) wird ignoriert, stört nicht.

### Zeichnung aktualisieren

Einfach die Datei, auf die die Overlay-URL zeigt, ersetzen (neuer Export aus dem BayernAtlas
o. ä. hochladen/committen). Kein Codeänderung nötig.

## Anpassbare Konstanten in `page.js`

| Konstante | Zeile (ca.) | Bedeutung |
|---|---|---|
| `OVERLAY_COLORS_BY_NAME` | ~47 | Namens-Zuordnung Bereich → Farbe, falls GeoJSON keine `color`-Property liefert |
| `DEFAULT_OVERLAY_COLOR` | ~51 | Fallback-Farbe, falls weder Property noch Namens-Zuordnung greift |
| `OVERLAY_LABEL_MIN_ZOOM` | ~63 | Zoomstufe, ab der Labels sichtbar werden (Leaflet: 0 = Weltkarte, ca. 18–19 = Straßenebene) |

## Bekannte Einschränkungen

- **Label-Position bei stark verwinkelten Flächen**: Labels werden am Mittelpunkt der
  Bounding-Box der Fläche platziert. Bei sehr konkaven/L-förmigen Polygonen kann das optisch
  noch leicht daneben liegen. Für eine exakte Lösung wäre ein "Pole of Inaccessibility"-Algorithmus
  (z. B. via der `polylabel`-Bibliothek) nötig – aktuell nicht eingebaut.
- Das Overlay ist **rein visuell** (keine Verknüpfung zu Grist-Tabellenzeilen, keine Klick-Interaktion
  wie bei den normalen Standort-Markern).
- Bei vielen dicht beieinanderliegenden Flächen mit Labels kann die Karte trotz Zoom-Schwelle
  unübersichtlich werden.

## Credits

Basiert auf dem offiziellen [Grist Map Widget](https://github.com/gristlabs/grist-widget)
von Grist Labs (Apache-2.0-Lizenz).
