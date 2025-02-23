from ia.actions.AbstractAction import AbstractAction
from ia.api.ax12.AX12 import AX12
from ia.api.ax12.AX12Position import AX12Position
from typing import Optional
from ia.actions.ActionRepository import ActionRepository
from typing import List
import threading
import time

class ActionList(AbstractAction):

    def __init__(self, actionRepository: ActionRepository, actionList: List[str], flags: Optional[str]) -> None:
        self.actionList = actionList
        self.actionRepository = actionRepository
        self.flags = flags
        self.thread = None
        self.isFinished = False
        self.requestStop = False
    
    def checkActionListForMissing(self):
        '''
        Check that each action of the actionList exists in the action repository
        '''
        missingsIDs = []
        for a in self.actionList:
            if not self.actionRepository.hasAction(a):
                missingsIDs.append(a)
        if len(missingsIDs) > 0:
            missingActionIdsStr = ", ".join(missingsIDs)
            raise Exception(f"A least on action from the action list is missing form the action repository : {missingActionIdsStr}")

    def execute(self) -> None:
        if self.thread == None:
            self.thread = threading.Thread(target=self.threadFunction)
            self.thread.daemon = True
            self.thread.start()


    def finished(self) -> bool:
        if self.thread == None:
            return False
        return self.isFinished

    def stop(self) -> None:
        self.requestStop = True

    def reset(self) -> None:
        if self.thread == None:
            return
        if self.thread.is_alive:
            self.stop()
            self.thread.join()
        for actionId in self.actionList:
            self.actionRepository.getAction(actionId).reset()
        self.thread = None

    def getFlag(self) -> Optional[str]:
        return self.flags

    def threadFunction(self):
        '''
        Programm of the local Thread
        '''
        self.isFinished = False
        self.requestStop = False
        for actionId in self.actionList:
            if not self.requestStop:
                action = self.actionRepository.getAction(actionId)
                action.execute()
                while not action.finished() and self.requestStop == False:
                    time.sleep(0.01)
                if self.requestStop:
                    action.stop()
        self.isFinished = True