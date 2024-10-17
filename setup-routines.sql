-- This script defines stored procedures, functions, and triggers for managing custom Beyblade
-- configurations, recording battles, and calculating the heaviest Beyblade by type.

-- Stored Procedure: sp_add_beyblade
-- Description: Adds a custom Beyblade configuration for a user.
-- 1. Checks if the custom Beyblade configuration already exists in the database based
-- on its parts.
-- 2. If it does not exist (custom), generates a unique ID using MD5() & UUID() functions, 
-- then inserts it into 'beyblades' table. (beyblade_ID attribute of stock Beyblades in
-- 'beyblades' table are already known VARCHAR types, but we want custom Beyblades in 'beyblades' 
-- table to have auto generated IDs (can be anything, just needs to be unique))
-- 3. Links the Beyblade (either custom or existing) with the user by inserting it into the
-- 'beycollection' table.
-- Parameters:
--    _user_id: The ID of the user.
--    _name: The name of the Beyblade.
--    _type: The Beyblade type (Attack, Defense, Stamina, Balance).
--    _series: The series the Beyblade belongs to (Metal Fusion, Metal Masters, Metal Fury).
--    _face_bolt_id, _energy_ring_id, _fusion_wheel_id, _spin_track_id, _performance_tip_id: 
--    The parts comprising the Beyblade.
--    _bey_condition: The condition the Beyblade is in (i.e., new, used).
DROP PROCEDURE IF EXISTS sp_add_beyblade;
DELIMITER !

CREATE PROCEDURE sp_add_beyblade(
    IN _user_id INT,
    IN _name VARCHAR(250),
    IN _type ENUM('Attack', 'Defense', 'Stamina', 'Balance'),
    IN _series ENUM('Metal Fusion', 'Metal Masters', 'Metal Fury'),
    IN _face_bolt_id VARCHAR(20),
    IN _energy_ring_id VARCHAR(20),
    IN _fusion_wheel_id VARCHAR(20),
    IN _spin_track_id VARCHAR(20),
    IN _performance_tip_id VARCHAR(20),
    IN _bey_condition VARCHAR(100)
)
BEGIN
    DECLARE _beyblade_id VARCHAR(10);
    DECLARE _is_custom BOOLEAN; -- If the beyblade is not in the database, 
    -- It is custom

    -- Check if the Beyblade already exists based on its parts
    SELECT beyblade_ID INTO _beyblade_id FROM beyblades
    WHERE face_bolt_ID = _face_bolt_id 
    AND energy_ring_ID = _energy_ring_id 
    AND fusion_wheel_ID = _fusion_wheel_id 
    AND spin_track_ID = _spin_track_id 
    AND performance_tip_ID = _performance_tip_id
    LIMIT 1;

    IF _beyblade_id IS NULL THEN
        SET _is_custom = TRUE;
        -- Generate a new beyblade_ID using MD5 and UUID, and take first 10 
        -- chars
        SET _beyblade_id = LEFT(MD5(UUID()), 10);

        -- Attempt to insert the new custom Beyblade with the generated ID
        INSERT INTO beyblades (beyblade_ID, name, type, is_custom, series, 
            face_bolt_ID, energy_ring_ID, fusion_wheel_ID, spin_track_ID, 
            performance_tip_ID)
        VALUES (_beyblade_id, _name, _type, _is_custom, _series, _face_bolt_id, 
            _energy_ring_id, _fusion_wheel_id, _spin_track_id, 
            _performance_tip_id);
    ELSE
        -- Match was found, so it's not a custom Beyblade
        SET _is_custom = FALSE;
    END IF;

    -- Link the Beyblade (new or existing) to the user
    INSERT INTO beycollection (user_ID, beyblade_ID, bey_condition)
    VALUES (_user_id, _beyblade_id, _bey_condition);
    -- Note that user_beyblade_ID attribute of 'beycollection' table is auto-
    -- incremented INT, so
    -- don't need to explicitly provide a value for this when inserting
END !

DELIMITER ;


-- Procedure: sp_record_battle
-- Description: This procedure adds a record for a new Beyblade battle to the 
--              'battles' table.
--              It encapsulates the logic required for inserting a battle, 
--              ensuring that all necessary information is recorded correctly 
--              and database integrity is maintained.
-- Parameters:
--    _tournament_name VARCHAR(250): The name of the tournament where the 
--    battle took place.
--    _date DATETIME: The date and time when the battle occurred.
--    _location VARCHAR(250): The location where the battle was held.
--    _player1_ID INT: The user ID of the first player in the battle.
--    _player2_ID INT: The user ID of the second player in the battle.
--    _player1_beyblade_ID INT: The ID of the beyblade used by the first player.
--    _player2_beyblade_ID INT: The ID of the beyblade used by the second player.
--    _winner_ID INT: The user ID of the winner of the battle. Can be NULL if 
--    the battle was a draw.
DROP PROCEDURE IF EXISTS sp_record_battle;
DELIMITER !

CREATE PROCEDURE sp_record_battle(
    IN _tournament_name VARCHAR(250), 
    IN _battle_date DATETIME, 
    IN _location VARCHAR(250), 
    IN _player1_ID INT, 
    IN _player2_ID INT, 
    IN _player1_beyblade_ID INT,
    IN _player2_beyblade_ID INT, 
    IN _winner_ID INT
)
BEGIN
    -- Insert battle details into 'battles' table
    INSERT INTO battles (tournament_name, battle_date, location, player1_ID, 
        player2_ID, player1_beyblade_ID, player2_beyblade_ID, winner_ID)
    VALUES (_tournament_name, _battle_date, _location, _player1_ID, _player2_ID, 
        _player1_beyblade_ID, _player2_beyblade_ID, _winner_ID);
END !

DELIMITER ;


-- Trigger: trg_update_date_joined
-- This trigger automatically updates date_joined in 'users' table
-- whenever a  new row is inserted into it. Notably, new rows are inserted
-- into this table in add_user function of app.py files, and they do not
-- require date_joined as this is automatically done with the trigger.
DROP TRIGGER IF EXISTS trg_update_date_joined;
DELIMITER !

CREATE TRIGGER trg_update_date_joined
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    SET NEW.date_joined = NOW();
END !

DELIMITER ;


-- User-defined Function: udf_heaviest_beyblade_for_type
-- Description: Defines a function to find the heaviest beyblade of a specified type.
-- It calculates the total weight of each beyblade by summing the weights of 
-- its constituent parts. The function returns the beyblade_id of the heaviest 
-- Beyblade of the specified type
-- Parameters:
--      beyblade_type: The battle type of Beyblade (Attack, Defense, Stamina, Balance)
DROP FUNCTION IF EXISTS udf_heaviest_beyblade_for_type;
DELIMITER !

CREATE FUNCTION udf_heaviest_beyblade_for_type(beyblade_type ENUM('Attack', 
    'Defense', 'Stamina', 'Balance'))
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
    DECLARE heaviest_beyblade_id VARCHAR(10);
    -- Finds heaviest Beyblade based on total weight of its parts
    SELECT b.beyblade_id INTO heaviest_beyblade_id
    FROM beyblades AS b
    JOIN parts AS fb ON b.face_bolt_id = fb.part_id
    JOIN parts AS er ON b.energy_ring_id = er.part_id
    JOIN parts AS fw ON b.fusion_wheel_id = fw.part_id
    JOIN parts AS st ON b.spin_track_id = st.part_id
    JOIN parts AS pt ON b.performance_tip_id = pt.part_id
    WHERE b.type = beyblade_type
    GROUP BY b.beyblade_id
    ORDER BY SUM(fb.weight + er.weight + fw.weight + st.weight + pt.weight) DESC
    LIMIT 1;

    RETURN heaviest_beyblade_id;
END !

DELIMITER ;
