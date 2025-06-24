"""This module defines a FastMCP server for Google Maps Platform operations."""
import os
import re
import json
import asyncio
import googlemaps
from fastmcp import FastMCP
from typing import Optional, Dict, Any


#---------------
# settings
#---------------
host=os.environ.get("FASTMCP_HOST", "0.0.0.0")
port=os.environ.get("FASTMCP_PORT", 8080)
transport=os.environ.get("FASTMCP_TRANSPORT", "stdio")  # stdio, streamable-http, sse

google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=google_maps_api_key)


#-------------
# helpers
#-------------
allowed_modes = ["driving", "walking", "bicycling", "transit"]
def assert_mode(mode: str):
    assert mode in allowed_modes, f"ERROR: '{mode}' is not one of the allowed modes: {allowed_modes}"

allowed_input_types = ["textquery", "phonenumber"]
def assert_input_type(input_type: str):
    assert input_type in allowed_input_types, f"ERROR: '{input_type}' is not one of the allowed inpute types: {allowed_input_types}"


#-----------------------
# initialize fastmcp
#-----------------------
# https://gofastmcp.com/servers/fastmcp#server-configuration
mcp = FastMCP(
    name="FastMCP Google Maps Platform Server",
    dependencies=["googlemaps==4.10.0", "asyncio==3.4.3"],
    on_duplicate_tools="error",
)


#-------------------
# direction tools
#-------------------
@mcp.tool()
async def get_directions(origin: str, destination: str, mode: str="driving") -> Optional[Dict[str, Any]]:
    """Gives step-by-step instructions to get from origin to destination uisng a particular mode of transport
    Args:
        origin (str): originating address
        destination (str): destination address
        mode (str, optional): mode of transportation. Valid options are: driving, walking, bicycling, transit

    Returns:
        dictionary (JSON) of steps along with total distance and total duration
    """
    try:
        assert_mode(mode)
    except AssertionError as e:
        print(e)

    results = gmaps.directions(origin, destination, mode)

    if results:
        shortest_route = results[0]

        output = {
            "summary": shortest_route['summary'],
            "total_distance": shortest_route['legs'][0]['distance']['text'],
            "total_duration": shortest_route['legs'][0]['duration']['text'],
            "steps": []
        }

        for leg in shortest_route['legs']:
            for step in leg['steps']:
                output["steps"].append({
                    "instruction": step['html_instructions'],
                    "distance": step['distance']['text'],
                    "duration": step['duration']['text']
                })
        return json.dumps(output, separators=(',', ':'))
    else:
        return "No directions found for the specified locations."


#--------------------------
# distance matrix tools
#--------------------------
@mcp.tool()
async def get_distance(origin: str, destination: str, mode: str="driving") -> Optional[Dict[str, Any]]:
    """Finds the distance and travel time between two locations
    Args:
        origin (str): originating address
        destination (str): destination address

    Returns:
        dictionary (JSON) of total distance and total travel time duration
    """
    try:
        assert_mode(mode)
    except AssertionError as e:
        print(e)

    results = gmaps.distance_matrix(origin, destination, mode)

    if results:
        shortest_distance = results.get('rows', {})[0]

        output = {
            "total_distance": shortest_distance['elements'][0]['distance']['text'],
            "total_duration": shortest_distance['elements'][0]['duration']['text'],
        }
        return json.dumps(output, separators=(',', ':'))
    else:
        return "No directions found for the specified locations."


#-------------------
# geocoding tools
#-------------------
@mcp.tool()
async def get_geocode(address: str) -> Optional[Dict[str, Any]]:
    """
    Args:
        address (str): can be address or the name of a place

    Returns:
        dictionary (JSON) with the geocode (latitude & longitude) of the address
    """
    results = gmaps.geocode(address)

    if results:
        geocode = results[0]

        output = {
            "lat": geocode['geometry']['location']['lat'],
            "lng": geocode['geometry']['location']['lng'],
        }

        return json.dumps(output, separators=(',', ':'))
    else:
        return "Address not found"


#-------------------
# places tools
#-------------------
@mcp.tool()
async def find_place(input: str, input_type: str="textquery", fields: list=["place_id", "formatted_address", "name", "geometry", "types", "rating"]) -> Optional[Dict[str, Any]]:
    """Find/query a place with the provided name
    Args:
        input (str): name of the place you're looking for. provide more details if possible (i.e. city, country, etc.) for better accuracy. can also be the establishment type (i.e. bakery, bank, etc.)
        input_type (str, optional): the type of query, it can be a textquery or phonenumber query
        fields (list, optional): list of fields to query for

    Returns:
        dictionary (JSON) of with basic information of the top result based on input query. basic information inclulde:
        - name
        - place_id
        - address
        - location (latitude, longitude)
        - establishment type
        - average rating
    """
    try:
        assert_input_type(input_type)
    except AssertionError as e:
        print(e)

    results = gmaps.find_place(input, input_type, fields)

    if results:
        try:
            place = results.get('candidates', {})[0]
        except IndexError:
            return "No such place found"

        output = {
            "name": place['name'],
            "place_id": place['place_id'],
            "formatted_address": place['formatted_address'],
            "location": place['geometry']['location'],
            "types": place['types'],
            "rating": place.get('rating', None),
        }
        return json.dumps(output, separators=(',', ':'))


@mcp.tool()
async def place_nearby(location: dict, radius: int, place_type: str) -> Optional[Dict[str, Any]]:
    """Find types of places within a radius of a location (latitude, longitude)
    Args:
        location (dict): dictionary with 'lat' and 'lng' as keys and values are the latitude and longitude respectively
        radius (int): search area radius in meters (i.e. 2500 = 2.5km)
        place_type (str): type of place you're looking for (i.e. "italian restaurant", "hotel", etc.)

    Returns:
        dictionary (JSON) of establishment names (key) and their place_id (value)
    """
    results = gmaps.places_nearby(location, radius, place_type)
    output = {}

    if results:
        places_nearby = results.get('results', {})

        for place in range(len(places_nearby)):
            place_name = places_nearby[place]['name']
            place_id = places_nearby[place]['place_id']

            output[place_name] = place_id

        return json.dumps(output, separators=(',', ':'))
    else:
        return "Nothing nearby that matches the search criteria was found."


@mcp.tool()
async def place_details(place_id: str, fields: list=["name", "formatted_address", "formatted_phone_number", "website", "types", "rating", "user_ratings_total"]) -> Optional[Dict[str, Any]]:
    """
    Args:
        place_id (str): place_id of the place, which can be obtained via find_place() or place_nearby()
        fields (list, optional): list of fields to query for

    Returns:
        dictionary (JSON) of with details of provided place. details inclulde:
        - name
        - address
        - phone number
        - website
        - establishment type
        - average rating
        - total rating count
    """
    results = gmaps.place(place_id, fields)

    if results:
        place_details = results.get('result', {})

        output = {
            "name": place_details['name'],
            "formatted_address": place_details['formatted_address'],
            "formatted_phone_number": place_details.get('formatted_phone_number', None),
            "website": place_details.get('website', None),
            "types": place_details['types'],
            "rating": place_details.get('rating', None),
            "user_ratings_total": place_details.get('user_ratings_total', 0),
        }
        return json.dumps(output, separators=(',', ':'))
    else:
        return "No such place found."


#----------------
# main
#----------------
# https://gofastmcp.com/deployment/running-server
if __name__ == "__main__":
    try:
        asyncio.run(mcp.run(transport=transport, host=host, port=port))
    except KeyboardInterrupt:
        print("> FastMCP Google Maps Server stopped by user.")
    except Exception as e:
        print(f"> FastMCP Google Maps Server encountered error: {e}")
    finally:
        print("> FastMCP Google Maps Server exiting.")
