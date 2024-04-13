from backend.requests.requests import Request
from backend.entity.entities import Entity
import os
import glob

from backend.routing.generate_entities import GenerateEntities
from utils.errors import RoutingError

TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    # MAURI PUT YOUR PATH HERE
    TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    TEMPORARY_DATA_ROOT = "/home/ubuntu/Database"


class RootAuthority:
    def __init__(self, request: Request):
        self._request = request
        self._root_name = request.extract_next_route()

    def get_root(self) -> Entity:
        """
        Should return an object which can start routing the request
        This should be the head of a tree...
        #TODO do it way better
        :return:
        """
        organizations = glob.glob(f"{TEMPORARY_DATA_ROOT}/*")
        organization_names = [x.split('_')[-1] for x in organizations]
        if self._root_name not in organization_names:
            raise RoutingError(f"Root {self._root_name} does not exist")
        return (GenerateEntities
                .generate_entity_from_json_path(f"{TEMPORARY_DATA_ROOT}/organization_{self._root_name}/entity_definition.json"))
