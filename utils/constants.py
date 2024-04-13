import os

DEFAULT_IP = os.environ.get("SERVER_IP", "10.0.0.43")
DEFAULT_PORT = os.environ.get("SERVER_PORT", 6000)
BUFFER_SIZE = 2048

SUCCESS = 200
POOR_FORMAT = 400
REJECTED_BY_ENTITY = 401
ROUTE_DNE = 404
INVALID_REQUEST = 403
UNKNOWN = 402

TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    # MAURI PUT YOUR PATH HERE
    TEMPORARY_DATA_ROOT = "/home/andrewheschl/PycharmProjects/ResourceScheduler/backend/temp_sus_database"
if not os.path.exists(TEMPORARY_DATA_ROOT):
    TEMPORARY_DATA_ROOT = "/home/ubuntu/Database"

