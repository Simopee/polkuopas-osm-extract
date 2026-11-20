# Licence and attribution

This repository holds the method Polkuopas (https://polkuopas.fi) uses to build
a Derivative Database from OpenStreetMap data for a map overlay showing public
toilets, parking areas and drinking-water points across Finland. It is
published to satisfy Section 4.6 of the Open Database Licence (ODbL) v1.0.

**Publication status.** This notice, the script and the README are published
at https://github.com/Simopee/polkuopas-osm-extract. The Derivative Database
described here enters public use on **2026-10-04**, the date the overlay that
serves it is switched on at polkuopas.fi. The method is described in two
parts, both of which form the published method: the extraction script
(`polkuopas-osm-poi-extract.sh`) and the selection rules in README.md
("Selection applied before use"). It is linked from
https://polkuopas.fi/tietoa.

**Source data:** (c) OpenStreetMap contributors, available under the ODbL:
https://opendatacommons.org/licenses/odbl/1.0/

**Source extract used:** Geofabrik's Finland OSM extract,
https://download.geofabrik.de/europe/finland.html

**What this satisfies:** ODbL Section 4.6(b) - publication of "the method of
making the alterations to the Database (such as an algorithm)" used to produce
the Derivative Database from OpenStreetMap's Contents. It covers the three OSM
feature types handled by the script (`amenity=toilets`, `amenity=parking`,
`amenity=drinking_water`). See also OSMF's Horizontal Map Layers guideline:
https://osmfoundation.org/wiki/Licence/Community_Guidelines/Horizontal_Map_Layers_-_Guideline

**Scope note:** the Finnish part above applies only to the three OSM-derived
feature types named above. A second, separate part (Norway core types, below)
covers four other OSM feature types in Norway. Neither part extends to any
other Polkuopas data. In
particular, the hiking-destination points of interest shown elsewhere on the
map are sourced from LIPAS (University of Jyvaskyla, CC BY 4.0) and
Metsahallitus, and remain outside OpenStreetMap and the ODbL. See
https://polkuopas.fi/tietoa for full data-source attribution.

**Attribution on the live map (Finnish utility overlay):** "Map data (c) OpenStreetMap contributors" is
shown in the map's attribution control (uncollapsed) at all times a utility
overlay is rendered.

## Norway core types (2026-11)

**What this covers.** A Derivative Database built from OpenStreetMap data in
Norway, limited to four outdoor place types: viewpoint (`tourism=viewpoint`),
swimming place (`leisure=bathing_place`, `leisure=swimming_area`), fire place
(`leisure=firepit`, `amenity=bbq`) and tent site (`tourism=camp_site`,
`tourism=camp_pitch`). The file is `polkuopas-osm-no-core.geojson` at the
repository root. The method is in `norway-core/` (README, `rules/`) with the
ODbL 1.0 text in `norway-core/LICENSE`. It satisfies ODbL Section 4.6 for this
database, as the Finnish part does for the Finnish one.

**Source data:** (c) OpenStreetMap contributors, available under the ODbL:
https://opendatacommons.org/licenses/odbl/1.0/

**Source extract used:** the Norway extract of download.openstreetmap.fr,
https://download.openstreetmap.fr/extracts/europe/norway.osm.pbf, replication
timestamp in the file header `2026-11-19T01:57:18Z`, downloaded 2026-11-19. The
file and its checksums are recorded in `norway-core/README.md`. Geofabrik was
not reachable from the build environment on that date.

**Publication status.** The file, the method and the licence text are published
in this repository on the date of the commit that adds them (2026-11-20). The
Derivative Database enters public use when the viewpoint layer is switched on at
polkuopas.fi. Swimming place, fire place and tent site rows are published here
but are not shown on the map until later; the file holds all four types. Each
refresh of the file updates `norway-core/README.md` in the same commit.

**Attribution on the live map:** "© OpenStreetMap contributors", linked to
https://www.openstreetmap.org/copyright, is shown in the map's credit whenever
these rows are in view. The map sheet for a place shows "Lähde: ©
OpenStreetMap contributors, ODbL", with the licence linked, and a notice that
Polkuopas has changed the data (tags limited, ways and areas turned into centre
points, rows filtered and reclassified).

---

**Note on tag scope.** An earlier draft of the script filtered
`amenity=toilets` and `amenity=drinking_water` to nodes only
(`n/amenity=toilets`, `n/amenity=drinking_water`) while using `nwr` (node, way
and relation) for `amenity=parking`. That was narrower than needed, because
toilets and drinking-water points mapped as ways or relations are rare but
real. The published script uses `nwr` for all three tags. The same three
feature types are in scope either way.
