import logging

from ia.manager.strategy_manager import StrategyManager
from ia.tests.abstract_test import AbstractTest


class TestStrategyManager(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        logger.info('Testing StrategyManager...')
        strategy_manager = StrategyManager(self.year)
        logger.info("/!\/!\/!\/!\/!\/!\/!\/!\/!\/!\/!\ Prepare color0 objectives...")
        strategy_manager.prepare_objectives(is_color0=True)
        logger.info(strategy_manager)
        first_objective = strategy_manager.get_next_objective()
        logger.info(f'First objective: {first_objective}')
        first_step = first_objective.get_next_step([])
        logger.info(f'First step: {first_step}')
        second_step = first_objective.get_next_step([])
        logger.info(f'Second step: {second_step}')
        second_objective = strategy_manager.get_next_objective()
        logger.info(f'Second objective: {second_objective}')

        strategy_manager = StrategyManager(self.year)
        logger.info("/!\/!\/!\/!\/!\/!\/!\/!\/!\/!\/!\ Prepare color3000 objectives...")
        strategy_manager.prepare_objectives(is_color0=False)
        logger.info(strategy_manager)
        first_objective = strategy_manager.get_next_objective()
        logger.info(f'First objective: {first_objective}')
        first_step = first_objective.get_next_step([])
        logger.info(f'First step: {first_step}')
        second_step = first_objective.get_next_step([])
        logger.info(f'Second step: {second_step}')
        second_objective = strategy_manager.get_next_objective()
        logger.info(f'Second objective: {second_objective}')