import pandas as pd
import os

from utils.errors import NoTicketsAvailableError, DatabaseWriteError

TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    # MAURI PUT YOUR PATH HERE
    TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"


class TicketDataManagement:
    def __init__(self, organization_name: str, entity_name: str):
        self.organization_name = organization_name
        self.entity_name = entity_name

        # what tickets have been handed out, and to who
        self.tickets_allocated_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_expended.csv"
        # overview of the resource (max, etc...)
        self.resource_data_path = f"{TEMPORARY_DATA_ROOT}/organization_{organization_name}/{entity_name}_resources_info.csv"

        self.tickets_allocated = pd.read_csv(self.tickets_allocated_path)
        self.tickets_data = pd.read_csv(self.resource_data_path)

    def register_tickets(self, quantity, **kwargs):
        tickets_available = self.tickets_data.available[0]
        tickets_available -= len(self.tickets_allocated)
        if tickets_available < quantity:
            raise NoTicketsAvailableError(f"Requested {quantity} tickets but only {tickets_available} are available.")
        # what data we expect
        expected_headers = self.tickets_allocated.columns.tolist()
        # what data we have
        available_headers = list(kwargs.keys())
        # manage discrepancy
        if available_headers != expected_headers:
            raise DatabaseWriteError(f"Tracking {expected_headers} but provided {available_headers}")

        # update data table with new tickets, then write updates
        self.tickets_allocated = pd.concat([
            self.tickets_allocated, pd.DataFrame([pd.Series(kwargs)] * quantity, index=[i for i in range(quantity)])
        ]).reset_index(drop=True)

        self._write_updates()

    def _write_updates(self):
        self.tickets_data.to_csv(self.resource_data_path, index=False)
        self.tickets_allocated.to_csv(self.tickets_allocated_path, index=False)


if __name__ == "__main__":
    management = TicketDataManagement("uofc", "Campus_Tour")
    management.register_tickets(100, user_id=12342, user_email="ajheschl@gmail.com")
