-- Granting permission to admins and clients of beybladedb

DROP USER IF EXISTS 'jlavin'@'localhost';
DROP USER IF EXISTS 'gokus'@'localhost';
DROP USER IF EXISTS 'midoriyai'@'localhost';

-- Create admins (BeyAdmin)
CREATE USER 'jlavin'@'localhost' IDENTIFIED BY 'jlavinpw';


-- Create clients (Bladers)
CREATE USER 'gokus'@'localhost' IDENTIFIED BY 'gokuspw';
CREATE USER 'midoriyai'@'localhost' IDENTIFIED BY 'midoriyaipw';

-- Grant all priveleges to BeyAdmins

GRANT ALL PRIVILEGES ON beybladedb.* TO 'jlavin'@'localhost';


-- Grant priveleges to Bladers

-- Grant SELECT permission on beyblades and parts tables to Bladers
GRANT SELECT ON beybladedb.beyblades TO 'gokus'@'localhost';
GRANT SELECT ON beybladedb.parts TO 'gokus'@'localhost';
GRANT SELECT ON beybladedb.beycollection TO 'gokus'@'localhost';
GRANT SELECT ON beybladedb.beyblades TO 'midoriyai'@'localhost';
GRANT SELECT ON beybladedb.parts TO 'midoriyai'@'localhost';
GRANT SELECT ON beybladedb.beycollection TO 'midoriyai'@'localhost';

-- Grand SELECT permission on users to all clients
GRANT SELECT ON beybladedb.users TO 'gokus'@'localhost';
GRANT SELECT ON beybladedb.users TO 'midoriyai'@'localhost';

-- Grant INSERT, UPDATE, and DELETE permissions on beycollection table to 
-- Bladers
GRANT INSERT, UPDATE, DELETE ON beybladedb.beycollection 
    TO 'gokus'@'localhost';
GRANT INSERT, UPDATE, DELETE ON beybladedb.beycollection 
    TO 'midoriyai'@'localhost';

-- Grant EXECUTE permission on the sp_add_beyblade procedure to Bladers
-- This allows Bladers to perform actions encapsulated by the procedure, even
-- if they don't have direct permissions to perform those actions on the
-- underlying tables ('beyblades' table)
GRANT EXECUTE ON PROCEDURE beybladedb.sp_add_beyblade TO 'gokus'@'localhost';
GRANT EXECUTE ON PROCEDURE beybladedb.sp_add_beyblade 
    TO 'midoriyai'@'localhost';
GRANT EXECUTE ON FUNCTION beybladedb.authenticate TO 'gokus'@'localhost';
GRANT EXECUTE ON FUNCTION beybladedb.authenticate TO 'midoriyai'@'localhost';

GRANT SELECT ON beybladedb.battles TO 'gokus'@'localhost';
GRANT SELECT ON beybladedb.battles TO 'midoriyai'@'localhost';


GRANT EXECUTE ON PROCEDURE beybladedb.sp_add_user TO 'gokus'@'localhost';
GRANT EXECUTE ON PROCEDURE beybladedb.sp_add_user TO 'midoriyai'@'localhost';
GRANT INSERT ON beybladedb.users TO 'gokus'@'localhost';
GRANT INSERT ON beybladedb.users TO 'midoriyai'@'localhost';

GRANT EXECUTE ON FUNCTION beybladedb.udf_heaviest_beyblade_for_type 
    TO 'gokus'@'localhost';
GRANT EXECUTE ON FUNCTION beybladedb.udf_heaviest_beyblade_for_type 
    TO 'midoriyai'@'localhost';

FLUSH PRIVILEGES;
