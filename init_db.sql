SET GLOBAL local_infile = TRUE;

DROP DATABASE IF EXISTS beybladedb;
CREATE DATABASE beybladedb;
USE beybladedb;

SOURCE setup.sql;
SOURCE load-data.sql;
SOURCE setup-passwords.sql;
SOURCE setup-routines.sql;
SOURCE grant-permissions.sql;