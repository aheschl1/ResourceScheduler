# # https://ubuntu.com/server/docs/databases-mysql
# # creates database connection for package to access
# from typing import Union
#
# import mysql.connector as connector
# from mysql.connector.errors import ProgrammingError
# from mysql.connector.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
# from mysql.connector.pooling import PooledMySQLConnection
#
# TEST_DATABASE_NAME = "testdb"
# DEVELOPMENT_DATABASE_NAME = "ResourceScheduler_Development"
#
# DATABASE_CONNECTION: Union[PooledMySQLConnection | MySQLConnectionAbstract | None] = None
# DATABASE_CURSOR: Union[MySQLCursorAbstract | None] = None
#
#
# def _maybe_create_database(database_name: str) -> None:
#     """
#     Connects to MySQL without database instance
#     Creates a database, without exception handling!
#     :param database_name: The name of the database to create
#     :return:
#     """
#     assert database_name in [TEST_DATABASE_NAME, DEVELOPMENT_DATABASE_NAME], "Invalid database name"
#     db_connection = connector.connect(
#         host="localhost",
#         user="root",
#         passwd="root",
#     )
#     db_connection.connect()
#     db_connection.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
#
#
# def _initialize_package(database_name: str = DEVELOPMENT_DATABASE_NAME):
#     """
#     Create database based on state.
#     If the database already exists, simply look it up
#     Fills global variables for package access
#     :param database_name:
#     :return:
#     """
#     # TODO export details to environment variables
#     global DATABASE_CONNECTION, DATABASE_CURSOR
#     # we need to try to create the database.
#     # it may not exist, so catch the error and create it
#     _maybe_create_database(database_name)
#     DATABASE_CONNECTION = connector.connect(
#         host="localhost",
#         user="root",
#         passwd="root",
#         database=database_name
#     )
#     # create the cursor
#     DATABASE_CURSOR = DATABASE_CONNECTION.cursor()
#
#
# # initialize database connection and create database if necessary
# database_state = TEST_DATABASE_NAME
# print(f"Database initializing in {database_state}")
# _initialize_package(database_state)
