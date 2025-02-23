from ia.actions.AbstractAction import AbstractAction

class ActionRepository:
    def __init__(self, actionList: dict[str, AbstractAction]):
        self.actionsList = actionList
    
    def hasAction(self, actionId: str) -> bool:
        return actionId in self.actionsList

    def getAction(self, actionId: str) -> AbstractAction:
        if actionId in self.actionsList:
            return self.actionsList[actionId]
        else:
            raise f'Action id {actionId} not found in action collection'

    def registerAction(self, actiactionId: str, action: AbstractAction) -> None:
        self.actionsList[actiactionId] = action