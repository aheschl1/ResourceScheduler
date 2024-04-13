import json
from typing import Dict, Union

from backend.entity.entities import get_entity_class_from_type_string, Entity
from backend.json_policies.factory import PolicyFactory


class GenerateEntities:
    @staticmethod
    def generate_entity_from_json_path(path: str):
        with open(path, "r") as file:
            data = json.load(file)
        return GenerateEntities.generate_entity_from_dict(data)

    @staticmethod
    def generate_entity_from_dict(data: Dict) -> Union[Entity, dict]:
        """
        Create an entity from a dictionary
        :param data:
        :return: Entity
        """
        parent_entity_name = data["Entity_Name"]
        parent_type = data["Type"]
        parent_children = data.get("Children", [])
        parent_children = [GenerateEntities.generate_entity_from_dict(child) for child in parent_children]
        parent_policy = data.get("Policy", "FullApproval")
        return get_entity_class_from_type_string(parent_type)(
            parent_entity_name,
            PolicyFactory.get_policy_from_argument(parent_policy, org_name=parent_entity_name),
            parent_children
        )


if __name__ == "__main__":
    entity = GenerateEntities.generate_entity_from_json_path(
        "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database/organization_uofc/entity_definition.json")
    print(entity)
