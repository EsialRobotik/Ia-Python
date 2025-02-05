class AX12Compliance:
    seuils = [3, 7, 15, 31, 63, 127, 254]

    def __init__(self, friendly_value: int):
        if friendly_value < 1 or friendly_value > len(self.seuils):
            raise ValueError(f"Compliance must be set between 1 and {len(self.seuils)} included, given: {friendly_value}")
        self.raw_value = self.seuils[friendly_value - 1]
        self.friendly_value = friendly_value

    @staticmethod
    def from_friendly_value(i: int):
        return AX12Compliance(i)

    @staticmethod
    def from_raw(raw: int):
        if raw < 0 or raw > 254:
            raise ValueError("Raw must be set between 0 and 254 included")
        
        for i, seuil in enumerate(AX12Compliance.seuils):
            if raw < seuil:
                return AX12Compliance(i + 1)
        
        return AX12Compliance(len(AX12Compliance.seuils))

    def get_value_as_string(self):
        return f"{self.friendly_value}/{len(self.seuils)}"

    def get_raw_value(self):
        return self.raw_value

    def get_friendly_value(self):
        return self.friendly_value