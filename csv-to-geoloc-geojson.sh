#!/bin/bash
dos2unix $1.csv
python3 csv-to-geoloc-geojson.py "$1"
