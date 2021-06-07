#!/bin/bash
dos2unix commerces-tournefeuille.csv
python3 csv-to-geoloc-geojson.py "commerces-tournefeuille"