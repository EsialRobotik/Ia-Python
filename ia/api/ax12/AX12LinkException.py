class AX12LinkException(Exception):
    """
    Exception raised for errors in the AX12 link.

    Attributes:
        reason -- explanation of the error
        previous -- previous exception that caused this error
    """

    def __init__(self, reason: str, previous: Exception =None) -> None:
        """
        Initializes the AX12LinkException with a reason and an optional previous exception.
        Args:
            reason (str): The reason for the exception.
            previous (Exception, optional): The previous exception that led to this exception. Defaults to None.
        """

        self.reason = reason
        self.previous = previous
        super().__init__(reason)

    def __str__(self) -> str:
        """
        Returns a string representation of the AX12LinkException.
        If there is a previous exception, it includes the reason and the previous exception's message.
        Otherwise, it returns only the reason.
        Returns:
            str: The string representation of the exception.
        """

        if self.previous:
            return f"{self.reason} (caused by {self.previous})"
        return self.reason