# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application that displays Steam game playtime data. The application allows users to enter a Steam ID and view their gaming statistics in a web interface.

## Architecture

The project follows a simple Flask web application structure:

- **steam_data.py**: Main Flask application containing Steam API integration and web routes
- **templates/index.html**: Jinja2 template for the web interface
- **static/style.css**: CSS styling for the web interface

### Key Components

- **Steam API Integration**: Functions to fetch user info, game playtime data, and achievements from Steam Web API
- **Flask Web App**: Single route (`/`) that handles both GET (display form) and POST (process Steam ID lookup)
- **Data Processing**: Converts Steam API responses into structured data for web display

## Development Commands

### Running the Application
```bash
python steam_data.py
```
Note: Default port is 5000. If port 5000 is in use (common on macOS due to AirPlay), you may need to disable AirPlay Receiver or modify the app to use a different port.

### Python Environment
- Python 3.13.5
- Key dependencies: Flask, requests
- Full package list available via `pip freeze`

## API Configuration

The application uses the Steam Web API with:
- API key stored in `API_KEY` constant (steam_data.py:41)
- Default Steam ID for testing (steam_data.py:42)
- Supported endpoints defined in `POSSIBLE_DATA` dictionary (steam_data.py:43-50)

## Data Flow

1. User enters Steam ID via web form
2. Flask route processes the request
3. Steam API calls fetch user info and game data
4. Data is processed and sorted by playtime
5. Results are rendered in HTML template with game titles and hours played

## Security Notes

- Steam API key is currently hardcoded in the source code
- No input validation on Steam ID parameter
- No rate limiting implemented beyond basic API error handling