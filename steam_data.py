"""
Flask web application for displaying Steam game playtime data.

This application provides a web interface for users to enter a Steam ID (numeric or vanity URL)
and view their gaming statistics including game titles and hours played.

Modules:
    - requests: For making HTTP requests to the Steam API.
    - logging: For debug and error logging.
    - datetime: For converting Unix timestamps to human-readable dates.
    - flask: For the web application framework.

Constants:
    - API_KEY (str): Steam Web API key for authentication.
    - STEAM_ID (str): Default Steam user ID for testing.
    - POSSIBLE_DATA (dict): Mapping of data types to their corresponding Steam API endpoints.

Functions:
    - get_data_from_api(url, params=None) -> dict:
        Fetches data from a specified API endpoint using a GET request.
        Handles rate limiting and JSON parsing errors.

    - get_playtime_data(steam_id=STEAM_ID, print_response: bool = False) -> dict:
        Fetches and processes playtime data for all owned games of a specified user.
        Returns a dictionary mapping appids to game data (title and hours).

    - get_user_info(steamid, print_response: bool = False) -> dict:
        Fetches user profile information from the Steam API.
        Handles both numeric Steam IDs and vanity URLs.
        Returns a dictionary containing user details.

    - get_achievements_from_game(appid: int, print_response: bool = False) -> dict:
        Fetches achievement data for a specific game.
        Returns a dictionary mapping achievement names to their status.

    - home() -> str:
        Flask route handler for the main page.
        Processes Steam ID input and renders the game playtime template.

Example Usage:
    Run the Flask app with `python steam_data.py` and navigate to http://localhost:5000
"""

from datetime import datetime, timezone
import logging
import requests
from flask import Flask, render_template, request


API_KEY = "4D564D7028D70C861936DCF1C09BC797"
STEAM_ID = "76561198839172366"  # r0mb0's Steam ID
POSSIBLE_DATA = {
    "user_info": "GetPlayerSummaries",
    "freinds": "GetFriendList",
    "achievements": "GetPlayerAchievements",
    "recent_games": "GetRecentlyPlayedGames",
    "owned_games": "GetOwnedGames",
    "game_details": "GetAppDetails",
}


def get_data_from_api(url, params=None) -> dict:
    """
    Fetches data from the specified API endpoint using a GET request.

    Args:
        url (str): The API endpoint URL.
        params (dict, optional): Dictionary of query string parameters to include in the request.
        Defaults to None.

    Returns:
        dict: The JSON response from the API as a dictionary. Returns an empty dictionary if a 429
        status code is encountered.

    Raises:
        Exception: If the response cannot be parsed as JSON, the exception is raised after printing
        the status code and response text.
    """
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 429:
        logging.warning(
            "Rate limit exceeded (429 Too Many Requests). Please wait and try again later."
        )
        return {}
    if response.status_code != 200:
        logging.error("Status code: %d", response.status_code)
        logging.error("Response text: %s", response.text)
        return {}
    try:
        data = response.json()
    except Exception:
        logging.error("Status code: %d", response.status_code)
        logging.error("Response text: %s", response.text)
        return {}
    return data


def get_playtime_data(steam_id=STEAM_ID, print_response: bool = False) -> dict:
    """
    Fetches and processes playtime data for games from the Steam API.

    Makes a GET request to the Steam Web API to retrieve owned games data for a specific user,
    sorts the games by total playtime in descending order, and returns a structured dictionary
    with game information.

    Args:
        steam_id (str, optional): The Steam ID to fetch playtime data for. Defaults to STEAM_ID.
        print_response (bool, optional): If True, prints each game's name and playtime in hours.
        Defaults to False.

    Returns:
        dict: A dictionary where keys are appids (int) and values are dictionaries containing:
            - 'title' (str): Game name or appid as string if name unavailable
            - 'hours' (float): Total playtime in hours, rounded to 2 decimal places

    Note:
        Returns empty dict if API request fails or no games data is found.
    """
    params = {
        "key": API_KEY,
        "steamid": steam_id,
        "format": "json",
        "include_appinfo": True,
    }
    logging.debug("Making API call with steamid: %s", steam_id)
    logging.debug("API params: %s", params)
    data = get_data_from_api(
        url="https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/",
        params=params,
    )
    logging.debug("Playtime API response: %s", data)
    if not data or "response" not in data or "games" not in data["response"]:
        logging.debug(
            "No games data found. Response keys: %s",
            data.keys() if data else "No data",
        )
        return {}
    sorted_games = sorted(
        data["response"]["games"], key=lambda x: x["playtime_forever"], reverse=True
    )
    play_time = {}
    for game in sorted_games:
        play_time[game.get("appid")] = {
            "title": game.get("name", str(game["appid"])),
            "hours": round(game["playtime_forever"] / 60, 2),
        }
    if print_response:
        for game_data in play_time.values():
            logging.info("%s: %s hours", game_data["title"], game_data["hours"])
    return play_time


def get_user_info(steamid, print_response: bool = False) -> dict:
    """
    Fetches user information from the Steam API.

    Handles both numeric Steam IDs and vanity URLs. If a vanity URL is provided,
    it first resolves it to a numeric Steam ID before fetching user information.

    Args:
        steamid (str): The Steam ID (numeric) or vanity URL to fetch information for.
        print_response (bool, optional): If True, prints user information to console.
        Defaults to False.

    Returns:
        dict: A dictionary containing user information such as personaname, avatar,
        profile URL, and last logoff time. Returns {'personaname': 'Invalid Steam ID'}
        if the Steam ID cannot be resolved or found.
    """
    if isinstance(steamid, str) and not steamid.isdigit():
        params = {"key": API_KEY, "vanityurl": steamid, "format": "json"}
        response = get_data_from_api(
            "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/",
            params=params,
        )
        logging.debug("Vanity URL response for '%s': %s", steamid, response)
        if (
            not response
            or "response" not in response
            or "steamid" not in response["response"]
        ):
            logging.debug("Failed to resolve vanity URL")
            return {"personaname": "Invalid Steam ID"}
        steamid = response["response"]["steamid"]
        logging.debug("Resolved to Steam ID: %s", steamid)
    params = {
        "key": API_KEY,
        "steamids": steamid,
        "format": "json",
    }
    data = get_data_from_api(
        url="http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
        params=params,
    )
    if (
        not data
        or "response" not in data
        or "players" not in data["response"]
        or not data["response"]["players"]
    ):
        return {"personaname": "Invalid Steam ID"}
    for info in data["response"]["players"][0]:
        if print_response:
            logging.info("%s: %s", info, data["response"]["players"][0][info])
    return data["response"]["players"][0]


def get_achievements_from_game(appid: int, print_response: bool = False) -> dict:
    """
    Fetches and returns the achievement status for a specific Steam game.

    Uses the hardcoded STEAM_ID constant to fetch achievements for the default user.

    Args:
        appid (int): The Steam App ID of the game to retrieve achievements for.
        print_response (bool, optional): If True, prints the achievement statuses to the console.
        Defaults to False.

    Returns:
        dict: A dictionary mapping achievement names (with underscores replaced by spaces) to their
        status. The status is either "Achieved on <date>" if unlocked, or "Not Achieved" otherwise.

    Note:
        This function uses the global STEAM_ID constant and does not accept a steamid parameter.
    """
    achievements = get_data_from_api(
        url="http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/",
        params={
            "appid": appid,
            "key": API_KEY,
            "steamid": STEAM_ID,
            "format": "json",
        },
    )["playerstats"]["achievements"]
    achievement_status = {}
    for achievement in achievements:
        achievement_status[achievement["apiname"].replace("_", " ")] = (
            f"Achieved on {datetime.fromtimestamp(achievement["unlocktime"],
                                                  tz=timezone.utc).strftime("%B %-d, %Y")}"
            if achievement["achieved"]
            else "Not Achieved"
        )
    if print_response:
        logging.info("Achievements for appid %d:", appid)
        for name, status in achievement_status.items():
            logging.info("%s: %s", name, status)
    return achievement_status


# --- Flask Web App ---
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Flask route handler for the main page.

    Handles both GET and POST requests. Processes Steam ID from query parameters,
    fetches user information and playtime data, and renders the template.

    Query Parameters:
        steamid (str, optional): Steam ID (numeric) or vanity URL to lookup.

    Returns:
        str: Rendered HTML template with user data and game playtime information.
        If no steamid is provided, shows an empty form.
    """
    steamid = request.args.get("steamid")
    if steamid:
        # Only fetch data if a steamid is provided
        user_info = get_user_info(steamid)
        user_name = user_info.get("personaname", "Unknown User")

        # Get the resolved steamid from user_info if it was converted from vanity URL
        resolved_steamid = steamid
        if isinstance(steamid, str) and not steamid.isdigit():
            # This was a vanity URL, we need to resolve it for playtime data
            params = {"key": API_KEY, "vanityurl": steamid, "format": "json"}
            response = get_data_from_api(
                "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/",
                params=params,
            )
            if (
                response
                and "response" in response
                and "steamid" in response["response"]
            ):
                resolved_steamid = response["response"]["steamid"]

        playtime_data = get_playtime_data(resolved_steamid)
        games = playtime_data.values()
        header_message = f"Steam Game Playtime For {user_name}"
    else:
        # No steamid provided, show empty form
        user_name = "Enter a Steam ID"
        games = []
        steamid = ""
        header_message = "Steam Game Playtime"

    return render_template(
        "index.html",
        games=games,
        user_name=user_name,
        steamid=steamid,
        header_message=header_message,
    )


if __name__ == "__main__":
    app.run(debug=False)
