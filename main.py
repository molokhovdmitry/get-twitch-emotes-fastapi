import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


# Function to get a new access token
def get_access_token():
    global ACCESS_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': CLIENT_ID,
        'client_secret': SECRET,
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail=response.json())

    token_info = response.json()
    ACCESS_TOKEN = token_info['access_token']

    # Update the ACCESS_TOKEN in .env file
    with open('.env', 'r') as file:
        lines = file.readlines()

    with open('.env', 'w') as file:
        for line in lines:
            if line.startswith("ACCESS_TOKEN"):
                file.write(f"ACCESS_TOKEN={ACCESS_TOKEN}\n")
            else:
                file.write(line)


# Function to get user ID
def get_user_id(username: str):
    global ACCESS_TOKEN
    if not ACCESS_TOKEN:
        get_access_token()

    base_url = "https://api.twitch.tv/helix/"
    endpoint = "users"
    url = base_url + endpoint

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Client-Id': CLIENT_ID
    }
    params = {'login': username}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail=response.json())

    user_data = response.json()
    if not user_data['data']:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user_data['data'][0]['id']
    return user_id


# Endpoint to get emotes from 7tv
@app.get("/getUser/{username}")
def api_get_stv_user_emotes(username: str):
    base_url = "https://7tv.io/v3/users/twitch/"
    user_id = get_user_id(username)
    url = base_url + user_id
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail=response.json())

    user_info = response.json()

    emotes = {
        emote['name']: 'https:' + emote['data']['host']['url'] + '/4x.webp'
        for emote in user_info['emote_set']['emotes']
        if emote['flags'] == 0}  # Filter zero-width emotes out

    return emotes
