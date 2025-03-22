class AX12Compliance:
    """
    Represents the compliance settings for an AX12 servo motor.
    """
    thresholds = [3, 7, 15, 31, 63, 127, 254]

    def __init__(self, friendly_value: int) -> None:
        """
        Initializes the AX12Compliance object with a friendly value.
        Args:
            friendly_value (int): The friendly value to set. Must be between 1 and the length of the thresholds.
        Raises:
            ValueError: If the friendly value is not within the valid range.
        """
        if friendly_value < 1 or friendly_value > len(self.thresholds):
            raise ValueError(f"Compliance must be set between 1 and {len(self.thresholds)} included, given: {friendly_value}")
        self.raw_value = self.thresholds[friendly_value - 1]
        self.friendly_value = friendly_value

    @staticmethod
    def from_friendly_value(i: int) -> 'AX12Compliance':
        """
        Creates an AX12Compliance object from a friendly value.

        Args:
            i (int): The friendly value to convert to an AX12Compliance object.

        Returns:
            AX12Compliance: The created AX12Compliance object.
        """
        return AX12Compliance(i)

    @staticmethod
    def from_raw(raw: int) -> 'AX12Compliance':
        """
        Creates an AX12Compliance object from a raw value.

        Args:
            raw (int): The raw value to convert to an AX12Compliance object. Must be between 0 and 254.

        Returns:
            AX12Compliance: The created AX12Compliance object.

        Raises:
            ValueError: If the raw value is not within the valid range.
        """
        if raw < 0 or raw > 254:
            raise ValueError("Raw must be set between 0 and 254 included")

        for i, seuil in enumerate(AX12Compliance.thresholds):
            if raw < seuil:
                return AX12Compliance(i + 1)

        return AX12Compliance(len(AX12Compliance.thresholds))

    def get_value_as_string(self) -> str:
        """
        Returns the friendly value as a string.

        Returns:
            str: The friendly value as a string in the format "friendly_value/total_thresholds".
        """
        return f"{self.friendly_value}/{len(self.thresholds)}"

    def get_raw_value(self) -> int:
        """
        Returns the raw value of the AX12Compliance object.

        Returns:
            int: The raw value.
        """
        return self.raw_value

    def get_friendly_value(self) -> int:
        """
        Returns the friendly value of the AX12Compliance object.

        Returns:
            int: The friendly value.
        """
        return self.friendly_value