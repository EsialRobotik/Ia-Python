from api.ax12.enums.AX12Error import AX12Error

class AX12Exception(Exception):
    """
    Custom exception class for AX12 errors.
    Attributes:
        msg (str): The error message.
        errors (tuple): Additional errors associated with the exception.
    Methods:
        __str__(): Returns a string representation of the exception.
        contains(err): Checks if a specific error is contained in the exception.
    """


    def __init__(self, msg: str =None, *errors: AX12Error):
        """
        Initialize an AX12Exception instance.
        Args:
            msg (str, optional): The error message. Defaults to None.
            *errors (AX12Error): Additional AX12Error instances related to the exception.
        """

        super().__init__(msg)
        self.errors = errors

    def __str__(self):
        """
        Returns a string representation of the AX12Exception instance.
        This method constructs a string by combining the string representation
        of the base exception (if any) and the string representations of all
        errors contained in the `errors` attribute of the instance.
        Returns:
            str: A string representation of the exception.
        """
        
        sb = []
        if super().__str__():
            sb.append(super().__str__())
        first = True
        for err in self.errors:
            if sb:
                if first:
                    sb.append(' ')
                    first = False
                else:
                    sb.append(", ")
            sb.append(str(err))
        return ''.join(sb)

    def contains(self, err: AX12Error):
        """
        Check if the specified AX12Error is in the list of errors.
        Args:
            err (AX12Error): The error to check for in the list of errors.
        Returns:
            bool: True if the error is in the list, False otherwise.
        """

        return err in self.errors