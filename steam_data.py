"""
This script interacts with the Steam Web API to fetch and process user and game data.

Modules:
    - requests: For making HTTP requests to the Steam API.
    - json: For handling JSON data.
    - datetime: For converting Unix timestamps to human-readable dates.

Constants:
    - API_KEY (str): Steam Web API key for authentication.
    - STEAM_ID (str): The Steam user ID to fetch data for.
    - POSSIBLE_DATA (dict): Mapping of data types to their corresponding Steam API endpoints.

Functions:
    - get_data_from_api(url, params=None) -> dict:
        Fetches data from a specified API endpoint using a GET request.
        Handles rate limiting and JSON parsing errors.

    - get_playtime_data(print_response: bool = False) -> dict:
        Fetches and processes playtime data for all owned games of the user.
        Returns a dictionary mapping game names (or appids) to playtime in hours.
        Optionally prints the playtime data.

    - get_user_info(print_response: bool = False) -> dict:
        Fetches user profile information from the Steam API.
        Returns a dictionary containing user details.
        Optionally prints the user information.

    - unix_to_datetime(unix_timestamp: int) -> datetime:
        Converts a Unix timestamp (seconds since epoch) to a Python datetime object (UTC).

Example Usage:
    Call get_playtime_data(True) to print and retrieve playtime data for the specified user.
"""

from datetime import datetime, timezone
import requests


API_KEY = "4D564D7028D70C861936DCF1C09BC797"
STEAM_ID = "76561198839172366"
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
        print(
            "Error: Rate limit exceeded (429 Too Many Requests). Please wait and try again later."
        )
        return {}
    try:
        data = response.json()
    except Exception:
        print("Status code:", response.status_code)
        print("Response text:", response.text)
        raise
    return data


def get_playtime_data(print_response: bool = False) -> dict:
    """
    Fetches and processes playtime data for games from a remote API.

    Makes a GET request to the specified URL with given parameters, parses the JSON response,
    sorts the games by total playtime in ascending order, and returns a dictionary mapping
    each game's name (or appid if the name is unavailable) to its total playtime in hours.

    Args:
        print_response (bool, optional): If True, prints each game's name and playtime in hours.
        Defaults to False.

    Returns:
        dict: A dictionary where keys are game names (or appids) and values are playtime in hours
        (float).

    Raises:
        Exception: If the response cannot be parsed as JSON, prints the status code and response
        text, then re-raises the exception.
    """
    params = {
        "key": API_KEY,
        "steamid": STEAM_ID,
        "format": "json",
        "include_appinfo": True,
    }
    data = get_data_from_api(
        url="http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/",
        params=params,
    )
    sorted_games = sorted(
        data["response"]["games"], key=lambda x: x["playtime_forever"], reverse=False
    )
    play_time = {}
    for game in sorted_games:
        play_time[game.get("appid")] = {
            "title": game.get("name", str(game["appid"])),
            "hours": round(game["playtime_forever"] / 60, 2),
        }
    if print_response:
        for game_data in play_time.values():
            print(f"{game_data['title']}: {game_data['hours']} hours")
    return play_time


def get_user_info(print_response: bool = False) -> dict:
    """
    Fetches user information from the Steam API.

    Returns:
        dict: A dictionary containing user information such as avatar, profile URL, and last logoff
        time.
    """
    params = {
        "key": API_KEY,
        "steamids": STEAM_ID,
        "format": "json",
    }
    data = get_data_from_api(
        url="http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
        params=params,
    )
    for info in data["response"]["players"][0]:
        if print_response:
            print(f"{info}: {data["response"]["players"][0][info]}")
    return data["response"]["players"][0]


def get_achievements_from_game(appid: int, print_response: bool = False) -> dict:
    """
    Fetches and returns the achievement status for a specific Steam game.

    Args:
        appid (int): The Steam App ID of the game to retrieve achievements for.
        print_response (bool, optional): If True, prints the achievement statuses to the console.
        Defaults to False.

    Returns:
        dict: A dictionary mapping achievement names (with underscores replaced by spaces) to their
        status.
              The status is either "Achieved on <date>" if unlocked, or "Not Achieved" otherwise.
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
            f"Achieved on {unix_to_datetime(achievement["unlocktime"])}"
            if achievement["achieved"]
            else "Not Achieved"
        )
    if print_response:
        print(f"Achievements for appid {appid}:")
        for name, status in achievement_status.items():
            print(f"{name}: {status}")
    return achievement_status


def unix_to_datetime(unix_timestamp: int) -> str:
    """
    Converts a Unix timestamp (seconds since epoch) to a human-readable date string
    (UTC, e.g., March 5, 2024).

    Args:
        unix_timestamp (int): The Unix timestamp to convert.

    Returns:
        str: The corresponding date string in UTC.
    """
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).strftime(
        "%B %-d, %Y"
    )


get_achievements_from_game(1172380, True)
