# Hellforge

**Helpfully labeled layers (for geneticists)**

A Webapp/Database for the collection of archaeological context information related to **ancient sedimentary DNA research** projects. The key unit for the database is the "Archaeological Layer"

## Explore

The webapp is currently available at [https://hellforge.merlin-szymanski.de](https://hellforge.merlin-szymanski.de/site/list)

## Build

### Requirements

- [uv](https://github.com/astral-sh/uv) for package management  

### Start

1. Clone the github repository `git clone https://www.github.com/merszym/hellforge` and change into it `cd hellforge`
2. Create a file `.env` that will contain some instance-specific settings (see below)
3. Set up the database and your useraccount (see below)
4. Start the database

### Instructions

##### env-file

Create an `.env` file (thats the full name, it starts with a `.` so it is invisible later) in the hellforge directory, make sure to include the following `settings`:
Be aware of the quotation marks for the string-based values.

```
SECRET_KEY="RANDOM-STRING-HERE"
DEBUG=True
HOST="localhost 127.0.0.1"
```

##### Database and User

If you have a copy of the hellforge database (named `db.sqlite3`) copied into the dierctory already, skip this step. Otherwise create an empty database:

```
uv run manage.py migrate
```
Voila, you have a database called "db.sqlite3" sitting in your folder. Then, please create a user to enjoy user privileges

```
uv run manage.py createsuperuser
```

##### Run the Database
and then start the webapp

```
uv run manage.py runserver
```

And in your browser navigate to `localhost:8000`
If you created an empty database, log into the admin-interface first to start editing the database `localhost:8000/admin`
