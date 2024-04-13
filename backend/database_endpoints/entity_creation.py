import json
import os
import shutil
from typing import Dict
import pandas as pd
from backend.json_policies.factory import PolicyFactory
from backend.requests.requests import Request
from utils.errors import AssociationAlreadyExistsError, MalformedEntityError

TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    # MAURI PUT YOUR PATH HERE
    TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    TEMPORARY_DATA_ROOT = "/home/ubuntu/Database"


class EntityEntryDataManagement:
    def __init__(self, request: Request):
        self._request = request

    @staticmethod
    def _allocate_new_association(name: str):
        """
        Allocates the data space for the new association
        :param name:
        :return:
        """
        os.mkdir(f"{TEMPORARY_DATA_ROOT}/organization_{name}")

    @staticmethod
    def _deallocate_new_association(name: str):
        """
        Deallocates space for an association.
        :param name:
        :return:
        """
        shutil.rmtree(f"{TEMPORARY_DATA_ROOT}/organization_{name}")

    @staticmethod
    def _validate_valid_entity_create_request(entity_definition: Dict, org_name: str):
        """
        Recursively verifies that when creating an entity, it be workin
        :param entity_definition:
        :param org_name:
        :return:
        """
        if "Entity_Name" not in entity_definition:
            raise MalformedEntityError("Entity_Name must be defined in your entities. Ex: eventa")
        if entity_definition["Type"] not in ["Ticketed", "Routing", "Slotted"]:
            raise MalformedEntityError("Type of entity must be Ticketed, Routing, or Slotted.")
        if entity_definition["Type"] in ["Slotted", "Ticketed"] and "Collect" not in entity_definition:
            raise MalformedEntityError("Define what data is to be collected for your ticketed/slotted entities.")
        if entity_definition["Type"] == "Ticketed" and "Available" not in entity_definition:
            raise MalformedEntityError("Must define Available in ticketed entities.")
        if entity_definition["Type"] == "Slotted" and ("StartKey" not in entity_definition or "EndKey" not in entity_definition):
            raise MalformedEntityError("Must define StartKey and EndKey in slotted entities.")
        if "Policy" in entity_definition:
            PolicyFactory.get_policy_from_argument(entity_definition["Policy"], org_name=org_name)
        if "Children" in entity_definition:
            for child in entity_definition["Children"]:
                EntityEntryDataManagement._validate_valid_entity_create_request(child, org_name)

    @staticmethod
    def _generate_data_sheet(entity_definition: Dict, org_name: str) -> None:
        """
        Gicen the definition of an entity being created, generates data tables
        :param entity_definition:
        :param org_name:
        :return:
        "Collect": {
          "name": "user.name",
          "email": "user.email",
          "quantity": "data.quantity",
          "level": "data.level"
        }
        """
        name = entity_definition["Entity_Name"]
        collect = entity_definition["Collect"]
        type = entity_definition["Type"]
        # Create the info sheet
        if type == "Ticketed":
            info_sheet = {
                "available": [entity_definition["Available"]]
            }
        else:
            info_sheet = {
                "start_key": [entity_definition["StartKey"]],
                "end_key": [entity_definition["EndKey"]],
                "strict": [1]
            }
        info_sheet.update(
            {f"header::{key}": [collect[key]] for key in collect}
        )
        info_sheet = pd.DataFrame(info_sheet)
        info_sheet.to_csv(f"{TEMPORARY_DATA_ROOT}/organization_{org_name}/{name}_resources_info.csv", index=False)
        # Create the empty expended sheet
        expended = pd.DataFrame({key: [] for key in collect})
        expended.to_csv(f"{TEMPORARY_DATA_ROOT}/organization_{org_name}/{name}_resources_expended.csv", index=False)

    def build_new(self) -> bool:
        """
        Builds a brand new organization, it's policies, and it's defined entities
        :return:
        """
        requested = self._request.raw_request
        # Assert that the root name is not taken
        if os.path.exists(f"{TEMPORARY_DATA_ROOT}/organization_{requested['OrganizationName']}"):
            raise AssociationAlreadyExistsError(f"Organization {requested['OrganizationName']} already exists.")
        # Allocate the association
        EntityEntryDataManagement._allocate_new_association(requested['OrganizationName'])
        # Now we make sure we can actually build every defined policy
        try:
            # We open into a try so we can deallocate an association if something goes wrong
            policies = {}
            if "Policies" in requested:
                for name, policy_definition in requested["Policies"].items():
                    # Prepare these policies if they are well-defined
                    # This may throw an error which will go back to the client
                    PolicyFactory.get_policy_from_dict(policy_definition)
                    policies[name] = policy_definition
            # Policy build success! Let us start writing shit
            if len(policies) > 0:
                os.mkdir(f"{TEMPORARY_DATA_ROOT}/organization_{requested['OrganizationName']}/policies")
                for policy_name, policy in policies.items():
                    with open(f"{TEMPORARY_DATA_ROOT}/organization_{requested['OrganizationName']}/policies/{policy_name}.json",
                              "w+") as file:
                        json.dump(policy, file, indent=4)
            # The root may have a policy. In this case, make sure it is valid
            if "Policy" in requested:
                # We do this after policy file writes, because maybe it calls on one by name
                PolicyFactory.get_policy_from_argument(requested["Policy"], org_name=requested["OrganizationName"])
            # Check on entities
            for entity_definition in requested["Entities"]:
                EntityEntryDataManagement._validate_valid_entity_create_request(entity_definition, requested["OrganizationName"])
            # If we get here, all entities and policies are valid! Wonderful.
            # Now build the fucking tree - and the datasets while we are at it.
            """
              Entity_Name": "uofc",
              "Type": "Routing",
              "Policy": {
                "required_headers": {
                  "headers": [
                    "user_attributes.ucid",
                    "user_attributes.undergrad"
                  ]
                }
              },
              "Children": []
            """
            """
            {
              "Entity_Name": "eventa",
              "Type": "Ticketed",
              "Available": 100,
              "Policy": "event_policy",
              "Collect": {
                "name": "user.name",
                "email": "user.email",
                "quantity": "data.quantity",
                "level": "data.level"
              }
              "Children": [....]
            }
            """
            entity_definition = {
                "Entity_Name": requested["OrganizationName"],
                "Type": "Routing",
                "Policy": requested.get("Policy", "FullApproval"),
                "Children": []
            }

            def recursive_build_entity_definition(current_definition, entity_at_level) -> Dict:
                """
                Builds the tree + generates all required data sheets
                :param current_definition:
                :param entity_at_level:
                :return:
                """
                if "Collect" in entity_at_level:
                    EntityEntryDataManagement._generate_data_sheet(entity_at_level, requested["OrganizationName"])
                entity = {
                    "Entity_Name": entity_at_level["Entity_Name"],
                    "Type": entity_at_level["Type"],
                    "Policy": entity_at_level.get("Policy", "FullApproval"),
                    "Children": []
                }
                for child in entity_at_level.get("Children", []):
                    entity = recursive_build_entity_definition(entity, child)
                current_definition["Children"].append(entity)
                return current_definition

            for child_entity in requested["Entities"]:
                entity_definition = recursive_build_entity_definition(entity_definition, child_entity)
            # Save the entity definition
            # fuckkkkkkkkkkkkk
            with open(f"{TEMPORARY_DATA_ROOT}/organization_{requested['OrganizationName']}/entity_definition.json", "w+") as file:
                json.dump(entity_definition, file, indent=4)
            return True

        except Exception as e:
            # Clean out failed build, and re-raise the exception
            EntityEntryDataManagement._deallocate_new_association(requested['OrganizationName'])
            raise e
