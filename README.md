# Beyblade Database Project

This project is a full-stack application for the Beyblade community. It manages Beyblade data, including Beyblade parts, configurations, user collections, and tournament battle results.

The system consists of three components:

• **Web application**: allows users to browse Beyblades, manage their personal collection, and view tournament results.

• **FastAPI backend**: exposes REST API endpoints used by the frontend to query and update the database.

• **Command-line interface (CLI)**:  used by administrators to manage the underlying database, including adding Beyblades, parts, users, and battle results.

All data is stored in a **MySQL relational database** that models users, Beyblades, parts, tournaments, battles, and collections.

## Tech Stack

Frontend
- HTML
- CSS
- Vanilla JavaScript

Backend
- Python
- FastAPI
- Pydantic

Database
- MySQL
- Stored Procedures
- SQL scripts for schema, data loading, and permissions

## System Architecture

The system follows a standard full-stack architecture:

Users interact with the web frontend, which sends requests to the FastAPI backend. The backend processes the request and performs SQL queries on the MySQL database.

Administrative operations can also be performed through a CLI interface that connects directly to the database.

## Setup Instructions

### 1. Install Python Dependencies
Before running this program, make sure to install Python dependencies such as Python MySQL Connector and tabulate. Also, note that this program was tested on MySQL Version 8.2.0.
It is advised to create a virtual environment.

```bash
$ python -m venv myenv
$ source myenv/bin/activate
$ pip install mysql-connector-python tabulate colorama
```

### 2. Configure Environment Variables

Create a **.env file** in the project root:

```bash
$ DB_HOST=localhost
$ DB_USER=your_mysql_user
$ DB_PASSWORD=your_mysql_password
$ DB_PORT=3306
$ DB_NAME=beybladedb
```

An example template is provided in **.env.example**.

### 3. Initialize the Database

Run the following command to automatically create and initialize the database:

    mysql --local-infile=1 -u root -p < init_db.sql

This script will
- create the database schema
- load seed data
- install stored procedures and functions
- configure database users and permissions

### 4. Run the Backend SErver

Start the FastAPI server with the following command:

    uvicorn main:app --reload

By default, the server will start at:
    http://127.0.0.1:8000

### 5. Open the Web Application

Open the frontend in your browser (for example web/index.html) and log in using one of the demo accounts.


# Demo Accounts

The registered BeyAdmins (admins) are:

| USER       | PASSWORD      |
|------------|---------------|
| jlavin     | jlavinpw      |

The registered Bladers (clients) are:

| USER       | PASSWORD      |
|------------|---------------|
| gokus     | gokuspw        |
| midoriyai | midoriyaipw    |

# CLI Walkthrough

While the web applicaiton is for Bladers (clients), administrative operations are performed through a CLI. Run the following to start the CLI:

    python app-admin.py

The following is a guide through the CLI:

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

If you are a Blader, then you have access to most of the options above, with the following key restrictions:
- Cannot add a part to the database
- Cannot add a Beyblade to the database, only to their own collection
- Cannot add a new battle result
- Cannot view battles by other admin/client usernames, only by location and tournament name
- Cannot view certain information of users in the database
