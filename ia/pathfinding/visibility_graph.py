import heapq
import logging
import math
import time
from typing import Dict, List, Optional, Set, Tuple

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from ia.utils.position import Position

# Type aliases
Vertex = Tuple[float, float]
Edge = Tuple[Vertex, Vertex]   # toujours stocké avec u <= v (ordre lexicographique)
Graph = Dict[Vertex, Dict[Vertex, float]]


def _edge_key(u: Vertex, v: Vertex) -> Edge:
    return (u, v) if u <= v else (v, u)


class VisibilityGraph:
    """
    Pathfinding par graphe de visibilité avec graphe précalculé et mise à jour
    incrémentale lors des désactivations de zones.

    Stratégie de cache
    ------------------
    Init (coût unique)
        _current_vertices  = sommets de l'union de tous les obstacles actifs
                             (≈20 points pour la table 2025, vs 48 si on extrayait
                              chaque polygone séparément)
        _static_graph      = visibilité avec les forbiddenZones seules
                             (même jeu de sommets)
        _cached_graph      = visibilité avec l'union courante (static + zones actives)
        _restorable_edges  = edges présents dans _static_graph mais absents de
                             _cached_graph : bloqués par des zones dynamiques actives.

    Déactivation — cas dominant, O(|restorable| + N·V_z)
        1. union = union.difference(zone_poly)
        2. Chaque _restorable_edge redevenu visible → restauré dans le cache
        3. Les sommets propres à la zone (absents du cache) sont ajoutés
           et leurs edges calculés contre tous les sommets courants

    Activation — cas rare, full rebuild accepté.

    compute_path — O(N)
        Copie légère de _cached_graph + branchement de start/goal.
        Les adversaires optionnels filtrent les edges bloqués et ajoutent
        leurs propres sommets, sans modifier le cache.

    Interface publique
        compute_path(start, goal, adversaries=None)
        update_dynamic_zone(zone_id, active)
        path  (List[Position])
    """

    ADVERSARY_RADIUS = 200  # mm

    def __init__(self, table_config: Dict, active_color: str) -> None:
        self.config = table_config
        self.size_x: int = table_config["sizeX"]
        self.size_y: int = table_config["sizeY"]
        self.marge: int = table_config["marge"]
        self.active_color = table_config.get(active_color, active_color)  # e.g. 'jaune'
        self.path: List[Position] = []
        self.logger = logging.getLogger(__name__)

        self._table_poly = Polygon([
            (self.marge, self.marge),
            (self.size_x - self.marge, self.marge),
            (self.size_x - self.marge, self.size_y - self.marge),
            (self.marge, self.size_y - self.marge),
        ])

        # ── État persistant ────────────────────────────────────────────
        self._static_union = None            # union forbiddenZones (immuable après init)
        self._current_obstacle_union = None  # union courante (mis à jour incrémentalement)

        # Sommets candidats pour le graphe — croît à chaque déactivation
        self._current_vertices: List[Vertex] = []

        # Graphe figé : visibilité avec _static_union (même sommets que cached)
        self._static_graph: Graph = {}
        # Graphe courant : visibilité avec _current_obstacle_union
        self._cached_graph: Graph = {}
        # Edges du static_graph absents du cached_graph = bloqués par zones actives
        self._restorable_edges: Dict[Edge, float] = {}

        # Zones dynamiques : id → {polygon, active, vertices}
        self._dynamic_zones: Dict[str, dict] = {}

        t0 = time.time_ns()
        self._full_rebuild()
        self.logger.info(f"[VG] Init in {(time.time_ns() - t0) / 1e6:.2f} ms")

    # ──────────────────────────────────────────────────────────────────
    # Géométrie
    # ──────────────────────────────────────────────────────────────────

    def _find_blocking_zones(self, pt) -> list[str]:
        """Identifie les zones (forbidden + dynamic) qui contiennent le point donné."""
        blocking = []
        shapely_pt = Point(pt)
        for zone in self.config["forbiddenZones"]:
            if zone["type"] != self.active_color or zone["type"] == "all":
                poly = self._make_polygon(zone)
                if poly.contains(shapely_pt):
                    blocking.append(zone["id"])
        for zone_id, zdata in self._dynamic_zones.items():
            if zdata["active"] and zdata["polygon"].contains(shapely_pt):
                blocking.append(zone_id)
        return blocking

    def _make_polygon(self, zone: Dict) -> Polygon:
        if zone["forme"] == "polygone":
            pts = [(p["x"], p["y"]) for p in zone["points"]]
            return Polygon(pts).buffer(self.marge, join_style=2)  # coins vifs (mitre)
        if zone["forme"] == "cercle":
            cx, cy = zone["centre"]["x"], zone["centre"]["y"]
            return Point(cx, cy).buffer(zone["rayon"] + self.marge, resolution=16)
        raise ValueError(f"Forme inconnue : {zone['forme']}")

    def _extract_vertices(self, geometry) -> List[Vertex]:
        """Extrait les sommets extérieurs d'une géométrie Shapely."""
        if geometry is None or geometry.is_empty:
            return []
        geoms = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
        result: List[Vertex] = []
        for poly in geoms:
            for x, y in poly.exterior.coords[:-1]:
                if 0 <= x <= self.size_x and 0 <= y <= self.size_y:
                    result.append((x, y))
        return result

    def _is_visible(self, p1: Vertex, p2: Vertex, obstacle_union) -> bool:
        if p1 == p2:
            return True
        seg = LineString([p1, p2])
        if not self._table_poly.covers(seg):
            return False
        if obstacle_union is None or obstacle_union.is_empty:
            return True
        return not obstacle_union.crosses(seg) and not obstacle_union.contains(seg)

    def _build_graph(self, vertices: List[Vertex], obstacle_union) -> Graph:
        graph: Graph = {}
        n = len(vertices)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = vertices[i], vertices[j]
                if self._is_visible(u, v, obstacle_union):
                    d = math.hypot(v[0] - u[0], v[1] - u[1])
                    graph.setdefault(u, {})[v] = d
                    graph.setdefault(v, {})[u] = d
        return graph

    # ──────────────────────────────────────────────────────────────────
    # Full rebuild
    # ──────────────────────────────────────────────────────────────────

    def _full_rebuild(self) -> None:
        """Reconstruit entièrement le cache. Appelé à l'init et lors d'une activation."""
        t0 = time.time_ns()

        # 1. Union statique (forbiddenZones)
        static_polys = []
        for zone in self.config["forbiddenZones"]:
            if zone["type"] != self.active_color or zone["type"] == "all":
                self.logger.info(f"[VG] Lock forbidden zone {zone['id']}")
                static_polys.append(self._make_polygon(zone))
        self._static_union = unary_union(static_polys) if static_polys else None

        # 2. Zones dynamiques (on préserve l'état actif si déjà connu)
        prev_active = {zid: z["active"] for zid, z in self._dynamic_zones.items()}
        self._dynamic_zones = {}
        for zone in self.config["dynamicZones"]:
            poly = self._make_polygon(zone)
            active = prev_active.get(zone["id"], zone["active"])
            self._dynamic_zones[zone["id"]] = {
                "polygon": poly,
                "active": active,
                "vertices": self._extract_vertices(poly),
            }

        # 3. Union courante (static + zones actives)
        dynamic_polys = [z["polygon"] for z in self._dynamic_zones.values() if z["active"]]
        all_polys = ([self._static_union] if self._static_union else []) + dynamic_polys
        self._current_obstacle_union = unary_union(all_polys) if all_polys else None

        # 4. Sommets = vertices de l'union courante
        #    On ne prend PAS les vertices de chaque polygone individuel : l'union
        #    renvoie un jeu compact (~20 pts) car les zones qui se chevauchent sont fusionnées.
        #    Les vertices des zones inactives seront ajoutés incrémentalement à la déactivation.
        self._current_vertices = self._extract_vertices(self._current_obstacle_union)
        # Ajouter également les vertices des zones déjà inactives (cas d'un rebuild post-activation)
        known: Set[Vertex] = set(self._current_vertices)
        for zdata in self._dynamic_zones.values():
            if not zdata["active"]:
                for v in zdata["vertices"]:
                    if v not in known:
                        p = Point(v)
                        if self._current_obstacle_union is None or not self._current_obstacle_union.contains(p):
                            self._current_vertices.append(v)
                            known.add(v)

        # 5. Graphe statique (référence figée, visibilité avec static_union seulement)
        self._static_graph = self._build_graph(self._current_vertices, self._static_union)

        # 6. Graphe courant (visibilité avec l'union complète)
        self._cached_graph = self._build_graph(self._current_vertices, self._current_obstacle_union)

        # 7. Restorable edges = edges dans static_graph absents du cached_graph
        cached_edges: Set[Edge] = {
            _edge_key(u, v)
            for u, nbrs in self._cached_graph.items()
            for v in nbrs
        }
        self._restorable_edges = {}
        for u, nbrs in self._static_graph.items():
            for v, dist in nbrs.items():
                ek = _edge_key(u, v)
                if ek not in cached_edges:
                    self._restorable_edges[ek] = dist

        n_v = len(self._current_vertices)
        n_e = len(cached_edges)
        n_r = len(self._restorable_edges)
        self.logger.info(
            f"[VG] Full rebuild in {(time.time_ns() - t0) / 1e6:.2f} ms — "
            f"{n_v} vertices, {n_e} edges cached, {n_r} restorable"
        )

    # ──────────────────────────────────────────────────────────────────
    # Mise à jour incrémentale (déactivation)
    # ──────────────────────────────────────────────────────────────────

    def _deactivate_zone(self, zone_id: str) -> None:
        t0 = time.time_ns()
        zdata = self._dynamic_zones[zone_id]

        # 1. Retirer la zone de l'union courante
        if self._current_obstacle_union is not None:
            new_union = self._current_obstacle_union.difference(zdata["polygon"])
            self._current_obstacle_union = None if new_union.is_empty else new_union

        # 2. Restaurer les edges redevenus visibles
        restored = 0
        still_blocked: Dict[Edge, float] = {}
        for ek, dist in self._restorable_edges.items():
            u, v = ek
            if self._is_visible(u, v, self._current_obstacle_union):
                self._cached_graph.setdefault(u, {})[v] = dist
                self._cached_graph.setdefault(v, {})[u] = dist
                restored += 1
            else:
                still_blocked[ek] = dist
        self._restorable_edges = still_blocked

        # 3. Ajouter les sommets propres à cette zone (nouveaux waypoints dans l'espace libre)
        new_verts: List[Vertex] = []
        for pt in zdata["vertices"]:
            if pt in self._cached_graph:
                continue  # déjà connu
            p = Point(pt)
            inside = (
                self._current_obstacle_union is not None
                and self._current_obstacle_union.contains(p)
            )
            if not inside:
                new_verts.append(pt)

        existing = list(self._current_vertices)
        for nv in new_verts:
            self._cached_graph.setdefault(nv, {})
            for ev in existing:
                if self._is_visible(nv, ev, self._current_obstacle_union):
                    d = math.hypot(ev[0] - nv[0], ev[1] - nv[1])
                    self._cached_graph[nv][ev] = d
                    self._cached_graph[ev][nv] = d
            self._current_vertices.append(nv)
            existing.append(nv)  # les nouveaux sommets peuvent aussi se voir entre eux

        zdata["active"] = False
        self.logger.info(
            f"[VG] Deactivate '{zone_id}' in {(time.time_ns() - t0) / 1e6:.2f} ms — "
            f"{restored} edges restored, +{len(new_verts)} vertices"
        )

    # ──────────────────────────────────────────────────────────────────
    # API publique
    # ──────────────────────────────────────────────────────────────────

    def update_dynamic_zone(self, zone_id: str, active: bool) -> None:
        """Active ou désactive une zone dynamique."""
        zdata = self._dynamic_zones.get(zone_id)
        if zdata is None or zdata["active"] == active:
            return
        if active:
            # Activation (rare) — coût de rebuild accepté
            self.logger.info(f"[VG] Activate '{zone_id}' — full rebuild")
            zdata["active"] = True
            self._full_rebuild()
        else:
            self._deactivate_zone(zone_id)

    def compute_path(
        self,
        start: Position,
        goal: Position,
        adversaries: Optional[List[Dict]] = None,
    ) -> None:
        """
        Calcule le chemin via le graphe de visibilité.

        Parameters
        ----------
        start, goal : Position (coordonnées en mm)
        adversaries : list of {"x": int, "y": int}, optionnel
            Obstacles circulaires temporaires de rayon ADVERSARY_RADIUS + marge.
            N'affectent pas le cache.
        """
        self.path = []
        t0 = time.time_ns()
        self.logger.info(f"[VG] Compute path {start} → {goal}")

        try:
            start_pt: Vertex = (float(start.x), float(start.y))
            goal_pt: Vertex = (float(goal.x), float(goal.y))

            # ── Obstacles adversaires ──────────────────────────────────
            if adversaries:
                # Approximation octogonale (resolution=2 → 8 côtés).
                # ADVERSARY_RADIUS représente la demi-diagonale maximale d'un adversaire
                # rectangulaire dont l'angle dans le repère de la table est inconnu.
                # L'octogone est inscrit dans ce cercle : l'apothème vaut R·cos(22.5°) ≈ 0.924·R,
                # ce qui reste une marge de sécurité acceptable.
                # Les sommets de l'octogone ne sont PAS ajoutés au graphe (évite O(N_adv²)
                # checks Shapely) ; l'adversaire se contente de filtrer les edges bloqués.
                adv_polys = [
                    Point(a["x"], a["y"]).buffer(
                        self.ADVERSARY_RADIUS + self.marge, resolution=2
                    )
                    for a in adversaries
                ]
                adv_union = unary_union(adv_polys)
            else:
                adv_union = None

            # ── Validation (checks séparés, évite de construire effective_union) ──
            # On teste start/goal contre chaque union individuellement plutôt que
            # de les fusionner (unary_union crée une géométrie complexe qui ralentit
            # tous les checks de visibilité suivants).
            for label, pt in (("Start", start_pt), ("Goal", goal_pt)):
                blocked = (
                    self._current_obstacle_union is not None
                    and self._current_obstacle_union.contains(Point(pt))
                ) or (
                    adv_union is not None
                    and adv_union.contains(Point(pt))
                )
                if blocked:
                    blocking = self._find_blocking_zones(pt)
                    zones_str = ", ".join(blocking) if blocking else "union de zones"
                    self.logger.error(f"[VG] {label} ({pt[0]}, {pt[1]}) is blocked by: {zones_str}")
                    return

            # ── Graphe temporaire : copie légère du cache ─────────────
            temp: Graph = {u: dict(nb) for u, nb in self._cached_graph.items()}

            # Avec adversaires : retirer les edges qu'ils bloquent
            if adv_union is not None:
                blocked_by_adv: List[Edge] = [
                    (u, v)
                    for u, nbrs in temp.items()
                    for v in nbrs
                    if u <= v and (
                        adv_union.crosses(LineString([u, v]))
                        or adv_union.contains(LineString([u, v]))
                    )
                ]
                for u, v in blocked_by_adv:
                    temp[u].pop(v, None)
                    if v in temp:
                        temp[v].pop(u, None)

            # ── Brancher start et goal ────────────────────────────────
            new_pts: List[Vertex] = [start_pt, goal_pt]
            for pt in new_pts:
                temp.setdefault(pt, {})

            known_pts = self._current_vertices
            for i, u in enumerate(new_pts):
                for v in known_pts:
                    if u == v:
                        continue
                    # Checks séparés sur les deux unions (plus rapide que effective_union fusionnée)
                    if self._is_visible(u, v, self._current_obstacle_union) and (
                        adv_union is None or self._is_visible(u, v, adv_union)
                    ):
                        d = math.hypot(v[0] - u[0], v[1] - u[1])
                        temp[u][v] = d
                        temp.setdefault(v, {})[u] = d
                for v in new_pts[i + 1:]:
                    if self._is_visible(u, v, self._current_obstacle_union) and (
                        adv_union is None or self._is_visible(u, v, adv_union)
                    ):
                        d = math.hypot(v[0] - u[0], v[1] - u[1])
                        temp[u][v] = d
                        temp.setdefault(v, {})[u] = d

            self.logger.info(f"[VG] Temp graph in {(time.time_ns() - t0) / 1e6:.2f} ms")

            # ── Dijkstra ──────────────────────────────────────────────
            raw = self._dijkstra(temp, start_pt, goal_pt)
            if raw:
                self.path = [Position(int(round(x)), int(round(y))) for x, y in raw]
                self.logger.info(f"[VG] Path: {len(self.path)} waypoints")
            else:
                self.logger.error("[VG] No path found.")

        except Exception as exc:
            self.logger.error(f"[VG] Error: {exc}", exc_info=True)
        finally:
            self.logger.info(f"[VG] Total in {(time.time_ns() - t0) / 1e6:.2f} ms")

    # ──────────────────────────────────────────────────────────────────
    # Dijkstra
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _dijkstra(graph: Graph, start: Vertex, goal: Vertex) -> Optional[List[Vertex]]:
        dist: Dict[Vertex, float] = {start: 0.0}
        prev: Dict[Vertex, Optional[Vertex]] = {start: None}
        heap = [(0.0, start)]
        visited: Set[Vertex] = set()

        while heap:
            cost, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            if node == goal:
                path: List[Vertex] = []
                cur: Optional[Vertex] = goal
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                return list(reversed(path))
            for neighbor, weight in graph.get(node, {}).items():
                nc = cost + weight
                if neighbor not in dist or nc < dist[neighbor]:
                    dist[neighbor] = nc
                    prev[neighbor] = node
                    heapq.heappush(heap, (nc, neighbor))

        return None