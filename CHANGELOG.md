# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [0.2.0] - 2025-10-07
### Added
- `fastmcp.json` to adhere to changes in FastMCP module updates
### Changed
- Updated `fastmcp` from `>= 2.9.0` to `>= 2.12.4`
- Updated `mcp` from `== 1.9.4` to `== 1.16.0`

## [0.1.0] - 2025-07-01 - Happy birthday, Canada!
### Added
- Unit tests via `pytest` in `tests/test_server.py` (thanks, [Jules](https://jules.google/)!)
- FastMCP client test in `tests/client_list_tools.py`
- Additional error handling in `server.py` (also recommended by Jules)
- `pytest` and `pytest-asyncio` to `requirements.txt`

## [0.0.2] - 2025-06-24
### Added
- Tools: `get_geocode`, `get_distance`
### Changed
- Made function tools `async`
### Removed
- Helper function: `strip_html_regex()` function as the agent will interpret and format the text accordingly

## [0.0.1] - 2025-06-23
### Added
- Initial commit
- Tools: `get_directions`, `find_place`, `place_nearby`, `place_details`
