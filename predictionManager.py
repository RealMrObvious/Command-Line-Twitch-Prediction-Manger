import requests, webbrowser, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

# === Constants ===
# Should match the info in your twitch dev application
CLIENT_ID = ''
CLIENT_SECRET = ''
PORT = 3000
REDIRECT_URI = f'http://localhost:{str(PORT)}'

# Broadcaster ID of your twitch account
BROADCASTER_ID = ''

# Path to the root of the TSH Folder
TSH_FOLDER = ""

SCOPES = 'channel:manage:predictions'
STATE = 'unique_state_string'

# =================

# === OAuth Handler ===
class OAuthRedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get("code", [None])[0]

        if code:
            # print(f"\n Authorization code received: {code}")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body onload='setTimeout(function() { window.close() }, 0);'><h1>Authorization complete. You may close this window.</h1></body></html>")

            self.server.auth_code = code
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Error: No authorization code received.</h1></body></html>")


# === Auth URL ===
def generate_auth_url(client_id, redirect_uri, scopes, state):
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scopes,
        'state': state
    }
    return f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"


# === Token Exchange ===
def get_user_oauth_token(client_id, client_secret, redirect_uri, auth_code):
    token_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=params)
    response.raise_for_status()
    token_data = response.json()
    return token_data['access_token'], token_data.get('refresh_token')


# === Player Fetching ===
# Reads the text file in TSH to get the player name
def getPlayer(p):
    if 0 < p < 3:
        path = f'{TSH_FOLDER}/out/score/1/team/{p}/player/1/mergedOnlyName.txt'
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "Player"


# === Main App ===
if __name__ == "__main__":

    #Generartes and opens a tab for you to login with your twitch account 
    auth_url = generate_auth_url(CLIENT_ID, REDIRECT_URI, SCOPES, STATE)
    webbrowser.open(auth_url)

    # Local server to get the auth code.
    server = HTTPServer(("localhost", PORT), OAuthRedirectHandler)
    print(f"Local server started at http://localhost:{PORT}/")
    server.auth_code = None
    server.serve_forever()
    server.server_close()

    auth_code = server.auth_code
    if not auth_code:
        print("No authorization code received.")
        exit(1)

    # Exchange code for token
    token, refresh_token = get_user_oauth_token(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, auth_code)

    # === Main Menu ===
    player1 = getPlayer(1)
    player2 = getPlayer(2)

    prediction_id = None
    submissions_ended = False

    while True:
        print("\nTwitch Prediction Menu\n========================")
        print("0. Reload Player Data")      # from the text files
        print(f"1. Start Prediction ({player1} vs {player2})")
        print("2. Cancel Prediction")

        choice = input("Select an option (0, 1, 2): ").strip()

        if choice == '0':
            player1 = getPlayer(1)
            player2 = getPlayer(2)

        elif choice == '1':
            json_data = {
                'broadcaster_id': BROADCASTER_ID,
                'title': f'Who will win? {player1} vs {player2}',
                'outcomes': [
                    {'title': player1},
                    {'title': player2},
                ],
                'prediction_window': 45,
            }

            headers = {
                'Client-ID': CLIENT_ID,
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }

            response = requests.post('https://api.twitch.tv/helix/predictions', headers=headers, json=json_data)
            data = response.json()

            if "status" in data and data["status"] == 400:
                print(f"Error: {data.get('message')}")
                continue

            prediction = data["data"][0]
            prediction_id = prediction["id"]
            outcome_ids = [o["id"] for o in prediction["outcomes"]]
            submissions_ended = False
            print("Prediction started!")

            # === Submenu for controlling prediction ===
            while True:
                print("\n--- Prediction Control ---")
                if not submissions_ended:
                    print("0. Lock Submissions")
                print(f"1. Set Winner: {player1}")
                print(f"2. Set Winner: {player2}")
                print("3. Cancel Prediction")
                print("4. Exit to Main Menu")

                action = input("Choose: ").strip()

                if action == "0" and not submissions_ended:
                    url = f'https://api.twitch.tv/helix/predictions?broadcaster_id={BROADCASTER_ID}&id={prediction_id}&status=LOCKED'
                    res = requests.patch(url, headers=headers)
                    if res.status_code == 200:
                        submissions_ended = True
                        print("Submissions locked.")
                    else:
                        print("Failed to lock submissions.")

                elif action in ["1", "2"]:
                    win_id = outcome_ids[int(action) - 1]
                    url = f'https://api.twitch.tv/helix/predictions?broadcaster_id={BROADCASTER_ID}&id={prediction_id}&status=RESOLVED&winning_outcome_id={win_id}'
                    res = requests.patch(url, headers=headers)
                    if res.status_code == 200:
                        print(f"Winner Selected: {player1 if action == '1' else player2} wins!")
                    else:
                        print("Failed to resolve prediction.")
                    
                    break

                elif action == "3":
                    url = f'https://api.twitch.tv/helix/predictions?broadcaster_id={BROADCASTER_ID}&id={prediction_id}&status=CANCELED'
                    res = requests.patch(url, headers=headers)
                    if res.status_code == 200:
                        print("Prediction cancelled.")
                    else:
                        print("Failed to cancel prediction.")
                    
                    break

                elif action == "4":
                    break
                else:
                    print("Invalid input.")

        elif choice == '2' and prediction_id:
            url = f'https://api.twitch.tv/helix/predictions?broadcaster_id={BROADCASTER_ID}&id={prediction_id}&status=CANCELED'
            res = requests.patch(url, headers=headers)
            if res.status_code == 200:
                print("Prediction cancelled.")
            else:
                print("Failed to cancel prediction.")

        elif choice == '3':
            print("Exiting...")
            break

        else:
            print("Invalid option. Please try again.")
