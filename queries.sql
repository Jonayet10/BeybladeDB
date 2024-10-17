-- app_admin queries :

-- Query to fetch is_admin status for a user
SELECT is_admin
FROM users where username = 'gokus';

-- Authentication of username and password. 
SELECT authenticate('gokus', 'gokuspw');

-- Query to fetch user_ID based on username. 
SELECT user_ID 
FROM users where username = 'gokus';

-- Retrieves the IDs, usernames, emails, is_admin statuses, and date joined
-- of users. 
SELECT user_ID, username, email, is_admin, date_joined
FROM users;

-- Retrieves the user_beyblade_IDs, beyblade_IDs, names, and custom 
-- statuses of beyblades of a user. 
SELECT ub.user_beyblade_ID, b.beyblade_ID, b.name, b.is_custom, ub.bey_condition
FROM beyblades b
JOIN beycollection ub ON b.beyblade_ID = ub.beyblade_ID
JOIN users u ON ub.user_ID = u.user_ID
WHERE u.username = 'gokus';

-- Retrieves all beyblades for the user. 
SELECT * FROM beyblades;

-- Retrieves all battle results related to the current user from the 
-- battles table. 
SELECT b.battle_ID, b.tournament_name, b.battle_date, b.location, 
        u1.username AS Player1_Username, u2.username AS Player2_Username, 
        bb1.name AS Player1_Beyblade_Name, bb2.name AS Player2_Beyblade_Name, 
        b.player1_beyblade_ID, b.player2_beyblade_ID, b.winner_ID
FROM battles b
JOIN users u1 ON b.player1_ID = u1.user_ID
JOIN users u2 ON b.player2_ID = u2.user_ID
JOIN beycollection ub1 ON b.player1_beyblade_ID = ub1.user_beyblade_ID
JOIN beyblades bb1 ON ub1.beyblade_ID = bb1.beyblade_ID
JOIN beycollection ub2 ON b.player2_beyblade_ID = ub2.user_beyblade_ID
JOIN beyblades bb2 ON ub2.beyblade_ID = bb2.beyblade_ID
WHERE u1.username = 'gokus' OR u2.username = 'gokus';

-- Retrieves all battle results related to a specified tournament from the
-- battles table. 
SELECT b.battle_ID, b.battle_date, b.location, 
        u1.username AS Player1_Username, u2.username AS Player2_Username, 
        bb1.name AS Player1_Beyblade_Name, bb2.name AS Player2_Beyblade_Name, 
        b.player1_beyblade_ID, b.player2_beyblade_ID, b.winner_ID
FROM battles b
JOIN users u1 ON b.player1_ID = u1.user_ID
JOIN users u2 ON b.player2_ID = u2.user_ID
JOIN beycollection ub1 ON b.player1_beyblade_ID = ub1.user_beyblade_ID
JOIN beyblades bb1 ON ub1.beyblade_ID = bb1.beyblade_ID
JOIN beycollection ub2 ON b.player2_beyblade_ID = ub2.user_beyblade_ID
JOIN beyblades bb2 ON ub2.beyblade_ID = bb2.beyblade_ID
WHERE b.tournament_name = 'WBBA Prelim';

-- Retrieves all battle results related to a specified tournament from the
-- given location. 
SELECT b.battle_ID, b.tournament_name, b.battle_date, 
        u1.username AS Player1_Username, u2.username AS Player2_Username, 
        bb1.name AS Player1_Beyblade_Name, bb2.name AS Player2_Beyblade_Name, 
        b.player1_beyblade_ID, b.player2_beyblade_ID, b.winner_ID
FROM battles b
JOIN users u1 ON b.player1_ID = u1.user_ID
JOIN users u2 ON b.player2_ID = u2.user_ID
JOIN beycollection ub1 ON b.player1_beyblade_ID = ub1.user_beyblade_ID
JOIN beyblades bb1 ON ub1.beyblade_ID = bb1.beyblade_ID
JOIN beycollection ub2 ON b.player2_beyblade_ID = ub2.user_beyblade_ID
JOIN beyblades bb2 ON ub2.beyblade_ID = bb2.beyblade_ID
WHERE b.location = 'NYC';

-- Retrives the information for a specific part given a part_id. 
SELECT part_ID, part_type, weight, description
FROM parts
WHERE part_ID = 'Byxis FB';

-- Retrieves the names and weights of all parts that make up a specific 
-- Beyblade.
SELECT p.part_ID, p.part_type, p.weight, p.description
FROM parts p
JOIN beyblades b ON p.part_ID IN (b.face_bolt_ID, b.energy_ring_ID, 
                                  b.fusion_wheel_ID, b.spin_track_ID, 
                                  b.performance_tip_ID)
WHERE b.beyblade_ID = 'BB-70';

-- Gets the ID of the heaviest Beyblade of a specific type. 
SELECT udf_heaviest_beyblade_for_type('Stamina') 
    AS heaviest_beyblade_id;

-- Gets the name of a Beyblade for a specified Beyblade ID.
SELECT name 
FROM beyblades 
WHERE beyblade_id = 'BB-70';

-- Selects all parts of Beyblades.
SELECT part_ID, part_type, weight, description 
FROM parts 
ORDER BY part_type, part_ID;

-- Select all tournament names.
SELECT DISTINCT tournament_name 
FROM battles 
ORDER BY tournament_name;

-- Select all locations of battles.
SELECT DISTINCT location 
FROM battles 
ORDER BY location;

-- Select and order all beyblades based off battle wins. 
SELECT bb.beyblade_ID, bb.name, bb.type, COUNT(b.battle_ID) as wins
FROM battles b
INNER JOIN beycollection ub ON b.winner_ID = ub.user_beyblade_ID
INNER JOIN beyblades bb ON ub.beyblade_ID = bb.beyblade_ID
GROUP BY bb.beyblade_ID, bb.name, bb.type
ORDER BY wins DESC, bb.name;

-- RA SPECIFIC QUERY - though this is used in app-admin:
-- Inserts a new part into the parts table. 
INSERT INTO parts (part_ID, part_type, weight, description) 
    VALUES ('BD145', 'Spin Track', 8, 'This particular spin track is designed 
    for stamina Type Beyblades, enhancing their endurance in battles'); 

-- setup queries:
-- Used to select a beyblade based off which parts it has that we specify. 
-- SHOULD RETURN EMPTY SET.
SELECT beyblade_ID FROM beyblades
WHERE face_bolt_ID = 'Leone I FB' 
AND energy_ring_ID = 'Virgo' 
AND fusion_wheel_ID = 'Twisted' 
AND spin_track_ID = 'W105' 
AND performance_tip_ID = 'WB' 
LIMIT 1;

-- This selects the heaviest beyblade out of all beyblades for a certain
-- specified beyblade type. 
SELECT b.beyblade_id 
FROM beyblades AS b
JOIN parts AS fb ON b.face_bolt_id = fb.part_id
JOIN parts AS er ON b.energy_ring_id = er.part_id
JOIN parts AS fw ON b.fusion_wheel_id = fw.part_id
JOIN parts AS st ON b.spin_track_id = st.part_id
JOIN parts AS pt ON b.performance_tip_id = pt.part_id
WHERE b.type = 'Stamina' 
GROUP BY b.beyblade_id
ORDER BY SUM(fb.weight + er.weight + fw.weight + st.weight + pt.weight) DESC
LIMIT 1;
