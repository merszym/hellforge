# Hellforge

Helpfully labeled layers (for geneticists)

A Database/Webapp to provide archaeological context for samples.

### Requirements

- conda

### Start

this assumes, that you have a compatible version of the hellforge database (named `db.sqlite3`) sitting in the root of this folder structure. Otherwise please contact me :D

To run this webapp locally, install and activate the environment:

```
conda env create -f env.yml
conda activate hellforge
```

Then create a `.env` file in the root of the repository, make sure to include the following `secrets`:
```
SECRET_KEY="RANDOM-STRING-HERE"
DEBUG=True
HOST="localhost 127.0.0.1"
```

Then run the django server!

```
python3 manage.py runserver
```

And in your browser navigate to `localhost:8000`
