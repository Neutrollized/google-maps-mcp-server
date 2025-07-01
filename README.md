# Google Maps Platform MCP server
This uses the [googlemaps](https://github.com/googlemaps/google-maps-services-python) Python package (which hasn't been updated since 2023, but does appear to still be active)
- [documentation](https://googlemaps.github.io/google-maps-services-python/docs/index.html)

## Setup
For this example, you will need a Google Maps Platform API key.  I restricted my APIs to the following:
- Directions API
- Distance Matrix API
- Geocoding API
- Places API

You may need to expand on this if you wish to add more functionality.  Here is the [Google Maps Platform API Picker](https://developers.google.com/maps/documentation/api-picker) to help you decided what you need.  You will also need an set an additional environment variable, `GOOGLE_MAPS_API_KEY`.

Of course, there will be a [cost](https://mapsplatform.google.com/pricing) to using the Maps API as well.  It's got a pretty generous free-tier, depending on what you're using, just don't go crazy with it ;)


## Running the FastMCP server
```sh
fastmcp run server.py --transport stdio
```

You can substitute `stdio` with `streaming-http` or `sse` (deprecated) depending on your deployment method.


**NOTE:** if you use the `fastmcp` option, it ignores the `if __name__ == "__main__"`, so you need to pass `--transport` and any other settings you wish to override.


## Unit tests
```
pytest -v tests/
```

### Client test
Run server with:
```
fastmcp run server --transport streaming-http
```

Run client with:
```
python tests/client_list_tools.py
```

- sample output:
```console
[Tool found]: get_directions
[Tool found]: get_distance
[Tool found]: get_geocode
[Tool found]: find_place
[Tool found]: place_nearby
[Tool found]: place_details
```


## How to use/connect
### Agent Development Kit (ADK)
```python
model="gemini-2.5-flash"
google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY")


maps_agent = LlmAgent(
    name="maps_agent",
    model=model,
    instruction=(
        "You are an AI Google Maps assistant. Your primary function is to find places that meet the user's criteria. Include with your findings the name of the place, its rating, and its address. Limit the results to a maximum of 10. Use only the tools provided to you."
    ),
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='fastmcp',
                args=[
                    "run",
                    "maps_agent/server.py"
                ],
                env={
                    "GOOGLE_MAPS_API_KEY": google_maps_api_key
                },
            ),
            #tool_filter=['tool1', 'tool2']
        )

    ],
)
```

And here's a more detailed prompt example I give my agent:
```
MAPS_AGENT_PROMPT="""
System Role: You are an AI Google Maps assistant. Your primary function is to find places that meet the user's criteria. You achieve this by finding a list of places within a 4km radius of the user's location unless otherwise specified. Include with your findings the name of the place, its rating, and its address. Limit the results to a maximum of 10.

When asked for directions, provide the route we will be travelling via, total distance, total time and step-by-step directions in a list format.

If the user asks for "within walking distance", any nearby places returned should be within a 500m radius of the origin location.

Use only the tools provided to you.
"""
```
