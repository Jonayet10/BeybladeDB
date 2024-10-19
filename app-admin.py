"""
This script provides a command-line interface (CLI) for a BeyAdmin for managing a Beyblade 
database system. It comprises functionalities for adding entities (Beyblade part, user, etc.)
to the database and viewing specific information regarding Beyblades, tournaments, and users.
The script connects to a MySQL database ('beybladedb') to perform various SQL queries and 
stored procedure calls.

Make sure to configure the MySQL connection details and run the necessary SQL scripts to set up
the database schema before using this script (instructions in README).
"""

import sys  # To print error messages to sys.stderr
import mysql.connector
# To get error codes from the connector, useful for user-friendly
# error-handling
import mysql.connector.errorcode as errorcode
from tabulate import tabulate

# For output coloring
import colorama
from colorama import Fore

# To validate date format
from datetime import datetime

colorama.init(autoreset=True)

# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client. ***Set to False when done testing.***
DEBUG = True

# ----------------------------------------------------------------------
# SQL Utility Functions
# ----------------------------------------------------------------------


def get_conn():
    """"
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='jlavin',
            # Find port in MAMP or MySQL Workbench GUI or with
            # SHOW VARIABLES WHERE variable_name LIKE 'port';
            port='3306',  # this may change!
            password='jlavinpw',
            database='beybladedb',  # replace this with your database name
        )
        print('Successfully connected.')
        return conn
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in
        # simulated program. Their user information would be in a users table
        # specific to your database; hence the DEBUG use.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr.write(
                'Incorrect username or password when connecting to DB.' + '\n')
            sys.stderr.flush()
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr.write('Database does not exist.' + '\n')
            sys.stderr.flush()
        elif DEBUG:
            sys.stderr.write(str(err) + '\n')
            sys.stderr.flush()

        else:
            # A fine catchall client-facing message.
            sys.stderr('An error occurred, please contact the administrator.')
        sys.exit(1)

# ----------------------------------------------------------------------
# Functions for Command-Line Options/Query Execution
# ----------------------------------------------------------------------


def add_beyblade(beyblade_ID, name, type, is_custom, series, face_bolt_ID,
                 energy_ring_ID, fusion_wheel_ID, spin_track_ID,
                 performance_tip_ID):
    """
    Adds the beyblade to the beyblades and beycollection table.

    Arguments:
        name (str): The name of the Beyblade.
        type (str): The type category of the Beyblade
            (e.g., Attack, Defense, Stamina, Balance).
        series (str): The series the Beyblade belongs to.
        is_custom (bool): Indicates whether the Beyblade is custom.
        face_bolt_id (int): The ID of the face bolt.
        energy_ring_id (int): The ID of the energy ring.
        fusion_wheel_id (int): The ID of the fusion wheel.
        spin_track_id (int): The ID of the spin track.
        performance_tip_id (int): The ID of the performance tip.

    Return value: none.
    """
    cursor = conn.cursor()

    # Validate Beyblade type
    valid_types = ['Attack', 'Defense', 'Stamina', 'Balance']
    if type not in valid_types:
        print(Fore.RED + f"\nError: Invalid Beyblade type '{type}'. "
            f"Please enter one of {valid_types}."
        )

    # Validate Beyblade series
    valid_series = ['Metal Fusion', 'Metal Masters', 'Metal Fury']
    if series not in valid_series:
        print(Fore.RED + f"\nError: Invalid Beyblade series '{series}'. "
              f"Please enter one of {valid_series}.")
        return
    
    # Validate that parts exist in the 'parts' table
    part_ids = [face_bolt_ID, energy_ring_ID, fusion_wheel_ID, spin_track_ID, performance_tip_ID]
    for part_id in part_ids:
        cursor.execute("SELECT COUNT(*) FROM parts WHERE part_ID = %s", (part_id,))
        if cursor.fetchone()[0] == 0:
            print(Fore.RED + f"\nError: Part ID '{part_id}' does not exist in the parts table.")
            return
            
    # SQL INSERT statement with accurate column names
    sql = (
        "INSERT INTO beyblades (beyblade_ID, name, type, is_custom, series, "
        "face_bolt_ID, energy_ring_ID, fusion_wheel_ID, spin_track_ID, "
        "performance_tip_ID) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    # The data tuple matches the corrected SQL statement
    data = (
        beyblade_ID,
        name,
        type,
        is_custom,
        series,
        face_bolt_ID,
        energy_ring_ID,
        fusion_wheel_ID,
        spin_track_ID,
        performance_tip_ID)
    try:
        cursor.execute(sql, data)
        conn.commit()
        print(Fore.BLUE + f"\nAdded new Beyblade: {name}")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")


def add_battle(tournament_name, battle_date, location, player1_id, player2_id,
               player1_beyblade_id, player2_beyblade_id, winner_id):
    """
    Records a new battle result in the database.

    Arguments:
        tournament_name (str): Name of the tournament.
        battle_date (str or datetime): Date when the battle occurred.
        location (str): Location of the battle.
        player1_id (int): User ID of the first player.
        player2_id (int): User ID of the second player.
        player1_beyblade_id (int): ID of the Beyblade used by the 1st player.
        player2_beyblade_id (int): ID of the Beyblade used by the 2nd player.
        winner_id (int): User ID of the winner.

    Return value: None.
    """
    cursor = conn.cursor()

    # Validate the date format
    try:
        if len(battle_date.strip()) == 10:  # If only date is provided (YYYY-MM-DD)
            battle_date += " 00:00:00"  # Add default time
        datetime.strptime(battle_date, "%Y-%m-%d %H:%M:%S")  # Validate date format
    except ValueError:
        print(Fore.RED + 
              f"\nInvalid date format '{battle_date}'. Please use 'YYYY-MM-DD' "
              "or 'YYYY-MM-DD HH:MM:SS'.")
        return

    # Validate player IDs and Beyblade IDs to ensure they are integers
    try:
        player1_id = int(player1_id)
        player2_id = int(player2_id)
        player1_beyblade_id = int(player1_beyblade_id)
        player2_beyblade_id = int(player2_beyblade_id)
        if winner_id:  # Only convert winner_id if it is provided
            winner_id = int(winner_id)
    except ValueError:
        print(Fore.RED + "\nInvalid input. Player IDs, Beyblade IDs, and Winner ID "
              "must be integers.")
        return
    
    # Check if player1_id exists in the 'users' table
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_ID = %s", (player1_id,))
    player1_exists = cursor.fetchone()[0]

    # Check if player2_id exists in the 'users' table
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_ID = %s", (player2_id,))
    player2_exists = cursor.fetchone()[0]

    if not player1_exists or not player2_exists:
        missing_players = []
        if not player1_exists:
            missing_players.append(f"Player 1 (ID: {player1_id})")
        if not player2_exists:
            missing_players.append(f"Player 2 (ID: {player2_id})")
        
        print(Fore.RED + f"\nError: The following players are not found in the database: "
              + ", ".join(missing_players))
        return
    
    try:
        cursor.callproc('sp_record_battle', (tournament_name, battle_date, location,
                                             player1_id, player2_id,
                                             player1_beyblade_id,
                                             player2_beyblade_id, winner_id))
        conn.commit()
        print(Fore.BLUE + "\nNew battle result added successfully.")
    except mysql.connector.Error as err:
        # Check for the foreign key error
        if err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            # Foreign key constraint failed
            print(Fore.RED + f"\nError: Player {player1_id} or {player2_id} "
                  "does not have the specified Beyblade in their collection.")
        else:
            # Handle other errors
            print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()


def view_users():
    """
    Retrieves and displays a list of all users and their information.
    """
    cursor = conn.cursor()
    sql = "SELECT user_ID, username, email, is_admin, date_joined FROM users;"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        if results:
            print(Fore.BLUE + "\nCurrent Users:")
            print(
                f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10} "
                f"{'Date Joined'}")
            for row in results:
                user_id, username, email, is_admin, date_joined = row
                admin_status = "Yes" if is_admin else "No"
                print(
                    f"{user_id:<5} {username:<20} {email:<30} "
                    f"{admin_status:<10} {date_joined}")
        else:
            print(Fore.RED + "\nNo users found.")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()


def view_user_beyblades(user_name):
    """
    Queries the database for all Beyblades owned by a specific user and prints
    their beyblade_ID, name, custom status, and Beyblade-Player ID, along with 
    the condition of each Beyblade in a well-formatted table.

    Arguments:
        user_name (str) - The username of the user.
    Returns: Prints the Beyblade ID, Name, Custom Status, Beyblade-Player 
             ID, and Condition of the user's Beyblades
    """
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    SELECT ub.user_beyblade_ID, b.beyblade_ID, b.name, b.is_custom, 
    ub.bey_condition
    FROM beyblades b
    JOIN beycollection ub ON b.beyblade_ID = ub.beyblade_ID
    JOIN users u ON ub.user_ID = u.user_ID
    WHERE u.username = %s;
    """
    cursor.execute(query, (user_name,))

    results = cursor.fetchall()
    headers = ["Beyblade-Player ID", "Beyblade ID", "Name", "Is Custom", 
               "Condition"]

    if results:
        formatted_results = [
            (user_beyblade_id, id, name, "Yes" if is_custom else "No", 
             condition) for user_beyblade_id, id, name, is_custom, 
             condition in results]
        print(tabulate(formatted_results, headers=headers, tablefmt="grid"))
    else:
        print(Fore.RED + f"\nNo Beyblades found for user: {user_name}")

    cursor.close()
    conn.close()


def add_beyblade_part(part_ID, part_type, weight, description):
    """
    Adds a new Beyblade part to the database.

    Arguments:
        part_ID (int): The unique identifier for the Beyblade part.
        part_type (str): The type of the Beyblade part
            (e.g., Face Bolt, Energy Ring, Fusion Wheel).
        weight (float): The weight of the part in grams.
        description (str): A brief description of the part.

    Return value: None.
    """
    cursor = conn.cursor()

    # Validate part type input
    valid_part_types = ['Face Bolt', 'Energy Ring', 'Fusion Wheel', 'Spin Track', 'Performance Tip']
    
    if part_type not in valid_part_types:
        print(Fore.RED + f"\nError: Invalid part type '{part_type}'. "
              f"Please enter one of the following: {', '.join(valid_part_types)}")
        return  # Exit the function if the part type is invalid
    
    # Validate the weight input
    try:
        weight = float(weight)
    except ValueError:
        print(Fore.RED + "\nInvalid weight. Please enter a numeric value.")
        return  # Exit the function if the weight is invalid
        
    # SQL INSERT statement for the parts table
    sql = ("INSERT INTO parts (part_ID, part_type, weight, description) "
           "VALUES (%s, %s, %s, %s)")
    # Data tuple for the values to insert
    data = (part_ID, part_type, weight, description)

    try:
        cursor.execute(sql, data)
        conn.commit()  # Commit the transaction to save the changes
        print(Fore.BLUE + f"\nAdded new part: {part_ID} successfully")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()

# ------------ Functions that also the client has ----------------


def view_all_beyblades():
    """
    Queries the beyblades table for
    the entirety of all beyblades for the user to look through.

    Return value: Query of the beyblades table.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beyblades;")

    # Fetching all results
    results = cursor.fetchall()

    # Defining the table headers as per beyblades table columns
    headers = ['Beyblade ID', 'Name', 'Type', 'Is Custom', 'Series',
               'Face Bolt ID', 'Energy Ring ID', 'Fusion Wheel ID',
               'Spin Track ID', 'Performance Tip ID']

    # Printing the results in a table format
    print(tabulate(results, headers=headers, tablefmt="grid"))

    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_all_battle_results_for_user(user_name):
    """
    Queries the battles table for all battle results related to the
    current user.

    Arguments:
        user_name (str) - the name of the user.

    Return value: Query of the battles table.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to fetch battle results for the given user
    query = """
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
    WHERE u1.username = %s OR u2.username = %s;
    """
    cursor.execute(query, (user_name, user_name))

    headers = ["Battle ID", "Tournament Name", "Date", "Location",
                   "Player 1 Username", "Player 2 Username",
                   "Player 1 Beyblade Name", "Player 2 Beyblade Name",
                   "Player 1 Beyblade ID", "Player 2 BeyBlade ID", "Winner ID"]
    
    # Fetching all results
    results = cursor.fetchall()
    if not results:
        print(Fore.RED + "\nNo battles found for user!")
    else:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_battle_results_for_tournament(tournament_name):
    """
    Queries the battles table for all battle results related to the specified 
    tournament.

    Arguments:
        tournament_name (str) - the name of the tournament.

    Return value: None. Prints the query result of the battles table in a 
                  formatted table.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to fetch battle results for the given tournament name
    query = """
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
    WHERE b.tournament_name = %s;
    """
    cursor.execute(query, (tournament_name,))

    # Fetching all results
    results = cursor.fetchall()
    headers = ["Battle ID", "Date", "Location",
               "Player 1 Username", "Player 2 Username",
               "Player 1 Beyblade Name", "Player 2 Beyblade Name",
               "Player 1 Beyblade ID", "Player 2 BeyBlade ID", "Winner ID"]

    # Check if there are any results
    if results:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print(Fore.RED + f"\nNo battles found for tournament: {tournament_name}")

    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_battle_results_for_location(location):
    """
    Queries the battles table for all battle results related to the specified 
    location.

    Arguments:
        location (str) - the specified location of the battles to query.

    Return value: None. Prints the query result of the battles table in a 
                  formatted table.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to fetch battle results for the given location
    query = """
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
    WHERE b.location = %s;
    """
    cursor.execute(query, (location,))

    # Fetching all results
    results = cursor.fetchall()
    headers = ["Battle ID", "Tournament Name", "Date",
               "Player 1 Username", "Player 2 Username",
               "Player 1 Beyblade Name", "Player 2 Beyblade Name",
               "Player 1 Beyblade ID", "Player 2 BeyBlade ID", "Winner ID"]

    # Check if there are any results
    if results:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print(Fore.RED + f"\nNo battles found for location: {location}")

    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_part_info(part_id):
    """
    Queries the parts table for information about a specific part given its 
    part_ID.

    Arguments:
        part_id (str) - the unique identifier for the part to query.

    Return value: None. Prints the query result of the part in a formatted 
                  table.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to fetch information for the given part_ID
    query = """
    SELECT part_ID, part_type, weight, description
    FROM parts
    WHERE part_ID = %s;
    """
    cursor.execute(query, (part_id,))

    # Fetching the result
    result = cursor.fetchone()

    headers = ["Part ID", "Part Type", "Weight", "Description"]

    # Check if there is a result
    if result:
        print(tabulate([result], headers=headers, tablefmt="grid"))
    else:
        print(Fore.RED + f"\nNo information found for part ID: {part_id}")

    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_beyblade_parts(beyblade_id):
    """
    Queries the database for the names and weights of all parts that make up
    a specific Beyblade and prints them in a well-formatted table.

    Arguments:
        beyblade_id (str) - The ID of the Beyblade.
    Returns: Prints the PART ID, Part Type, Part Description, and Weight.
    """
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    SELECT p.part_ID, p.part_type, p.weight, p.description
    FROM parts p
    JOIN beyblades b ON p.part_ID IN (b.face_bolt_ID, b.energy_ring_ID,
                                      b.fusion_wheel_ID, b.spin_track_ID,
                                      b.performance_tip_ID)
    WHERE b.beyblade_ID = %s;
    """
    cursor.execute(query, (beyblade_id,))

    results = cursor.fetchall()
    headers = ["Part ID", "Part Type", "Weight (g)", "Description"]

    if results:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print(Fore.RED + f"\nNo parts found for Beyblade ID: {beyblade_id}")

    cursor.close()
    conn.close()


def add_user_beyblade(
        username,
        name,
        type,
        series,
        face_bolt_id,
        energy_ring_id,
        fusion_wheel_id,
        spin_track_id,
        performance_tip_id,
        bey_condition):
    """
    Adds the beyblade to the beyblades and beycollection table.

    Arguments:
        username (str): Username of the user adding the Beyblade.
        name (str): Name of the Beyblade.
        type (str): Type of the Beyblade
            (Attack, Defense, Stamina, Balance).
        series (str): Series the Beyblade belongs to
            (Metal Fusion, Metal Masters, Metal Fury).
        face_bolt_id (str): ID of the Face Bolt part.
        energy_ring_id (str): ID of the Energy Ring part.
        fusion_wheel_id (str): ID of the Fusion Wheel part.
        spin_track_id (str): ID of the Spin Track part.
        performance_tip_id (str): ID of the Performance Tip part.
        bey_condition (str): Condition of the Beyblade being added.

    Return value: none.
    """
    cursor = conn.cursor()

    # Validate Beyblade type
    valid_types = ['Attack', 'Defense', 'Stamina', 'Balance']
    if type not in valid_types:
        print(Fore.RED + f"\nError: Invalid Beyblade type '{type}'. "
            f"Please enter one of {valid_types}."
        )

    # Validate Beyblade series
    valid_series = ['Metal Fusion', 'Metal Masters', 'Metal Fury']
    if series not in valid_series:
        print(Fore.RED + f"\nError: Invalid Beyblade series '{series}'. "
              f"Please enter one of {valid_series}.")
        return

    # Validate that parts exist in the 'parts' table
    part_ids = [face_bolt_id, energy_ring_id, fusion_wheel_id, spin_track_id, performance_tip_id]
    for part_id in part_ids:
        cursor.execute("SELECT COUNT(*) FROM parts WHERE part_ID = %s", (part_id,))
        if cursor.fetchone()[0] == 0:
            print(Fore.RED + f"\nError: Part ID '{part_id}' does not exist in the parts table.")
            return

    # SQL query to fetch user_id based on username
    sql_get_user_id = "SELECT user_ID FROM users WHERE username = %s;"
    try:
        cursor.execute(sql_get_user_id, (username,))
        user_id_row = cursor.fetchone()
        if user_id_row is not None:
            user_id = user_id_row[0]
        else:
            print(Fore.RED + f"\nError: User '{username}' not found")
            return
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError fetching user ID: {err}")
        return

    # Now, call the stored procedure with the obtained user_id
    sql_call_sp = "CALL sp_add_beyblade(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data = (user_id, name, type, series, face_bolt_id, energy_ring_id,
            fusion_wheel_id, spin_track_id, performance_tip_id, bey_condition)
    try:
        cursor.execute(sql_call_sp, data)
        conn.commit()
        print(Fore.BLUE + f"\nAdded new Beyblade: {name} for user {username}")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError adding Beyblade: {err}")
    finally:
        cursor.close()


def heaviest_beyblade_for_type(beyblade_type):
    """
    Fetches and displays the ID and name of the heaviest Beyblade of a specific
    type.
    Arguments:
        beyblade_type (str): The type of Beyblade
        (Attack, Defense, Stamina, Balance).
    """
    conn = get_conn()
    cursor = conn.cursor()

    # Call the UDF `udf_heaviest_beyblade_for_type` passing the beyblade type
    query = (f"SELECT udf_heaviest_beyblade_for_type('{beyblade_type}') AS "
             "heaviest_beyblade_id;")
    cursor.execute(query)

    # Fetching the result which is the ID of the heaviest beyblade
    result = cursor.fetchone()
    if result and result[0]:
        beyblade_id = result[0]
        # Fetch beyblade name using the ID
        cursor.execute(
            "SELECT name FROM beyblades WHERE beyblade_id = %s;", 
            (beyblade_id,))
        name_result = cursor.fetchone()
        if name_result and name_result[0]:
            print(Fore.BLUE + f"\nThe heaviest Beyblade of type '{beyblade_type}' is "
                f"ID: {beyblade_id}, Name: {name_result[0]}")
        else:
            print(Fore.RED + f"\nNo Beyblade found with ID: {beyblade_id}")
    else:
        print(Fore.RED + f"\nNo heaviest Beyblade found for type '{beyblade_type}'")

    cursor.close()
    conn.close()


def view_all_beyblade_parts():
    """
    Retrieves and displays all Beyblade parts from the database, sorted
    by part type and part ID.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to select all parts
    sql = ("SELECT part_ID, part_type, weight, description FROM parts "
          "ORDER BY part_type, part_ID;")

    try:
        cursor.execute(sql)
        parts = cursor.fetchall()  # Fetch all results

        if parts:
            # Printing the results in a table format
            print(Fore.BLUE + "\nBeyblade Parts List:")
            print(
                tabulate(
                    parts,
                    headers=[
                        'Part ID',
                        'Part Type',
                        'Weight (g)',
                        'Description'],
                    tablefmt="grid"))
        else:
            print(Fore.RED + "\nNo parts found in the database")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()
        conn.close()


def view_all_tournament_names():
    """
    Retrieves and prints unique tournament names from the 'battles' table.
    If no tournaments exist, indicates no tournaments found.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to select distinct tournament names
    sql = ("SELECT DISTINCT tournament_name FROM battles " 
           "ORDER BY tournament_name;")

    try:
        cursor.execute(sql)
        tournaments = cursor.fetchall()  # Fetch all results

        if tournaments:
            print(Fore.BLUE + "\nList of Tournament Names:")
            for tournament in tournaments:
                print(Fore.BLUE + tournament[0])  # Print each tournament name
        else:
            print(Fore.RED + "\nNo tournaments found in the database")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()
        conn.close()


def view_all_battle_locations():
    """
    Fetches and displays unique battle locations from the 'battles' table.
    """
    conn = get_conn()  # Way to get database connection
    cursor = conn.cursor()

    # SQL query to select distinct battle locations
    sql = "SELECT DISTINCT location FROM battles ORDER BY location;"

    try:
        cursor.execute(sql)
        locations = cursor.fetchall()  # Fetch all results

        if locations:
            print(Fore.BLUE + "\nList of Battle Locations:")
            for location in locations:
                print(Fore.BLUE + location[0])  # Print each location
        else:
            print(Fore.RED + "\nNo battle locations found in the database")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()
        conn.close()  # Closing the connection when done


def beyblade_leaderboard():
    """
    Prints a leaderboard of Beyblades based on their wins in battles.
    """
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    SELECT bb.beyblade_ID, bb.name, bb.type, COUNT(*) as wins
    FROM battles b
    INNER JOIN beycollection ub ON b.winner_ID = ub.user_beyblade_ID
    INNER JOIN beyblades bb ON ub.beyblade_ID = bb.beyblade_ID
    GROUP BY bb.beyblade_ID, bb.name, bb.type
    ORDER BY wins DESC, bb.name;
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print(Fore.BLUE + "\nBeyblade Leaderboard (Most Wins):")
            headers = ['Beyblade ID', 'Name', 'Type', 'Wins']
            print(tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print(Fore.RED + "\nNo battle results found")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------------------------
# Functions for Logging Users In
# ----------------------------------------------------------------------
# Note: There's a distinction between database users (admin and client)
# and application users (e.g. members registered to a store). You can
# choose how to implement these depending on whether you have app.py or
# app-client.py vs. app-admin.py (in which case you don't need to
# support any prompt functionality to conditionally login to the sql database)

def is_admin_func(username):
    """
    Helper function to verify whether the user logging in is a BeyAdmin.
    Checks the `is_admin` flag for the given username in the `users` table.
    """
    cursor = conn.cursor()
    sql = "SELECT is_admin FROM users WHERE username = %s;"
    try:
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        # If the user exists and the is_admin flag is True, return True
        if result and result[0]:
            return True
        else:
            return False
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nDatabase error: {err}")
        return False
    finally:
        cursor.close()


def login():
    """
    This function prompts the login for an admin.
    It checks the database to ensure that the username and password are correct.
    """
    cursor = conn.cursor()

    print("\n------------------------------ BeyAdmin Login -----------"
          "-------------------\n")

    while True:
        username = input("USERNAME: ").lower()
        password = input("PASSWORD: ").lower()

        while not is_admin_func(username):
            print("\nIt appears that you are not a BeyAdmin. "
                  "Please try again! \n")
            username = input("USERNAME: ").lower()
            password = input("PASSWORD: ").lower()

        sql = "SELECT authenticate('%s', '%s');" % (username, password)

        try:
            cursor.execute(sql)
            check_response = cursor.fetchone()

            if check_response[0] == 1:
                show_options(username)
            else:
                print("\nUsername or password is incorrect. "
                      "Please try again :)\n")

        except mysql.connector.Error as err:
            if DEBUG:
                sys.stderr(err)
                sys.exit(1)
            else:
                sys.stderr("\nError logging in.")


def add_user(username, email, password, is_admin):
    """
    Adds the user to the users and user_info table.

    Arguments:
        username (str) - The username of the new user.
        email (str) - The email address of the new user.
        password (str) - The password for the new user.
        is_client (bool) - Boolean indicating whether new user is admin or not.

    Return value: none.
    """
    cursor = conn.cursor()
    # Call the stored procedure to add user to user_info table
    sql_user_info = "CALL sp_add_user(%s, %s, %s)"
    # Add user to users table
    sql_users = ("INSERT INTO users (username, email, is_admin) " 
                 "VALUES (%s, %s, %s)")
    try:
        # Add user to user_info table
        cursor.execute(sql_user_info, (username, password, is_admin))
        # Add user to users table
        cursor.execute(sql_users, (username, email, is_admin))
        conn.commit()
        print(Fore.GREEN + f"\nUser '{username}' added successfully")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")

# ----------------------------------------------------------------------
# Command-Line Functionality
# ----------------------------------------------------------------------


def show_options(username):
    """
    Displays options users can choose in the application, such as
    viewing <x>, filtering results with a flag (e.g. -s to sort),
    sending a request to do <x>, etc.
    """
    print('\n')
    print('What would you like to do?')
    print('\n')

    print('* Add Entities: ')
    print('  (a) Add a part to the database')  
    print('  (b) Add a new Beyblade to the database')  
    print('  (c) Add a Beyblade to your collection')
    print('  (d) Add a new battle result')  
    print('  (e) Add a new user')   
    print('\n')

    print('* View Beyblade Information: ')

    print('  (f) View all Beyblades')   
    print('  (g) View Beyblades from a user\'s collection')  
    print('  (h) View all parts in the database')  
    print('  (i) View parts of a Beyblade')  
    print('  (j) View part information')    
    print('  (k) View the heaviest Beyblade for a type')    
    print('\n')

    print('* View Battle Information: ')

    print('  (l) View all tournament names')    
    print('  (m) View battle results for a tournament')  
    print('  (n) View all battle locations')    
    print('  (o) View battle results for a location')   
    print('  (p) View current users')   
    print('  (r) View battle results for a user')   
    print('  (s) View the leaderboard')  
    print('\n')

    print('  (q) - quit')
    ans = input('Enter an option: ').lower()

    if ans == 'q':
        quit_ui()
    elif ans == 'a':
        # Add a record to parts table
        part_ID = input('Enter Part ID: ')
        part_type = input(
            'Enter Part Type (Face Bolt, Energy Ring, Fusion Wheel, '
            'Spin Track, Performance Tip): ')
        weight = input('Enter Weight (in grams): ')
        description = input('Enter Decription: ')
        try:
            weight = float(weight)
        except ValueError:
            print("\nInvalid weight. Please enter a numeric value.")
            show_options(username)
            return
        add_beyblade_part(part_ID, part_type, weight, description)
        show_options(username)
    elif ans == 'b':
        # Adds full Beyblade to database
        # Just the parts need to be in the database for the Beyblade being
        # added
        beyblade_ID = input('Enter Beyblade ID: ')
        name = input('Enter Beyblade name: ')
        type = input(
            'Enter Beyblade type (Attack, Defense, Stamina, Balance): ')
        is_custom = (input(
            'Is it custom? (True/False): ').lower() 
            in ['true', '1', 't', 'y', 'yes'])
        series = input(
            'Enter Beyblade series (Metal Fusion, Metal Masters, Metal Fury): ')
        face_bolt_id = input('Enter Face Bolt ID: ')
        energy_ring_id = input('Enter Energy Ring ID: ')
        fusion_wheel_id = input('Enter Fusion Wheel ID: ')
        spin_track_id = input('Enter Spin Track ID: ')
        performance_tip_id = input('Enter Performance Tip ID: ')
        add_beyblade(
            beyblade_ID,
            name,
            type,
            is_custom,
            series,
            face_bolt_id,
            energy_ring_id,
            fusion_wheel_id,
            spin_track_id,
            performance_tip_id)
        show_options(username)
    elif ans == 'c':
        # Adds a Beyblade to the account that is logged in right now
        name = input('Enter Beyblade name: ')
        type = input(
            'Enter Beyblade type (Attack, Defense, Stamina, Balance): ')
        series = input(
            'Enter Beyblade series (Metal Fusion, Metal Masters, Metal Fury): ')
        face_bolt_id = input('Enter Face Bolt ID: ')
        energy_ring_id = input('Enter Energy Ring ID: ')
        fusion_wheel_id = input('Enter Fusion Wheel ID: ')
        spin_track_id = input('Enter Spin Track ID: ')
        performance_tip_id = input('Enter Performance Tip ID: ')
        bey_condition = input('Enter Condition of Your Beyblade (i.e. Like New): ')
        add_user_beyblade(
            username,
            name,
            type,
            series,
            face_bolt_id,
            energy_ring_id,
            fusion_wheel_id,
            spin_track_id,
            performance_tip_id,
            bey_condition)
        show_options(username)
    elif ans == 'd':
        # Adds a new record to battles table
        tournament_name = input('Enter tournament name: ')
        battle_date = input('Enter date of the battle (YYYY-MM-DD HH:MM:SS): ')
        location = input('Enter location: ')
        player1_id = input('Enter Player 1 ID: ')
        player2_id = input('Enter Player 2 ID: ')
        player1_beyblade_id = input('Enter Beyblade-Player ID: ')
        player2_beyblade_id = input('Enter Beyblade-Player ID: ')
        winner_id = input('Enter Winner ID (leave blank if draw): ')
        winner_id = winner_id if winner_id.strip() != '' else None
        add_battle(
            tournament_name,
            battle_date,
            location,
            player1_id,
            player2_id,
            player1_beyblade_id,
            player2_beyblade_id,
            winner_id)
        show_options(username)
    elif ans == 'e':
        # Add a new record to users table, also adds to user_info table 
        # for password authentication
        # It works to then log in with this new user and pass with app-admin
        # (if admin) or app-client (if client)
        username = input('Enter username: ')
        email = input('Enter email: ')
        password = input('Enter password: ')
        is_admin = (input(
            'Is the user an admin? (True/False): ').lower() 
            in ['true', '1', 't', 'y', 'yes'])
        add_user(username, email, password, is_admin)
        show_options(username)
    elif ans == 'f':
        # View beyblades table
        view_all_beyblades()
        show_options(username)
    elif ans == 'g':
        # View beycollection given username
        user_name = input('Enter username: ')
        view_user_beyblades(user_name)
        show_options(username)
    elif ans == 'h':
        # Shows all records in parts table
        view_all_beyblade_parts()
        show_options(username)
    elif ans == 'i':
        # View part records of individual parts in Beyblade
        beyblade_ID = input('Enter Beyblade ID: ')
        view_beyblade_parts(beyblade_ID)
        show_options(username)
    elif ans == 'j':
        # View part type, weight (g), and description of a part
        part_ID = input('Enter part ID: ')
        view_part_info(part_ID)
        show_options(username)
    elif ans == 'k':
        # Return the Beyblade ID of the heaviest Beyblade for a certain type
        # Validation for Beyblade entered type
        valid_types = ['Attack', 'Defense', 'Stamina', 'Balance']
        while True:
            beyblade_type = input(
                'Enter Beyblade type (Attack, Defense, Stamina, Balance): ').capitalize()
            if beyblade_type in valid_types:
                heaviest_beyblade_for_type(beyblade_type)
                break
            else:
                print(Fore.RED + f"\nError: Invalid Beyblade type. "
                    f"Please enter one of {valid_types}.")
        show_options(username)
    elif ans == 'l':
        # Prints list of distinct tournament names present in battles table
        view_all_tournament_names()
        show_options(username)
    elif ans == 'm':
        tournament_name = input('Enter tournament name: ')
        view_battle_results_for_tournament(tournament_name)
        show_options(username)
    elif ans == 'n':
        # Prints list of distinct battle locations present in battles table
        view_all_battle_locations()
        show_options(username)
    elif ans == 'o':
        tournament_location = input('Enter tournament location: ')
        view_battle_results_for_location(tournament_location)
        show_options(username)
    elif ans == 'p':
        # View the users table
        view_users()
        show_options(username)
    elif ans == 'r':
        # View a user's battle results, names, IDs, winners
        username = input('Enter username: ')
        view_all_battle_results_for_user(username)
        show_options(username)
    elif ans == 's':
        # Prints a leaderboard of the Beyblades that won the most
        beyblade_leaderboard()
        show_options(username)


def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    print('\n----------------------------------------------'
          '------------------\n')
    print('Thank you for managing our community of Bladers. '
          'Goodbye, and keep spinning forward!')
    print('\n-----------------------------------------------'
          '-----------------\n')
    exit()


def main():
    """
    Main function for starting things up.
    """
    login()


if __name__ == '__main__':
    # This conn is a global object that other functions can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()
