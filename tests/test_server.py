"""Unit tests for server.py."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch, MagicMock, PropertyMock

# Since server.py might try to initialize googlemaps.Client immediately,
# we need to patch it *before* importing the server module.
# We also need to mock GOOGLE_MAPS_API_KEY as it's read at module level.
MOCK_API_KEY = "test_api_key"

# Patch os.getenv specifically for GOOGLE_MAPS_API_KEY
patch_getenv = patch('os.getenv', return_value=MOCK_API_KEY)
patch_getenv.start()

# Patch googlemaps.Client before it's imported by server
patch_gmaps_client = patch('googlemaps.Client', autospec=True)
mock_gmaps_client_constructor = patch_gmaps_client.start()

# Now it's safe to import the server module and its components
from server import (
    get_directions,
    get_distance,
    get_geocode,
    find_place,
    place_nearby,
    place_details,
    assert_mode,
    assert_input_type,
    gmaps # This will be the mocked instance
)

# Stop the patches after server module is loaded if they are not needed globally for all tests
# However, gmaps instance in server.py is created at module level, so mock_gmaps_client_constructor
# needs to remain active for the tests to use the mocked gmaps.
# patch_getenv.stop() # Keep this active if server re-reads env var, or stop if not needed.


# Fixture to provide a fresh mock of the gmaps client for each test
@pytest.fixture
def mock_gmaps():
    # server.gmaps is already a MagicMock due to the class-level patch.
    # We can reset it or reconfigure it per test if needed.
    # For instance, to ensure each test gets a fresh mock state:
    instance = mock_gmaps_client_constructor.return_value
    instance.reset_mock() # Reset call counts, etc.
    return instance

# Example of how to stop class-level patches after all tests if necessary,
# though pytest usually handles teardown well.
# def pytest_sessionfinish(session, exitstatus):
#     patch_gmaps_client.stop()
#     patch_getenv.stop()

# --- Helper Function Tests ---

def test_assert_mode_valid():
    """Test assert_mode with valid modes."""
    for mode in ["driving", "walking", "bicycling", "transit"]:
        assert_mode(mode) # Should not raise

def test_assert_mode_invalid():
    """Test assert_mode with an invalid mode."""
    with pytest.raises(AssertionError) as excinfo:
        assert_mode("flying")
    assert "'flying' is not one of the allowed modes" in str(excinfo.value)

def test_assert_input_type_valid():
    """Test assert_input_type with valid types."""
    for input_type in ["textquery", "phonenumber"]:
        assert_input_type(input_type) # Should not raise

def test_assert_input_type_invalid():
    """Test assert_input_type with an invalid type."""
    with pytest.raises(AssertionError) as excinfo:
        assert_input_type("email")
    assert "'email' is not one of the allowed inpute types" in str(excinfo.value) # Typo "inpute" is in original code


# --- Tool Function Tests (Placeholder Structure) ---
# We will fill these in based on the plan

# print(">>>>>>>>>>>> DIR GET_DIRECTIONS", dir(get_directions)) # Temporary debug line

@pytest.mark.asyncio
async def test_get_directions_success(mock_gmaps):
    """Test get_directions successfully returns directions."""
    mock_api_response = [
        {
            "summary": "US-101 S",
            "legs": [
                {
                    "distance": {"text": "100 mi"},
                    "duration": {"text": "2 hours"},
                    "steps": [
                        {
                            "html_instructions": "Head south on US-101 S",
                            "distance": {"text": "50 mi"},
                            "duration": {"text": "1 hour"}
                        },
                        {
                            "html_instructions": "Continue straight",
                            "distance": {"text": "50 mi"},
                            "duration": {"text": "1 hour"}
                        }
                    ]
                }
            ]
        }
    ]
    mock_gmaps.directions.return_value = mock_api_response

    origin = "San Francisco"
    destination = "San Jose"
    mode = "driving"
    result = await get_directions.fn(origin, destination, mode)

    mock_gmaps.directions.assert_called_once_with(origin, destination, mode)

    expected_output = {
        "summary": "US-101 S",
        "total_distance": "100 mi",
        "total_duration": "2 hours",
        "steps": [
            {
                "instruction": "Head south on US-101 S",
                "distance": "50 mi",
                "duration": "1 hour"
            },
            {
                "instruction": "Continue straight",
                "distance": "50 mi",
                "duration": "1 hour"
            }
        ]
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_get_directions_no_results(mock_gmaps):
    """Test get_directions when API returns no results."""
    mock_gmaps.directions.return_value = [] # Empty list simulates no results

    origin = "Oz"
    destination = "Wonderland"
    result = await get_directions.fn(origin, destination)

    mock_gmaps.directions.assert_called_once_with(origin, destination, "driving") # Default mode
    assert result == "No directions found for the specified locations."

@pytest.mark.asyncio
async def test_get_directions_invalid_mode(mock_gmaps, capsys):
    """Test get_directions with an invalid mode."""
    origin = "San Francisco"
    destination = "San Jose"
    invalid_mode = "flying"

    # The function currently prints the assertion error and then proceeds,
    # potentially raising an error later if gmaps.directions can't handle the mode.
    # For this test, we check the printed output and that directions wasn't called with invalid mode.
    # A more robust implementation would return an error message or raise.

    # Set up the mock gmaps client to return an empty list,
    # as our function will call it even with an invalid mode.
    mock_gmaps.directions.return_value = []

    result = await get_directions.fn(origin, destination, invalid_mode)

    # assert_mode now causes an early return with a JSON error message
    expected_error_msg = f"ERROR: '{invalid_mode}' is not one of the allowed modes: {['driving', 'walking', 'bicycling', 'transit']}"
    assert json.loads(result) == {"error": expected_error_msg}

    # gmaps.directions should NOT be called if assert_mode fails and returns early
    mock_gmaps.directions.assert_not_called()


@pytest.mark.asyncio
async def test_get_distance_success(mock_gmaps):
    """Test get_distance successfully returns distance and duration."""
    mock_api_response = {
        "rows": [
            {
                "elements": [
                    {
                        "distance": {"text": "50 km"},
                        "duration": {"text": "1 hour"}
                    }
                ]
            }
        ]
    }
    mock_gmaps.distance_matrix.return_value = mock_api_response

    origin = "Point A"
    destination = "Point B"
    mode = "driving"
    result = await get_distance.fn(origin, destination, mode)

    mock_gmaps.distance_matrix.assert_called_once_with(origin, destination, mode)

    expected_output = {
        "total_distance": "50 km",
        "total_duration": "1 hour",
        "mode": "driving",
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_get_distance_no_results(mock_gmaps):
    """Test get_distance when API returns no results or malformed response."""
    # Covers cases like empty 'rows', or 'elements' not having expected structure
    mock_gmaps.distance_matrix.return_value = {"rows": []}

    origin = "Atlantis"
    destination = "El Dorado"
    default_fields_mode = "driving" # Default mode used by get_distance if not specified

    # Scenario 1: API returns {"rows": []} (empty rows)
    mock_gmaps.distance_matrix.return_value = {"rows": []}
    result_empty_rows = await get_distance.fn(origin, destination, default_fields_mode)
    mock_gmaps.distance_matrix.assert_called_once_with(origin, destination, default_fields_mode)
    assert result_empty_rows == "No distance information found for the specified locations."

    # Scenario 2: API returns rows with empty elements list
    mock_gmaps.reset_mock()
    mock_gmaps.distance_matrix.return_value = {"rows": [{"elements": []}]}
    result_empty_elements = await get_distance.fn(origin, destination, default_fields_mode)
    mock_gmaps.distance_matrix.assert_called_once_with(origin, destination, default_fields_mode)
    assert result_empty_elements == "No distance information found for the specified locations."

    # Scenario 3: API returns element with ZERO_RESULTS status
    mock_gmaps.reset_mock()
    mock_gmaps.distance_matrix.return_value = {
        "rows": [{"elements": [{"status": "ZERO_RESULTS"}]}]
    }
    result_zero_results = await get_distance.fn(origin, destination, default_fields_mode)
    mock_gmaps.distance_matrix.assert_called_once_with(origin, destination, default_fields_mode)
    # The current server logic will return the generic message because the ZERO_RESULTS element is missing distance/duration
    assert result_zero_results == "No distance information found for the specified locations."

    # Scenario 4: API returns None (overall falsy response)
    mock_gmaps.reset_mock()
    mock_gmaps.distance_matrix.return_value = None
    result_none_response = await get_distance.fn(origin, destination, default_fields_mode)
    mock_gmaps.distance_matrix.assert_called_once_with(origin, destination, default_fields_mode)
    assert result_none_response == "No distance information found for the specified locations."


@pytest.mark.asyncio
async def test_get_distance_invalid_mode(mock_gmaps, capsys):
    """Test get_distance with an invalid mode."""
    origin = "Point A"
    destination = "Point B"
    invalid_mode = "teleportation"

    # Set the mock to return None, simulating that an invalid mode leads to no results from API
    mock_gmaps.distance_matrix.return_value = None

    result = await get_distance.fn(origin, destination, invalid_mode)

    # assert_mode now causes an early return with a JSON error message
    expected_error_msg = f"ERROR: '{invalid_mode}' is not one of the allowed modes: {['driving', 'walking', 'bicycling', 'transit']}"
    assert json.loads(result) == {"error": expected_error_msg}

    # gmaps.distance_matrix should NOT be called if assert_mode fails and returns early
    mock_gmaps.distance_matrix.assert_not_called()


@pytest.mark.asyncio
async def test_get_geocode_success(mock_gmaps):
    """Test get_geocode successfully returns latitude and longitude."""
    mock_api_response = [
        {
            "geometry": {
                "location": {
                    "lat": 37.7749,
                    "lng": -122.4194
                }
            }
        }
    ]
    mock_gmaps.geocode.return_value = mock_api_response

    address = "1600 Amphitheatre Parkway, Mountain View, CA"
    result = await get_geocode.fn(address)

    mock_gmaps.geocode.assert_called_once_with(address)

    expected_output = {
        "lat": 37.7749,
        "lng": -122.4194
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_get_geocode_not_found(mock_gmaps):
    """Test get_geocode when the API returns no results (address not found)."""
    mock_gmaps.geocode.return_value = [] # Empty list indicates not found

    address = "NonExistent Address, Atlantis"
    result = await get_geocode.fn(address)

    mock_gmaps.geocode.assert_called_once_with(address)
    assert result == "Address not found"

@pytest.mark.asyncio
async def test_find_place_success(mock_gmaps):
    """Test find_place successfully returns place details."""
    mock_api_response = {
        "candidates": [
            {
                "name": "Googleplex",
                "place_id": "ChIJj61dQgK6j4AR4GeTYWZsKWw",
                "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
                "geometry": {"location": {"lat": 37.4224764, "lng": -122.0842499}},
                "types": ["point_of_interest", "establishment"],
                "rating": 4.5
            }
        ]
    }
    mock_gmaps.find_place.return_value = mock_api_response

    query = "Googleplex"
    input_type = "textquery"
    fields = ["place_id", "formatted_address", "name", "geometry", "types", "rating"]
    result = await find_place.fn(query, input_type, fields)

    mock_gmaps.find_place.assert_called_once_with(query, input_type, fields)

    expected_output = {
        "name": "Googleplex",
        "place_id": "ChIJj61dQgK6j4AR4GeTYWZsKWw",
        "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
        "location": {"lat": 37.4224764, "lng": -122.0842499},
        "types": ["point_of_interest", "establishment"],
        "rating": 4.5
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_find_place_no_candidates(mock_gmaps):
    """Test find_place when API returns no candidates."""
    mock_gmaps.find_place.return_value = {"candidates": []} # No candidates found

    query = "MadeUpPlace Central"
    result = await find_place.fn(query, "textquery")

    mock_gmaps.find_place.assert_called_once_with(query, "textquery", ["place_id", "formatted_address", "name", "geometry", "types", "rating"])
    assert result == "No such place found"

@pytest.mark.asyncio
async def test_find_place_invalid_input_type(mock_gmaps, capsys):
    """Test find_place with an invalid input_type."""
    query = "Some Place"
    invalid_type = "urlquery"

    # Set mock to return a valid response structure if called, to isolate assert_input_type behavior
    mock_gmaps.find_place.return_value = {"candidates": []}

    result = await find_place.fn(query, invalid_type)

    expected_error_msg = f"ERROR: '{invalid_type}' is not one of the allowed inpute types: {['textquery', 'phonenumber']}" # Original typo "inpute"
    assert json.loads(result) == {"error": expected_error_msg}

    # gmaps.find_place should NOT be called if assert_input_type fails and returns early
    mock_gmaps.find_place.assert_not_called()

@pytest.mark.asyncio
async def test_place_nearby_success(mock_gmaps):
    """Test place_nearby successfully returns a dictionary of nearby places."""
    mock_api_response = {
        "results": [
            {"name": "Cafe Alpha", "place_id": "place_id_alpha"},
            {"name": "Restaurant Beta", "place_id": "place_id_beta"}
        ]
    }
    mock_gmaps.places_nearby.return_value = mock_api_response

    location = {"lat": 34.0522, "lng": -118.2437} # Los Angeles
    radius = 1500
    place_type = "restaurant"
    result = await place_nearby.fn(location, radius, place_type)

    mock_gmaps.places_nearby.assert_called_once_with(location, radius, place_type)

    expected_output = {
        "Cafe Alpha": "place_id_alpha",
        "Restaurant Beta": "place_id_beta"
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_place_nearby_no_results(mock_gmaps):
    """Test place_nearby when API returns no results."""
    mock_gmaps.places_nearby.return_value = {"results": []} # No results found

    location = {"lat": 0, "lng": 0} # Null Island
    radius = 5000
    place_type = "cafe"
    result = await place_nearby.fn(location, radius, place_type)

    mock_gmaps.places_nearby.assert_called_once_with(location, radius, place_type)
    # The function returns json.dumps({}) if results are empty, which is '"{}"'
    # The message "Nothing nearby that matches the search criteria was found." is for when results itself is None/falsy.
    # Let's test both conditions for full coverage of the function's logic.

    # Scenario 1: API returns {"results": []}
    assert json.loads(result) == {}

    # Scenario 2: API returns None (or other falsy value for 'results')
    mock_gmaps.reset_mock()
    mock_gmaps.places_nearby.return_value = None
    result_for_none_api_response = await place_nearby.fn(location, radius, place_type)
    mock_gmaps.places_nearby.assert_called_once_with(location, radius, place_type)
    assert result_for_none_api_response == "Nothing nearby that matches the search criteria was found."


@pytest.mark.asyncio
async def test_place_details_success(mock_gmaps):
    """Test place_details successfully returns detailed information for a place."""
    mock_api_response = {
        "result": {
            "name": "TechPark Cafe",
            "formatted_address": "123 Innovation Drive, Tech City",
            "formatted_phone_number": "555-0100",
            "website": "http://techparkcafe.example.com",
            "types": ["cafe", "food", "point_of_interest", "establishment"],
            "rating": 4.7,
            "user_ratings_total": 150
        }
    }
    mock_gmaps.place.return_value = mock_api_response

    place_id = "ChIJtestplaceid123"
    fields = ["name", "formatted_address", "formatted_phone_number", "website", "types", "rating", "user_ratings_total"]
    result = await place_details.fn(place_id, fields)

    mock_gmaps.place.assert_called_once_with(place_id, fields)

    expected_output = {
        "name": "TechPark Cafe",
        "formatted_address": "123 Innovation Drive, Tech City",
        "formatted_phone_number": "555-0100",
        "website": "http://techparkcafe.example.com",
        "types": ["cafe", "food", "point_of_interest", "establishment"],
        "rating": 4.7,
        "user_ratings_total": 150
    }
    assert json.loads(result) == expected_output

@pytest.mark.asyncio
async def test_place_details_not_found(mock_gmaps):
    """Test place_details when API indicates place not found or no details."""
    place_id = "ChIJnonexistentplace"
    fields = ["name", "rating"]

    # Scenario 1: API returns an empty 'result' dictionary
    mock_gmaps.place.return_value = {"result": {}}
    result_empty_details = await place_details.fn(place_id, fields)
    mock_gmaps.place.assert_called_once_with(place_id, fields)
    # Expecting the message for when essential details like name are missing.
    # If 'name' is part of requested fields and it's missing, it hits "Essential place details... missing"
    # If 'name' is NOT part of requested fields, and result is empty, it hits "No details found..."
    # Since 'details' itself is empty, the `if not details:` check in server.py is triggered first.
    assert result_empty_details == "No details found for the specified place."

    # Scenario 1b: API returns an empty 'result' dictionary, and 'name' is NOT in fields
    # This should now hit the "No details found for the specified place." if `details` is empty.
    # Or, if 'name' is not requested, the "Essential place details" check on name won't fail.
    # The code `if not details:` should catch an empty `details` dict first.
    mock_gmaps.reset_mock()
    mock_gmaps.place.return_value = {"result": {}}
    fields_no_name = ["rating", "website"]
    result_empty_details_no_name_request = await place_details.fn(place_id, fields_no_name)
    mock_gmaps.place.assert_called_once_with(place_id, fields_no_name)
    assert result_empty_details_no_name_request == "No details found for the specified place."


    # Scenario 2: API returns a 'result' dictionary missing a critical key like 'name' (but 'result' is not empty)
    mock_gmaps.reset_mock()
    mock_gmaps.place.return_value = {"result": {"formatted_address": "Some Address"}} # 'name' is missing
    fields_with_name = ["name", "formatted_address"]
    result_missing_name = await place_details.fn(place_id, fields_with_name)
    mock_gmaps.place.assert_called_once_with(place_id, fields_with_name)
    assert result_missing_name == "Essential place details (e.g. name) are missing."

    # Scenario 3: API returns None (overall falsy response for 'results')
    mock_gmaps.reset_mock()
    mock_gmaps.place.return_value = None
    result_none_response = await place_details.fn(place_id, fields) # fields can be anything here
    mock_gmaps.place.assert_called_once_with(place_id, fields)
    assert result_none_response == "No such place found."
