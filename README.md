# Beyblade-Database-Project

The GitHub repository establishes a Beyblade database project, cataloging Beybalde parts, configurations, and battle outcomes. It features a dual command-line interface, one tailored for a Blader (client) and another for a BeyAdmin (administrator), enabling users to execute a wide variety of functions. These include account creation, strategic Beyblade assembly based on accessible data, management of their personal Beyblade collection, as well as the analysis of battle statistics for various Beyblades and tournaments.

Before running this program, make sure to install Python MySQL Connector and tabulate with pip. Also, note that this program was tested on MySQL Version 8.2.0.
It is advised to create a virtual environment and do the following:

```bash
$ python -m venv myenv
$ source myenv/bin/activate
$ pip install mysql-connector-python tabulate colorama
```

# Setup Instructions

In your computer's command line, do the following:

    $ mysql --local-infile=1 -u root -p

and enter your password accordingly, assuming root is the username being used to log into the MySQL database server and 'mysql' is the command-line client.

(Note: Deleting a databse with DROP DATABASE beybladedb also deletes all routinres, procedures, etc. associated with it)

Create and use database in the MySQL command-line interface:

    mysql> SET GLOBAL local_infile = TRUE;

    mysql> CREATE DATABASE beybladedb;

    mysql> USE beybladedb;

Run the following commands to establish the backend of the project:

    mysql> SOURCE setup.sql;

    mysql> SOURCE load-data.sql

    mysql> SOURCE setup-passwords.sql;

    mysql> SOURCE setup-routines.sql;

    mysql> SOURCE grant-permissions.sql;

    mysql> SOURCE queries.sql;

# Instructions for Running Python Program

Quit out of MySQL CLI:

    mysql> quit

If you are a client, run

    $ python app-client.py

If you are an admin, run

    $ python app-admin.py

After running either of the two commands above, enter the username and password accordingly.

The registered BeyAdmins (admins) are:

| USER       | PASSWORD      |
|------------|---------------|
| jlavin     | jlavinpw      |

The registered Bladers (clients) are:

| USER       | PASSWORD      |
|------------|---------------|
| gokus     | gokuspw        |
| midoriyai | midoriyaipw    |

# Walkthrough

The following is a guide through the functionalities of this application:

If you are a BeyAdmin:

    1. Select option (f) to view all Beyblades in the database

    2. Select option (p) to view current users in the database

    3. Select option (g) to view Beyblades from a user's collection with a username from option (p)

    4. Select option (h) to view all Beyblade parts in the database

    5. Select option (i) to view parts of a Beyblade with Beyblade ID from option (f)

    6. Select option (j) to view weight and description of a part given part ID from option (h)

    7. Select option (k) to view the heaviest Beyblade for a Beyblade type in the database

    8. Select option (l) to view all tournament names for the battles in the database

    9. Select option (m) to view all battle results of a specific tournament name from option (8)
    
    10. Select option (n) to view all battle locations in the database

    11. Select option (o) to view the battle results of a specific location from option (n)

    12. Select option (r) to view the battle results for a user with username from option (p)

    13. Select option (s) to view Beyblade leaderboard

    14. Select option (a) to add a part to the database using the format seen from option (h)

    15. Select option (b) to add a new Beyblade to the database using the format seen from option (f) and part IDs from option (h)

    16. Select option (c) to add a new Beyblade to your collection

    17. Select option (d) to add a new battle result using format seen from option (m), user ID from option (p) and Beyblade-Player ID from option (g)

    18. Select option (e) to add a new user to the database

    19. Select option (q) to quit

If you are a Blader, then you have access to most of the options above, with the following restrictions (note different letters 
corresonding to different options for BeyAdmin and Blader):
- Cannot add a part to the database
- Cannot add a Beyblade to the database, only to their own collection
- Cannot add a new battle result
- Cannot view battles by other admin/client usernames, only by location and tournament name
- Cannot view certain information of users in the database
