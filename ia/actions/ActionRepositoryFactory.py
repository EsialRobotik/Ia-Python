from ia.actions.ActionRepository import ActionRepository
import json
import os
import logging
from ia.api.ax12 import AX12LinkSerial
from ia.actions.ax12.ActionAX12Factory import ActionAX12Factory
from ia.actions.ActionWait import ActionWait
from ia.actions.ActionList import ActionList


class ActionRepositoryFactory:
    @staticmethod
    def fromJsonFiles(folder: str, aX12LinkSerial: AX12LinkSerial) -> ActionRepository:
        logger = logging.getLogger(__name__)
        '''
        Read all actions json found into the given folder and put them into an ActionRepository 
        '''
        actions = dict()
        actionsCount = 0
        actionsAliasCount = 0
        actionRepository = ActionRepository(dict())
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".json"):
                    fullPath = os.path.join(root, file)
                    logger.debug(f"loading {fullPath}...")
                    with open(fullPath) as actionFile:
                        try:
                            actionIdLong = file[:-5].upper()
                            actionConfig = json.load(actionFile)
                            actionFile.close()

                            if "type" in actionConfig:
                                actionType = actionConfig["type"]
                                if actionType == "AX12":
                                    ax12Action = ActionAX12Factory.actionAx12FromJson(actionConfig["payload"], aX12LinkSerial)
                                    actions[actionIdLong] = ax12Action
                                elif actionType == "wait":
                                    if "duration" in actionConfig["payload"]:
                                        actions[actionIdLong] = ActionWait(actionConfig["payload"]["duration"], None)
                                    else:
                                        raise Exception(f"'duration' not found in wait action config payload")
                                elif actionType == "list":
                                    if "list" in actionConfig["payload"]:
                                        actionList = ActionList(actionRepository, actionConfig["payload"]["list"], None)
                                        actions[actionIdLong] = actionList
                                else:
                                    raise Exception(f"Unhandled action type : {actionType}")
                            if "alias" in actionConfig:
                                actionAlias = actionConfig["alias"]
                                if actionAlias in actions:
                                    logger.warning(f"Action alias '{actionAlias}' already exists in action pool and will be ovveriden by action file {fullPath}")
                                else:
                                    actionsAliasCount += 1
                                actions[actionAlias] = actions[actionIdLong]
                            actionsCount += 1
                        except Exception as e:
                            logger.debug(f"loading error : {e}")

        logger.info(f"Count of actions loaded from json files : {actionsCount} ({actionsAliasCount} alias))")
        for actionId in actions.keys():
            actionRepository.registerAction(actionId, actions[actionId])

        # TODO déclencher la vérification des ActionList

        return actionRepository