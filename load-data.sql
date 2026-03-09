-- This script will load 5 CSV files into various tables for the Beyblade database (beybladedb).
-- Ensure that the CSV files are in root directory and propertly formatted before executing.

-- Load the data for users table
LOAD DATA LOCAL INFILE 'users.csv' INTO TABLE users
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Load the data for parts table
LOAD DATA LOCAL INFILE 'parts.csv' INTO TABLE parts
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Load the data for beyblades table
LOAD DATA LOCAL INFILE 'beyblades.csv' INTO TABLE beyblades
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Load the data for beycollection table
LOAD DATA LOCAL INFILE 'beycollection.csv' INTO TABLE beycollection
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Load the data for battles table
LOAD DATA LOCAL INFILE 'battles.csv' INTO TABLE battles
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
