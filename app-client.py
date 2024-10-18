"""
This script provides a command-line interface (CLI) for a Blader for managing a Beyblade 
database system. It comprises functionalities for creating an account, adding Beyblades to
your personal collection, and viewing information on Beyblades and tournament outcomes in the
database. The script connects to a MySQL database ('beybladedb') to perform various SQL queries 
and stored procedure calls.

Make sure to configure the MySQL connection details and run the necessary SQL scripts to set up
the database schema before using this script (instructions in README).
"""


import sys  # to print error messages to sys.stderr
import mysql.connector
# To get error codes from the connector, useful for user-friendly
# error-handling
import mysql.connector.errorcode as errorcode

from tabulate import tabulate

# For output coloring
import colorama
from colorama import Fore

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
            user='gokus',
            # Find port in MAMP or MySQL Workbench GUI or with
            # SHOW VARIABLES WHERE variable_name LIKE 'port';
            port='3306',  # this may change!
            password='gokuspw',
            database='beybladedb'  # replace this with your database name
        )
        print('Successfully connected.')
        return conn
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in your
        # simulated program. Their user information would be in a users table
        # specific to your database; hence the DEBUG use.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr.write('Incorrect username or password'
                             'when connecting to DB.' + '\n')
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
        print(Fore.RED + f"\nYou currently have no Beyblades in your collection")

    cursor.close()
    conn.close()


def heaviest_beyblade_for_type(beyblade_type):
    """
    Fetches and displays the ID and name of the heaviest Beyblade of a specific 
    type.
    Arguments:
        beyblade_type (str): The type of Beyblade (Attack, Defense, Stamina, 
        Balance).
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
            print(Fore.BLUE + f"\nThe heaviest Beyblade of type '{beyblade_type}' is ID: "
                f"{beyblade_id}, Name: {name_result[0]}")
        else:
            print(Fore.RED + f"\nNo Beyblade found with ID: {beyblade_id}")
    else:
        print(Fore.RED + f"\nNo heaviest Beyblade found for type '{beyblade_type}'")

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

    # Fetching all results
    results = cursor.fetchall()
    if not results:
        print(Fore.RED + "\nNo battles found for user!")
    else:
        headers = ["Battle ID", "Tournament Name", "Date", "Location",
                   "Player 1 Username", "Player 2 Username",
                   "Player 1 Beyblade Name", "Player 2 Beyblade Name",
                   "Player 1 Beyblade ID", "Player 2 BeyBlade ID", "Winner ID"]

        print(tabulate(results, headers=headers, tablefmt="grid"))

    # Closing cursor and connection
    cursor.close()
    conn.close()


def view_all_tournament_names():
    """
    Retrieves and prints unique tournament names from the 'battles' table. If 
    no tournaments exist,
    indicates no tournaments found.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # SQL query to select distinct tournament names
    sql = ("SELECT DISTINCT tournament_name FROM battles ORDER BY "
           "tournament_name;")

    try:
        cursor.execute(sql)
        tournaments = cursor.fetchall()  # Fetch all results

        if tournaments:
            print(Fore.BLUE + "\nList of Tournament Names:")
            for tournament in tournaments:
                print(tournament[0])  # Print each tournament name
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
                print(location[0])  # Print each location
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


def view_battle_results_for_tournament(tournament_name):
    """
    Queries the battles table for all battle results related to the 
    specified tournament.

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


def add_beyblade(name, type, series, is_custom, face_bolt_id, energy_ring_id,
                 fusion_wheel_id, spin_track_id, performance_tip_id):
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
    conn = get_conn()
    cursor = conn.cursor()
    sql = (
        "INSERT INTO beyblades (name, type, series, is_custom, face_bolt_id, "
        "energy_ring_id, fusion_wheel_id, spin_track_id, performance_tip_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
    data = (
        name,
        type,
        series,
        is_custom,
        face_bolt_id,
        energy_ring_id,
        fusion_wheel_id,
        spin_track_id,
        performance_tip_id)
    try:
        cursor.execute(sql, data)
        conn.commit()
        print(Fore.BLUE + f"\nAdded new Beyblade: {name}")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")


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


def view_beyblade_parts(beyblade_id):
    """
    Queries the database for the names and weights of all parts that make up a 
    specific
    Beyblade and prints them in a well-formatted table.

    Arguments:
        beyblade_id (str) - The ID of the Beyblade.
    Returns: Prints the PART ID, Part Type, Part Description, and Weight in a 
             formatted table.
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

# ----------------------------------------------------------------------
# Functions for Logging Users In
# ----------------------------------------------------------------------
# Note: There's a distinction between database users (admin and client)
# and application users (e.g. members registered to a store). You can
# choose how to implement these depending on whether you have app.py or
# app-client.py vs. app-admin.py (in which case you don't need to
# support any prompt functionality to conditionally login to the sql database)


def is_client(username):
    """
    Helper function to verify whether the user logging in is a BeyClient.
    Checks the `is_admin` flag for the given username in the `users` table.
    """
    cursor = conn.cursor()
    sql = "SELECT is_admin FROM users WHERE username = %s;"
    try:
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        # If the user exists and the is_admin flag is false, return True
        if result and (not result[0]):
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

    print("\n------------------------------ BeyClient Login -----------------"
          "-------------\n")

    while True:
        username = input("USERNAME: ").lower()
        password = input("PASSWORD: ").lower()

        while not is_client(username):
            print("\nIt appears that you are not a BeyClient. Please try "
                  "again! \n")
            username = input("USERNAME: ").lower()
            password = input("PASSWORD: ").lower()

        sql = "SELECT authenticate('%s', '%s');" % (username, password)

        try:
            cursor.execute(sql)
            check_response = cursor.fetchone()

            if check_response[0] == 1:
                show_options(username)
            else:
                print("\nUsername or password is incorrect. Please try again "
                      ":)\n")

        except mysql.connector.Error as err:
            if DEBUG:
                sys.stderr(err)
                sys.exit(1)
            else:
                sys.stderr("Error logging in.")

# Add user to 'user_info' and 'users' tables


def add_user(username, email, password, is_admin):
    """
    Adds the user to the users and user_info table.

    Arguments:
        username (str) - The username of the new user.
        email (str) - The email address of the new user.
        password (str) - The password for the new user.
        is_client (bool) - Always 0, since this is client.

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
        print(Fore.BLUE + f"\nUser '{username}' added successfully")
    except mysql.connector.Error as err:
        print(Fore.RED + f"\nError: {err}")


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

    valid_types = ['Attack', 'Defense', 'Stamina', 'Balance']
    if type not in valid_types:
        print(Fore.RED + f"\nError: Invalid Beyblade type '{type}'. "
            f"Please enter one of {valid_types}."
        )

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

    print('  (a) Create an account')  
    print('  (b) Add a Beyblade to your collection')  
    print('\n')

    print('* View Beyblade Information: ')
    print('  (c) View all Beyblades')  
    print('  (d) View your Beyblades.')  
    print('  (e) View the heaviest Beyblade for a type')  
    print('\n')

    print('* View Beyblade Part Information: ')
    print('  (f) View information about a part')  
    print('  (h) View all parts in the database')
    print('  (i) View parts of a Beyblade')
    print('\n')

    print('* View Battle Information: ')
    print('  (j) View all tournament names')
    print('  (k) View all battle locations')
    print('  (l) View your battle results')
    print('  (m) View battle results for a tournament')
    print('  (n) View battle results for location')
    print('  (o) View Beyblade Battles leaderboard')
    print('\n')

    print('  (q) quit')
    print()
    ans = input('Enter an option: ').lower()

    if ans == 'q':
        quit_ui()
    elif ans == 'a':
        print("\nCREATING A NEW ACCOUNT.")
        new_username = input('Enter username: ')
        email = input('Enter email: ')
        password = input('Enter password: ')
        add_user(new_username, email, password, 0)
        show_options(username)
    elif ans == 'b':
        print("\nADDING A BEYBLADE TO YOUR ACCCOUNT.")
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
    elif ans == 'c':
        print(Fore.BLUE + "\nVIEWING ALL BEYBLADES.")
        view_all_beyblades()
        show_options(username)
    elif ans == 'd':
        print(Fore.BLUE + "\nVIEWING YOUR BEYBLADES.")
        view_user_beyblades(username)
        show_options(username)
    elif ans == 'e':
        # Validation for Beyblade entered type
        valid_types = ['Attack', 'Defense', 'Stamina', 'Balance']
        while True:
            beyblade_type = input(
                'Enter Beyblade type (Attack, Defense, Stamina, Balance): ').capitalize()
            if beyblade_type in valid_types:
                heaviest_beyblade_for_type(beyblade_type)
                break
            else:
                print(Fore.RED + f"\nError: Invalid Beyblade type. Please enter one of {valid_types}.")
        show_options(username)
    elif ans == 'f':
        print(Fore.BLUE + "\nVIEWING INFORMATION ABOUT A PART.")
        part_ID = input('Enter part ID: ')
        view_part_info(part_ID)
        show_options(username)
    elif ans == 'g':
        print(Fore.BLUE + "\nVIEWING ALL BEYBLADES IN YOUR COLLECTION.")
        # view_user_beyblades()
        show_options(username)
    elif ans == 'h':
        print(Fore.BLUE + "\nVIEWING ALL BEYBLADE PARTS.")
        view_all_beyblade_parts()
        show_options(username)
    elif ans == 'i':
        print(Fore.BLUE + "\nVIEWING ALL PARTS FOR A BEYBLADE.")
        beyblade_ID = input('Enter Beyblade ID: ')
        view_beyblade_parts(beyblade_ID)
        show_options(username)
    elif ans == 'j':
        print(Fore.BLUE + "\nVIEWING ALL TOURNAMENT NAMES.")
        view_all_tournament_names()
        show_options(username)
    elif ans == 'k':
        print(Fore.BLUE + "\nVIEWING ALL TOURNAMENT LOCATIONS.")
        view_all_battle_locations()
        show_options(username)
    elif ans == 'l':
        print(Fore.BLUE + "\nVIEWING YOUR BATTLE RESULTS.")
        view_all_battle_results_for_user(username)
        show_options(username)
    elif ans == 'm':
        print(Fore.BLUE + "\nVIEWING RESULTS FOR TOURNAMENT.")
        tournament_name = input('Enter tournament name: ')
        view_battle_results_for_tournament(tournament_name)
        show_options(username)
    elif ans == 'n':
        print(Fore.BLUE + "\nVIEWING BATTLE RESULTS FOR LOCATION.")
        tournament_location = input('Enter tournament location: ')
        view_battle_results_for_location(tournament_location)
        show_options(username)
    elif ans == 'o':
        print(Fore.BLUE + "\nVIEWING BEYBLADE BATTLE LEADERBOARD.")
        beyblade_leaderboard()
        show_options(username)
    elif ans == 'q':
        quit_ui()


def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    print('\n-----------------------------------------------------'
          '-----------\n')
    print('Thank you for keeping the Beyblade legacy ablaze. May the Beyblade '
          'spirit be with you. Goodbye!')
    print('\n-----------------------------------------------------'
          '-----------\n')
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
