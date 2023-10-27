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

And run the django server!

```
python3 manage.py runserver
```

And in your browser navigate to `localhost:8000`
