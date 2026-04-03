#!/usr/bin/env python3
"""
Génère 3 SVGs annotés à partir de table.svg pour les 3 scénarios de pathfinding.
"""

import json
import logging
import os
import sys

# Suppress verbose logs
logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, '/')
os.environ['PYTHONPATH'] = '/home/gag/Bureau/EsialRobotik/Ia-Python'

from shapely.geometry import Point, Polygon
from ia.pathfinding.astar import AStar
from ia.pathfinding.visibility_graph import VisibilityGraph
from ia.utils.position import Position

# ─── Config ───────────────────────────────────────────────────────────────────
CONFIG_PATH = '/config/2025/princess/config.json'
TABLE_SVG_PATH = '/simulator/2025/table.svg'
OUTPUT_DIR = '/utils/'

ACTIVE_COLOR = 'color0'
DISABLED_ZONES = ['gradin_o', 'gradin_e']

START = Position(200, 200)
GOAL = Position(1400, 2300)

SCENARIOS = [
    {
        'file': 'table_scenario_sans_adversaire.svg',
        'adversaries': [],
        'label': 'Sans adversaire',
    },
    {
        'file': 'table_scenario_adversaire_leger.svg',
        'adversaries': [{'x': 1800, 'y': 1500}],
        'label': 'Adversaire léger',
    },
    {
        'file': 'table_scenario_adversaires_lourds.svg',
        'adversaries': [{'x': 1000, 'y': 1200}, {'x': 800, 'y': 1800}],
        'label': 'Adversaires lourds',
    },
]

# ─── Load config ──────────────────────────────────────────────────────────────
with open(CONFIG_PATH) as f:
    full_config = json.load(f)
table_config = full_config['table']
marge = table_config['marge']

ADVERSARY_RADIUS = AStar.ADVERSARY_RADIUS  # 200

# ─── Helpers ──────────────────────────────────────────────────────────────────

def poly_to_svg_points(shapely_poly):
    """Shapely coords (table_x, table_y) → SVG points (svg_x=table_y, svg_y=table_x)."""
    coords = list(shapely_poly.exterior.coords[:-1])
    return ' '.join(f'{ty:.1f},{tx:.1f}' for tx, ty in coords)


def path_to_svg_polyline(positions, color, width=12):
    if not positions:
        return ''
    pts = ' '.join(f'{p.y},{p.x}' for p in positions)
    dots = ''.join(
        f'<circle cx="{p.y}" cy="{p.x}" r="20" fill="{color}"/>'
        for p in positions
    )
    return (
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'{dots}'
    )


def make_polygon_from_zone(zone):
    if zone['forme'] == 'polygone':
        pts = [(p['x'], p['y']) for p in zone['points']]
        return Polygon(pts).buffer(marge, join_style=2)
    elif zone['forme'] == 'cercle':
        cx, cy = zone['centre']['x'], zone['centre']['y']
        return Point(cx, cy).buffer(zone['rayon'] + marge, resolution=16)
    return None


def build_overlay(table_cfg, active_color, disabled_zones, adversaries, astar_path, vg_path):
    """Builds the SVG overlay group string."""
    parts = ['<g id="overlay">']

    # 1. Forbidden zones
    forbidden_polys = []
    for zone in table_cfg['forbiddenZones']:
        # zones are active when type != active_color, or type == 'all'
        active_color_name = table_cfg.get(active_color, active_color)  # e.g. 'jaune'
        if zone['type'] == 'all' or zone['type'] != active_color_name:
            poly = make_polygon_from_zone(zone)
            if poly and not poly.is_empty:
                forbidden_polys.append((zone['id'], poly))

    for zid, poly in forbidden_polys:
        pts = poly_to_svg_points(poly)
        parts.append(
            f'<polygon points="{pts}" '
            f'fill="#cc0000" fill-opacity="0.35" '
            f'stroke="#880000" stroke-width="3"/>'
        )

    # 2. Dynamic zones - active (not in disabled list)
    for zone in table_cfg['dynamicZones']:
        if zone['id'] not in disabled_zones:
            poly = make_polygon_from_zone(zone)
            if poly and not poly.is_empty:
                pts = poly_to_svg_points(poly)
                parts.append(
                    f'<polygon points="{pts}" '
                    f'fill="#ffcc00" fill-opacity="0.35" '
                    f'stroke="#cc8800" stroke-width="3"/>'
                )

    # 3. Dynamic zones - inactive (disabled)
    for zone in table_cfg['dynamicZones']:
        if zone['id'] in disabled_zones:
            poly = make_polygon_from_zone(zone)
            if poly and not poly.is_empty:
                pts = poly_to_svg_points(poly)
                parts.append(
                    f'<polygon points="{pts}" '
                    f'fill="none" '
                    f'stroke="#aaaaaa" stroke-width="2" stroke-dasharray="12,6"/>'
                )

    # 4. Adversaries
    for adv in adversaries:
        adv_poly = Point(adv['x'], adv['y']).buffer(ADVERSARY_RADIUS + marge, resolution=2)
        pts = poly_to_svg_points(adv_poly)
        parts.append(
            f'<polygon points="{pts}" '
            f'fill="#ff6600" fill-opacity="0.4" '
            f'stroke="#cc4400" stroke-width="3"/>'
        )

    # 5. AStar path
    if astar_path:
        parts.append(path_to_svg_polyline(astar_path, '#2255ff', width=12))

    # 6. VG path
    if vg_path:
        parts.append(path_to_svg_polyline(vg_path, '#00aa44', width=12))

    # 7. Start and Goal markers
    # Start: circle r=30, white fill, black stroke
    sx, sy = START.y, START.x  # SVG coords
    parts.append(
        f'<circle cx="{sx}" cy="{sy}" r="30" '
        f'fill="#ffffff" stroke="#000000" stroke-width="3"/>'
    )
    # Goal: square 40×40 centered, white fill, black stroke
    gx, gy = GOAL.y, GOAL.x  # SVG coords
    parts.append(
        f'<rect x="{gx - 20}" y="{gy - 20}" width="40" height="40" '
        f'fill="#ffffff" stroke="#000000" stroke-width="3"/>'
    )

    # 8. Legend (top right, x=2400, y=20)
    legend_items = [
        ('#cc0000', 0.35, '#880000', 3, None, 'Zones interdites'),
        ('#ffcc00', 0.35, '#cc8800', 3, None, 'Zones dynamiques actives'),
        ('none', 1.0, '#aaaaaa', 2, '12,6', 'Zones dynamiques inactives'),
    ]
    if adversaries:
        legend_items.append(('#ff6600', 0.4, '#cc4400', 3, None, 'Adversaires'))
    if astar_path:
        legend_items.append(('#2255ff', 1.0, '#2255ff', 2, None, 'Chemin A*'))
    if vg_path:
        legend_items.append(('#00aa44', 1.0, '#00aa44', 2, None, 'Chemin VG'))
    legend_items.append(('#ffffff', 1.0, '#000000', 3, None, 'Départ (cercle) / Arrivée (carré)'))

    lx, ly = 2400, 20
    box_size = 30
    spacing = 45
    parts.append('<g id="legend">')
    parts.append(
        f'<rect x="{lx - 10}" y="{ly - 5}" width="570" height="{len(legend_items) * spacing + 10}" '
        f'fill="white" fill-opacity="0.8" rx="8"/>'
    )
    for i, (fill, opacity, stroke, sw, dasharray, label) in enumerate(legend_items):
        item_y = ly + i * spacing
        dash_attr = f'stroke-dasharray="{dasharray}"' if dasharray else ''
        parts.append(
            f'<rect x="{lx}" y="{item_y}" width="{box_size}" height="{box_size}" '
            f'fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}" {dash_attr}/>'
        )
        parts.append(
            f'<text x="{lx + box_size + 10}" y="{item_y + 22}" '
            f'font-size="28" fill="#000000" font-family="sans-serif">{label}</text>'
        )
    parts.append('</g>')

    parts.append('</g>')
    return '\n'.join(parts)


# ─── Read base SVG ────────────────────────────────────────────────────────────
with open(TABLE_SVG_PATH, 'r', encoding='utf-8') as f:
    base_svg = f.read()

# ─── Generate each scenario ───────────────────────────────────────────────────
for scenario in SCENARIOS:
    print(f"\n=== Scénario: {scenario['label']} ===")
    adversaries = scenario['adversaries']

    # Init pathfinding objects fresh for each scenario
    astar = AStar(table_config, ACTIVE_COLOR)
    vg = VisibilityGraph(table_config, ACTIVE_COLOR)

    # Disable zones
    for zone_id in DISABLED_ZONES:
        astar.update_dynamic_zone(zone_id, active=False)
        vg.update_dynamic_zone(zone_id, active=False)

    # Compute A* path
    astar.a_star(START, GOAL, adversaries=adversaries if adversaries else None)
    astar_path = astar.path
    print(f"  A* path: {len(astar_path)} waypoints")

    # Compute VG path
    vg.compute_path(START, GOAL, adversaries=adversaries if adversaries else None)
    vg_path = vg.path
    print(f"  VG path: {len(vg_path)} waypoints")

    # Build overlay
    overlay = build_overlay(
        table_config,
        ACTIVE_COLOR,
        DISABLED_ZONES,
        adversaries,
        astar_path,
        vg_path,
    )

    # Inject overlay before </svg>
    output_svg = base_svg.replace('</svg>', overlay + '\n</svg>')

    # Write output
    out_path = os.path.join(OUTPUT_DIR, scenario['file'])
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output_svg)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"  Written: {out_path} ({size_kb:.1f} KB)")
    assert size_kb > 100, f"File too small: {size_kb:.1f} KB"

print("\nAll 3 SVG files generated successfully!")