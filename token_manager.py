import os
from datetime import date

# kite connect gives a fresh access token each day after login
# this just saves it to a file so we dont have to login every time we restart

def get_access_token(kite, api_secret, token_file):
    if os.path.exists(token_file):
        with open(token_file) as f:
            lines = f.read().splitlines()
        if len(lines) == 2 and lines[0] == str(date.today()):
            kite.set_access_token(lines[1])
            print("Token loaded from file")
            return lines[1]

    # need fresh login
    print("Open this URL in browser and login:")
    print(kite.login_url())
    req_token = input("Paste request_token from redirect URL: ").strip()

    session = kite.generate_session(req_token, api_secret=api_secret)
    access_token = session["access_token"]

    with open(token_file, "w") as f:
        f.write(str(date.today()) + "\n" + access_token)

    print("Token saved.")
    return access_token
