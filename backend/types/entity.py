from typing import Dict


class Entity:
    def __init__(self, data: Dict):
        self.name = data["Entity_Name"]
        self.organization = data["Entity_Organization"]
        self.type = data["Entity_Type"]
        if self.type not in ["Routing", "Ticketed", "Slotted", "Organization"]:
            raise ValueError(f"Entity type is invalid.")
        self._raw_data = data

    def get_raw_data(self):
        return self._raw_data

