import logging
import time

from ia.pathfinding.astar import AStar
from ia.pathfinding.visibility_graph import VisibilityGraph
from ia.tests.abstract_test import AbstractTest
from ia.utils.position import Position

RUNS = 5  # nombre de répétitions pour la mesure du path seul


def _ms(ns: int) -> float:
    return ns / 1e6


class TestComparePathfinding(AbstractTest):
    """
    Compare AStar (grille Lua) vs VisibilityGraph sur le même scénario.

    Scénarios
    ---------
    1. Sans adversaire                  — chemin de référence
    2. Adversaire léger (1 robot)       — force un contournement, chemin trouvable
    3. Adversaires agressifs (2 robots) — bloquent toute la largeur de la table

    Pour chaque scénario : init + path mesuré, puis le path seul répété RUNS fois.
    Lance via : python ia/test.py visibility_graph 2025 princess DEBUG
    """

    def test(self) -> None:
        logger = logging.getLogger(__name__)

        start = Position(200, 200)
        goal = Position(1400, 2300)
        active_color = "color0"
        dynamic_zones_to_deactivate = ["gradin_o", "gradin_e"]

        # Adversaire latéral : dans la zone déjà interdite côté droit (start_front),
        # ne bloque aucun waypoint du chemin principal → chemin inchangé, mesure l'overhead pur.
        adversary_light = [{"x": 1800, "y": 1500}]
        # Deux adversaires au centre : bloquent toute la largeur utilisable.
        # Les deux algos doivent conclure "pas de chemin" — compare la vitesse de détection.
        adversary_heavy = [{"x": 1000, "y": 1200}, {"x": 800, "y": 1800}]

        # ── Init des deux algos ────────────────────────────────────────
        logger.info("=" * 70)
        logger.info("INIT")
        logger.info("=" * 70)

        t0 = time.time_ns()
        astar = AStar(table_config=self.config_data["table"], active_color=active_color)
        t_astar_init_ms = _ms(time.time_ns() - t0)
        logger.info(f"[AStar] Init : {t_astar_init_ms:.1f} ms")

        t0 = time.time_ns()
        vg = VisibilityGraph(table_config=self.config_data["table"], active_color=active_color)
        t_vg_init_ms = _ms(time.time_ns() - t0)
        logger.info(f"[VG]    Init : {t_vg_init_ms:.1f} ms")

        logger.info("")
        logger.info("Déactivations...")
        for zone_id in dynamic_zones_to_deactivate:
            astar.update_dynamic_zone(zone_id, False)
            vg.update_dynamic_zone(zone_id, False)

        # ── Scénarios ─────────────────────────────────────────────────
        scenarios = [
            ("Sans adversaire",        None),
            ("Adversaire léger (x1)",  adversary_light),
            ("Adversaires lourds (x2)", adversary_heavy),
        ]

        results = []  # (label, astar_ms, vg_ms, astar_found, vg_found)

        for label, adversaries in scenarios:
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"SCÉNARIO : {label}")
            if adversaries:
                logger.info(f"  Adversaires : {adversaries}")
            logger.info("=" * 70)

            # ── AStar ──────────────────────────────────────────────────
            astar_times = []
            for _ in range(RUNS):
                t0 = time.time_ns()
                astar.a_star(start, goal, adversaries=adversaries)
                astar_times.append(_ms(time.time_ns() - t0))
            astar_avg = sum(astar_times) / RUNS
            astar_found = bool(astar.path)

            logger.info(f"[AStar] {RUNS} runs — avg {astar_avg:.1f} ms  "
                        f"({'OK ' + str(len(astar.path)) + ' wpts' if astar_found else 'aucun chemin'})")
            if astar.path:
                for p in astar.path:
                    logger.info(f"  {p}")

            # ── VG ─────────────────────────────────────────────────────
            vg_times = []
            for _ in range(RUNS):
                t0 = time.time_ns()
                vg.compute_path(start, goal, adversaries=adversaries)
                vg_times.append(_ms(time.time_ns() - t0))
            vg_avg = sum(vg_times) / RUNS
            vg_found = bool(vg.path)

            logger.info(f"[VG]    {RUNS} runs — avg {vg_avg:.1f} ms  "
                        f"({'OK ' + str(len(vg.path)) + ' wpts' if vg_found else 'aucun chemin'})")
            if vg.path:
                for p in vg.path:
                    logger.info(f"  {p}")

            results.append((label, astar_avg, vg_avg, astar_found, vg_found))

        # ── Tableau récapitulatif ──────────────────────────────────────
        logger.info("")
        logger.info("=" * 70)
        logger.info("RÉCAPITULATIF")
        logger.info("=" * 70)
        logger.info(f"  {'Init':<30} AStar {t_astar_init_ms:>7.1f} ms   VG {t_vg_init_ms:>7.1f} ms")
        logger.info(f"  {'':<30} {'(one-time)':<20}")
        logger.info("")
        logger.info(f"  {'Scénario':<30} {'AStar':>10}   {'VG':>10}   {'Ratio':>8}   Chemin")
        logger.info(f"  {'-'*30} {'-'*10}   {'-'*10}   {'-'*8}   ------")
        for label, a_ms, v_ms, a_ok, v_ok in results:
            ratio = a_ms / v_ms if v_ms > 0 else float("inf")
            status = f"A={'OK' if a_ok else 'KO'}  VG={'OK' if v_ok else 'KO'}"
            logger.info(f"  {label:<30} {a_ms:>9.1f}ms  {v_ms:>9.1f}ms  {ratio:>6.1f}×   {status}")