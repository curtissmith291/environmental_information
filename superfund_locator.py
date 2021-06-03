# Import Dependencies
import pandas as pd
import gmaps
import requests
from config import g_key
from geopy import distance
from geopy import Nominatim
import numpy as np

# Configure gmaps
gmaps.configure(api_key=g_key)

# State abreviations; EPA API uses abbreviations, address has whole name
us_state_abbrev = {
    'Alabama': 'AL', 'Alaska': 'AK', 'American Samoa': 'AS', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 
    'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Guam': 'GU', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA','Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
    'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
    'North Dakota': 'ND', 'Northern Mariana Islands':'MP', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Puerto Rico': 'PR',
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virgin Islands': 'VI', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI','Wyoming': 'WY'
}

# Function to get address from user
def address_input():
    global street, city, state, zip_code
    street = input("Enter Address Line 1 (Street Address): ").strip()
    city = input("Enter City: ").strip()
    state = input("Enter State: ")
    zip_code = str(input("Enter Zip/Postal Code: ")).strip()

def distance_calc(row):
    '''
    This function returns the distance in miles between the address lat/long and the Superfund Site lat/long
    '''
    address_coords = (lat, long)
    coord2 = (row['LATITUDE'], row['LONGITUDE'])
    return distance.distance(address_coords, coord2).miles

# Returns out the Site name and URL
site_base_url = 'https://cumulis.epa.gov/supercpad/cursites/csitinfo.cfm?id='

def get_site_url(row):
    to_append = row["SITE_ID"]
    return site_base_url + str(to_append)

'''Interative code below this line'''

# Asks for user address
address_input()

# Combines individual address inputs into one variable
address = street + ", " + city + ", " + state + ", " + zip_code

# Asks if address is correct
while True:
    print(f" You entered: {address}. \n Is this correct?")
    ans = input("Yes or No: ").lower()
    if ans == 'yes':
        break
    elif ans == "no":
        address_input()
    else:
        print("Please enter 'yes' or no'.")

# Returns lat/long from address
try:
    geolocator = Nominatim(user_agent="my_user_agent")
    location = geolocator.geocode(address)
    long_address = location
    lat = location.latitude
    long = location.longitude
    print("\n Address verified: Connecting to EPA Database.")
except:
    print("your address did not return a result. \n Program exiting.")
    exit()

# Returns abbreviation of state for URL
url_state = us_state_abbrev[state]

# EPA API Base URL for Active Superfund Sites
# Returns all location within the state and puts into Pandas DF
request = requests.get(f'https://data.epa.gov/efservice/SEMS_ACTIVE_SITES/SITE_STATE/CONTAINING/{url_state}/JSON').json()
sf_sites_all = pd.DataFrame(request)

# Returning new DF contianing sites that have coordinates, i.e. are currently on the NPL or proposed for NPL
sf_sites_cleaned = sf_sites_all[sf_sites_all["LATITUDE"].notna()]
# sf_sites_cleaned

# Creates a new column with the distance in miles between the address and Superfund Sites
# adding temp Dataframe prevents false positive SettingWithCopyWarning
sf_sites_temp = sf_sites_cleaned.copy()
sf_sites_temp['SITE_DISTANCE'] = sf_sites_cleaned.apply(distance_calc, axis=1)
sf_sites_cleaned = sf_sites_temp.copy()

# Creates new DataFrame with Superfund Site within the specified distance from the address
dist = 50 # 50 miles for troubleshooting; lower or make it user input in later versions
sf_sites_near = sf_sites_cleaned.loc[(sf_sites_cleaned['SITE_DISTANCE'] <= dist)]
sf_sites_near = sf_sites_near.sort_values(by = ['SITE_DISTANCE'])

# Exits program if there are no Superfund Sites near address
if len(sf_sites_near["SITE_NAME"]) == 0:
    print(f"There are 0 Superfund Sites within {dist} miles of your address")
    exit()

# Creates a new column with the Site URL
# adding temp Dataframe prevents false positive SettingWithCopyWarning
sf_sites_temp = sf_sites_near.copy()
sf_sites_temp.loc[:, 'SITE_URL'] = sf_sites_near.apply(get_site_url, axis=1)
sf_sites_near = sf_sites_temp.copy()
# sf_sites_near

# Adds cell information to lists
site_list = sf_sites_near.loc[:, 'SITE_NAME'].tolist()
url_list = sf_sites_near.loc[:, 'SITE_URL'].tolist()
distance_list = sf_sites_near.loc[:, 'SITE_DISTANCE'].tolist()

# Prints out the count of Superfund Sites
count = len(sf_sites_near.index)
print(f"\n There are {count} Superfund Sites within {dist} miles of your address: \n")
for i in range(len(site_list)):
    print(f'{i+1}): {site_list[i]} is {distance_list[i]} miles away. \n'
          f'URL: {url_list[i]} \n')

locations = sf_sites_near[["LATITUDE", "LONGITUDE"]]
fig = gmaps.figure(center=(30.0, 31.0), zoom_level=1.5)
marker_layer = gmaps.marker_layer(locations)
# marker_layer = gmaps.marker_layer(locations, info_box_content=hotel_info)
fig.add_layer(marker_layer)
fig