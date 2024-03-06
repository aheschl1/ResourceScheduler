import json
from typing import Dict

from backend.routing.entity.entities import get_entity_class_from_type_string, Entity


class GenerateEntities:
    @staticmethod
    def generate_entity_from_json_path(path: str):
        with open(path, "r") as file:
            data = json.load(file)
        return GenerateEntities.generate_entity_from_dict(data)

    @staticmethod
    def generate_entity_from_dict(data: Dict) -> Entity:
        # TODO deal with policies
        parent_entity_name = data["Entity_Name"]
        parent_type = data["Type"]
        parent_children = data.get("Children", [])
        parent_children = [GenerateEntities.generate_entity_from_dict(child) for child in parent_children]
        return get_entity_class_from_type_string(parent_type)(parent_entity_name, None, parent_children)


if __name__ == "__main__":
    entity = GenerateEntities.generate_entity_from_json_path(
        "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database/organization_uofc/entity_definition.json")
    print(entity)
