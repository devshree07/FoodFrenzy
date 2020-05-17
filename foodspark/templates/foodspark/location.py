import requests
api_key='AIzaSyDqJGSCO-ZKrbtBQcLflxwqG3zPcP-B2vY'
geo_url = "https://maps.googleapis.com/maps/api/js?key=AIzaSyDqJGSCO-ZKrbtBQcLflxwqG3zPcP-B2vY&callback=initMap"
my_address = {'address': 'Ahmedabad,Gujarat, India', 
             'language': 'en'}
response = requests.get(geo_url, params = my_address)
results = response.json()['results']
print(results)
my_geo = results[0]['geometry']['location']
print("Longitude:",my_geo['lng'],"\n","Latitude:",my_geo['lat'])

