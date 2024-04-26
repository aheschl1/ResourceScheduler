import json
from abc import abstractmethod
from typing import Union, Dict, Tuple

import pandas as pd
import os

from backend.policies.factory import PolicyFactory
from backend.policies.policy import Policy
from backend.requests.requests import Request
from backend.utils.utils import validate_iso8601, hierarchical_keys, hierarchical_dict_lookup
from utils.constants import TEMPORARY_DATA_ROOT
from utils.errors import NoTicketsAvailableError, DatabaseWriteError, InvalidRequestError, InvalidTimeslotError, OverlappingTimeslotError


class PolicyManagement:
    @staticmethod
    def lookup_policy_from_org_name(org_name: str, policy_name: str) -> Union[None, Policy]:
        possible_entity_path = f"{TEMPORARY_DATA_ROOT}/organization_{org_name}/policies/{policy_name}.json"
        if os.path.exists(possible_entity_path):
            with open(possible_entity_path, "r") as file:
                return PolicyFactory.get_policy_from_dict(json.load(file))
        return None


class DataQueryManagement:
    def __init__(self, request: Request):
        raw_data = request.raw_request
        request.validate()
        self._request = request
        self._entity = raw_data['entity']
        self._recursive = raw_data['recursive']

    @staticmethod
    def read_data_from_entity_and_organization_name(org_name: str, entity_name: str) -> Tuple[Dict, Dict]:
        """
        Given an entity and organization, reads all data related to it.
        :param org_name:
        :param entity_name:
        :return: Tuple of (info, expended) as dictionaries
        """
        info_frame = pd.read_csv(f"{TEMPORARY_DATA_ROOT}/organization_{org_name}/{entity_name}_resources_info.csv")
        expended_frame = pd.read_csv(f"{TEMPORARY_DATA_ROOT}/organization_{org_name}/{entity_name}_resources_expended.csv")
        return info_frame.to_dict(), expended_frame.to_dict()

    def query(self) -> Dict:
        """
        Generates a large dictionary of all data.
        :return:
        """
        from backend.routing.root_authority import RootAuthority

        entity = RootAuthority(self._request).get_root()
        all_entities = entity.get_children_of(self._entity, self._recursive)
        # we now have the entities that we wish to question for data
        results = {}
        for current_entity in all_entities:
            try:
                data = current_entity.query_data()
                results[current_entity.name] = {
                    "info": data[0],
                    "expended": data[1]
                }
            except InvalidRequestError as e:
                results[current_entity.name] = str(e)

        return results


class DataManagement:
    def __init__(self, organization_name: str, entity_name: str):
        self.headers_map = None
        self.organization_name = organization_name
        self.entity_name = entity_name
        # what resources have been handed out, and to who
        self.data_allocated_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_expended.csv"
        # overview of the resource (max, etc...)
        self.data_information_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_info.csv"
        self.data_allocated = pd.read_csv(self.data_allocated_path)
        self.data_information = pd.read_csv(self.data_information_path)

    @abstractmethod
    def register(self, data: Dict):
        # what data we expect
        expected_headers_final = [x[8:] for x in self.data_information.columns.tolist() if x[0:8] == "header::"]
        # we need to convert that to actual request headers location with the resources_info file!
        headers_map = {header: self.data_information.iloc[0][f"header::{header}"] for header in expected_headers_final}
        # what data we have
        expected_headers_fully_qualified = set(headers_map.values())
        available_headers = set(hierarchical_keys(data))
        # manage discrepancy
        if not expected_headers_fully_qualified.issubset(available_headers):
            raise DatabaseWriteError(f"Tracking {expected_headers_fully_qualified} but provided {available_headers}")
        self.headers_map = headers_map

    def write_updates(self):
        self.data_information.to_csv(self.data_information_path, index=False)
        self.data_allocated.to_csv(self.data_allocated_path, index=False)


class TicketDataManagement(DataManagement):
    def __init__(self, organization_name: str, entity_name: str):
        super().__init__(organization_name, entity_name)

    def register(self, data: Dict):
        """
        Registers 'quantity' tickets
        :param data:
        :return:
        """
        super().register(data)
        # ensure sufficient resources
        tickets_available = self.data_information.available[0]
        tickets_available -= len(self.data_allocated)
        requested_quantity = hierarchical_dict_lookup(data, self.headers_map["quantity"])
        if tickets_available < requested_quantity:
            raise NoTicketsAvailableError(f"Requested {requested_quantity} tickets but only {tickets_available} are available.")
        if requested_quantity <= 0:
            raise InvalidRequestError(f"You must request >= 0 tickets for a ticketed resource.")

        # update data table with new tickets, then write updates
        data_arguments = {header: hierarchical_dict_lookup(data, self.headers_map[header]) for header in self.headers_map}
        self.data_allocated = pd.concat([
            self.data_allocated, pd.DataFrame([pd.Series(data_arguments)], index=[0])
        ]).reset_index(drop=True)

        self.write_updates()


class TimeslotDataManagement(DataManagement):
    def __init__(self, organization_name, entity_name):
        super().__init__(organization_name, entity_name)
        self.data_information = pd.read_csv(self.data_information_path)
        self.data_allocated = pd.read_csv(self.data_allocated_path)

    def register(self, data: Dict):
        """
        Registers a timeslot request in database.
        Allows a write request if the data_information has strict = False or there is no overlap
        :param data:
        :return:
        """
        super().register(data)
        try:
            start_time = hierarchical_dict_lookup(data, self.data_information.start_key[0])
            end_time = hierarchical_dict_lookup(data, self.data_information.end_key[0])
        except KeyError:
            raise DatabaseWriteError(f"Keyword argument for start time or end time is missing.")

        if not (validate_iso8601(start_time) and validate_iso8601(end_time)):
            raise DatabaseWriteError("Invalid timeslot format. Expected ISO 8601 format.")
        # validate timeslot
        if start_time >= end_time:
            raise InvalidTimeslotError(f"start time {start_time} is greater than or equal to end time {end_time}")

        # TODO this functionality should be defined in the policy
        if self.data_information.strict[0]:
            overlap_conditions = [
                # start is in the middle
                (self.data_allocated.start_time <= start_time) & (self.data_allocated.end_time >= start_time),
                # end is in the middle
                (self.data_allocated.start_time <= end_time) & (self.data_allocated.end_time >= end_time),
                # surrounds full
                (self.data_allocated.start_time >= start_time) & (self.data_allocated.end_time <= end_time),
            ]
            overlap_condition = None
            # build the ors of the conditions
            for condition in overlap_conditions:
                if overlap_condition is None:
                    overlap_condition = condition
                    continue
                overlap_condition = overlap_condition | condition
            # check overlaps
            overlapping_resources = self.data_allocated.loc[overlap_condition]
            overlapping_count = len(overlapping_resources)
            if overlapping_count > 0:
                raise OverlappingTimeslotError(f"Requested slot overlaps with {overlapping_count} existing timeslots.")
        # ok
        # update data table with new slots, then write updates
        data_arguments = {header: hierarchical_dict_lookup(data, self.headers_map[header]) for header in self.headers_map}
        # we interpret start key and end key differently, but still take the info!
        data_arguments.update({
            self.data_information.start_key[0].split(".")[-1]: start_time,
            self.data_information.end_key[0].split(".")[-1]: end_time
        })
        self.data_allocated = pd.concat([
            self.data_allocated, pd.DataFrame([pd.Series(data_arguments)])
        ]).reset_index(drop=True)
        self.write_updates()


if __name__ == "__main__":
    management = TimeslotDataManagement("uofc", "v100")
    management.register(start_time="2024-01-02T01:30:12.000Z", end_time="2024-01-02T02:00:12.000Z", user_id=12342,
                        user_email="ajheschl@gmail.com")
