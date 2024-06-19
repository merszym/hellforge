# Hellforge

**Helpfully labeled layers (for geneticists)**

This repository contains the code to the Webapp/Database that I use to collect archaeological context for the samples of my **ancient sedimentary DNA research** projects. (And for other sites as well, when I read up on them...)

The database is centered around the concept of **archaeological layers** and the research of **ancient humans** and **mammals**

Because of that it currently stores information about:

**(Published) Archaeological Context**

- Site location and stratigraphy
- Associated human cultures
- Associated epochs
- Dates obtained from the layers or samples
- Associated mammalian taxa
- Geological properties (WIP)

**(Published) Sediment DNA projects**

- Project descriptions
- Samples obtained from the layer
- DNA Results (WIP)

## Explore

The webapp is currently available at [https://hellforge.merlin-szymanski.de](https://hellforge.merlin-szymanski.de/site/list)

## Build

### Requirements

- conda

### Start

Assuming, that you have a copy of the hellforge database (named `db.sqlite3`) sitting in the root of the folder structure

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
