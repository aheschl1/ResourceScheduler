from abc import abstractmethod

import pandas as pd
import os

from backend.utils.utils import validate_iso8601
from utils.errors import NoTicketsAvailableError, DatabaseWriteError, InvalidRequestError, InvalidTimeslotError, OverlappingTimeslotError

TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    # MAURI PUT YOUR PATH HERE
    TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"


class DataManagement:
    def __init__(self, organization_name: str, entity_name: str):
        self.organization_name = organization_name
        self.entity_name = entity_name
        # what resources have been handed out, and to who
        self.data_allocated_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_expended.csv"
        # overview of the resource (max, etc...)
        self.data_information_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_info.csv"
        self.data_allocated = pd.read_csv(self.data_allocated_path)
        self.data_information = pd.read_csv(self.data_information_path)

    @abstractmethod
    def register(self, **kwargs):
        # what data we expect
        expected_headers = set(self.data_allocated.columns.tolist())
        # what data we have
        available_headers = set(kwargs.keys())
        # manage discrepancy
        if available_headers != expected_headers:
            raise DatabaseWriteError(f"Tracking {expected_headers} but provided {available_headers}")

    def write_updates(self):
        self.data_information.to_csv(self.data_information_path, index=False)
        self.data_allocated.to_csv(self.data_allocated_path, index=False)


class TicketDataManagement(DataManagement):
    def __init__(self, organization_name: str, entity_name: str):
        super().__init__(organization_name, entity_name)

    def register(self, quantity, **kwargs):
        """
        Registers 'quantity' tickets
        :param quantity: quantity of tickets
        :param kwargs: headers in the database
        :return:
        """
        super().register(**kwargs)

        # ensure sufficient resources
        tickets_available = self.data_information.available[0]
        tickets_available -= len(self.data_allocated)
        if tickets_available < quantity:
            raise NoTicketsAvailableError(f"Requested {quantity} tickets but only {tickets_available} are available.")
        if quantity <= 0:
            raise InvalidRequestError(f"You must request >= 0 tickets.")

        # update data table with new tickets, then write updates
        self.data_allocated = pd.concat([
            self.data_allocated, pd.DataFrame([pd.Series(kwargs)] * quantity, index=[i for i in range(quantity)])
        ]).reset_index(drop=True)

        self.write_updates()


class TimeslotDataManagement(DataManagement):
    def __init__(self, organization_name, entity_name):
        super().__init__(organization_name, entity_name)
        self.data_information = pd.read_csv(self.data_information_path)
        self.data_allocated = pd.read_csv(self.data_allocated_path)

    def register(self, **kwargs):
        """
        Registers a timeslot request in database.
        Allows a write request if the data_information has strict = False or there is no overlap
        :param kwargs: The headers for request. Required start time and end time
        :return:
        """
        super().register(**kwargs)
        try:
            start_time = kwargs[self.data_information.start_key[0]]
            end_time = kwargs[self.data_information.end_key[0]]
        except KeyError:
            raise DatabaseWriteError(f"Keyword argument for start time or end time is missing.")

        if not (validate_iso8601(start_time) and validate_iso8601(end_time)):
            raise DatabaseWriteError("Invalid timeslot format. Expected ISO 8601 format.")
        # validate timeslot
        if start_time >= end_time:
            raise InvalidTimeslotError(f"start time {start_time} is greater than or equal to end time {end_time}")

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
        self.data_allocated = pd.concat([
            self.data_allocated, pd.DataFrame([pd.Series(kwargs)])
        ]).reset_index(drop=True)
        self.write_updates()


if __name__ == "__main__":
    management = TimeslotDataManagement("uofc", "v100")
    management.register(start_time="2024-01-02T01:30:12.000Z", end_time="2024-01-02T02:00:12.000Z", user_id=12342,
                        user_email="ajheschl@gmail.com")
