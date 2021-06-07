import sys
import os
import re
import csv
import json
import pandas
import urllib.request
import logging

if len(sys.argv) != 1:
  logging.error("%s: must have one argument, root csv name (without csv extension), exiting ...", sys.argv[0])

rootname = sys.argv[1]

if not rootname:
  logging.error("%s: argument could not be empty", sys.argv[0])

if not os.path.exists(rootname + '.csv'):
  logging.error("file %s must exist", rootname + '.csv')

if os.path.exists(rootname + '.log'):
  os.remove(rootname + '.log')

logging.basicConfig(filename=rootname + '.log', \
  format='%(asctime)s - %(levelname)s:%(message)s', \
  encoding='utf-8', level=logging.DEBUG)

if os.path.exists(rootname + '-out.csv'):
  os.remove(rootname + '-out.csv')

with open(rootname + '.csv', newline='') as csvfiler:
  csvheader = csv.reader(csvfiler, delimiter=';', quotechar='|')
  logging.info("read header...")
  header = next(csvheader)
  logging.debug("header: %s", header)
csvfiler.close()

csvfilew = open(rootname + '-out.csv', 'w', newline='')
csvwriter = csv.DictWriter(csvfilew, delimiter=',', fieldnames=header)

csvreader = csv.DictReader(open(rootname + '.csv', newline=''), \
  delimiter=';', quotechar='|')

logging.info("write header...")
csvwriter.writerow(dict((fn,fn) for fn in header))

for row in csvreader:
  print(row)
  name = row['designation']

  # replace multiple spaces with single space in the address field
  # same with re.sub('\s+',' ',row[3])
  address = ' '.join(row['adresse'].split()).replace(" ", "+")
  address = address.replace("ch ", "chemin ").replace("Ch ", "chemin ") \
                  .replace("av ", "avenue ").replace("Av ", "avenue ") \
                  .replace("r  ", "rue ").replace("R  ", "rue ") \
                  .replace("imp  ", "impasse ").replace("Imp  ", "impasse ") \
                  .replace("all  ", "allee ").replace("All  ", "allee ") \
                  .replace("rte  ", "route ").replace("Rte  ", "route ") \
                  .replace("bd  ", "boulevard ").replace("Bd  ", "boulevard ")
  # TODO: remove non ascii characters from address
  city = row['commune']
  postcode = row['code_postal']
  logging.debug("processing: %s ...", name)
  
  # TODO url in global var
  query = "https://api-adresse.data.gouv.fr/search/?q=" + \
          address + "+" + city + "&postcode=" + postcode + "&limit=1"
  print("[DEBUG]: query", query, "...")
  
  # request to get coordinates from address
  with urllib.request.urlopen(query) as response:
    result = response.read()
    logging.debug("query response: %s", result)
    # curl https://api-adresse.data.gouv.fr/search/\?q\=16+rue+Louis+Pasteur+Tournefeuille\&postcode\=31170\&limit\=1 | jq '.features[0].geometry.coordinates[0]'
    data = json.loads(result)
    for feature in data['features']:
        logging.debug("type of geometry: %s", feature['geometry']['type'])
        logging.debug("coordinates: %s", feature['geometry']['coordinates'])
        
        # rewrite row with coordinates
        newrow = row.copy()
        newrow['longitude'] = feature['geometry']['coordinates'][0]
        newrow['latitude'] = feature['geometry']['coordinates'][1]
        logging.debug("new row: %s", newrow)
        csvwriter.writerow(newrow)
        # sys.exit()

csvfiler.close()
csvfilew.close()

logging.debug("write geojson from csv file...")
data_frame = pandas.read_csv(
    rootname + '-out.csv',
    # parse_dates=[
    #     'last_update',
    #     'input_date',
    #     'date_photo',
    # ],
    infer_datetime_format=True,
    na_values=['']
)
json_result_string = data_frame.to_json(
    orient='records', 
    double_precision=12,
    date_format='iso'
)
json_result = json.loads(json_result_string)
geojson = {
    'type': 'FeatureCollection',
    'features': []
}
for record in json_result:
    geojson['features'].append({
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [record['longitude'], record['latitude']],
        },
        'properties': record,
    })

if os.path.exists(rootname + '-out.geojson'):
  os.remove(rootname + '-out.geojson')

with open(rootname + '-out.geojson', 'w') as f:
    f.write(json.dumps(geojson, indent=2))
f.close()

sys.exit()
