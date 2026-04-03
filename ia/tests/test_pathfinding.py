import logging
import time

from ia.pathfinding.visibility_graph import VisibilityGraph
from ia.tests.abstract_test import AbstractTest
from ia.utils.position import Position

RUNS = 5  # nombre de répétitions pour la mesure du path seul


def _ms(ns: int) -> float:
    return ns / 1e6


class TestPathfinding(AbstractTest):
    """
    Benchmark du VisibilityGraph sur différents scénarios.

    Scénarios
    ---------
    1. Sans adversaire                  — chemin de référence
    2. Adversaire léger (1 robot)       — overhead pur (adversaire hors couloir principal)
    3. Adversaires lourds (2 robots)    — bloquent toute la largeur de la table

    Lance via : python ia/test.py visibility_graph 2025 princess DEBUG
    """

    def test(self) -> None:
        logger = logging.getLogger(__name__)

        start = Position(200, 200)
        goal = Position(1400, 2300)
        active_color = "color0"
        dynamic_zones_to_deactivate = ["gradin_o", "gradin_e"]

        adversary_light = [{"x": 1800, "y": 1500}]
        adversary_heavy = [{"x": 1000, "y": 1200}, {"x": 800, "y": 1800}]

        # ── Init ──────────────────────────────────────────────────────
        logger.info("=" * 70)
        logger.info("INIT")
        logger.info("=" * 70)

        t0 = time.time_ns()
        vg = VisibilityGraph(table_config=self.config_data["table"], active_color=active_color)
        t_init_ms = _ms(time.time_ns() - t0)
        logger.info(f"[VG] Init : {t_init_ms:.1f} ms")

        logger.info("")
        logger.info("Déactivations...")
        for zone_id in dynamic_zones_to_deactivate:
            vg.update_dynamic_zone(zone_id, False)

        # ── Scénarios ─────────────────────────────────────────────────
        scenarios = [
            ("Sans adversaire",         None),
            ("Adversaire léger (x1)",   adversary_light),
            ("Adversaires lourds (x2)", adversary_heavy),
        ]

        results = []  # (label, avg_ms, found)

        for label, adversaries in scenarios:
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"SCÉNARIO : {label}")
            if adversaries:
                logger.info(f"  Adversaires : {adversaries}")
            logger.info("=" * 70)

            times = []
            for _ in range(RUNS):
                t0 = time.time_ns()
                vg.compute_path(start, goal, adversaries=adversaries)
                times.append(_ms(time.time_ns() - t0))
            avg = sum(times) / RUNS
            found = bool(vg.path)

            logger.info(f"[VG] {RUNS} runs — avg {avg:.1f} ms  "
                        f"({'OK ' + str(len(vg.path)) + ' wpts' if found else 'aucun chemin'})")
            if vg.path:
                for p in vg.path:
                    logger.info(f"  {p}")

            results.append((label, avg, found))

        # ── Récapitulatif ─────────────────────────────────────────────
        logger.info("")
        logger.info("=" * 70)
        logger.info("RÉCAPITULATIF")
        logger.info("=" * 70)
        logger.info(f"  Init : {t_init_ms:.1f} ms (one-time)")
        logger.info("")
        logger.info(f"  {'Scénario':<30} {'Avg':>10}   Chemin")
        logger.info(f"  {'-'*30} {'-'*10}   ------")
        for label, avg, found in results:
            logger.info(f"  {label:<30} {avg:>9.1f}ms   {'OK' if found else 'KO'}")