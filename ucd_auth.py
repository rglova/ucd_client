import base64
from datetime import timedelta, datetime
from getpass import getpass
import requests
import os

# Global vars
token_file = ".ucdToken"
ctime = datetime.now()
time_format = "%m-%d-%Y-%H:%M"


def generate_token(base_url):
    user = input('Enter UCD username: ')
    passwd = getpass('Enter UCD password: ')
    creds = base64.b64encode(("{}: {}".format(user, passwd)).encode())
    etime = get_exp_time()
    uri = '{}/cli/teamsecurity/tokens?user={}&expireDate={}'.format(base_url, user, etime)
    headers = {'Authorization': 'Basic ' + creds.decode('ascii'), 'Accept': 'application/json'}
    r = requests.put(uri, headers=headers, verify=False)
    obj = r.json()['token']
    token = base64.b64encode(obj.encode()).decode('ascii')
    with open(token_file, 'w') as file:
        file.write(token + "\n" + etime)
    return token


def get_exp_time():
    current_time = ctime + timedelta(hours=8)
    etime = current_time.strftime(time_format)
    return etime


def is_token_valid(etime):
    current_time = ctime.strftime(time_format)
    if current_time < etime:
        return True
    else:
        return False


def get_token(base_url):
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            f_lines = f.readlines()
            etime = f_lines[1].decode('ascii')
            token = base64.b64decode(f_lines[0])
            if not is_token_valid(etime):
                print('INFO: Token is not valid, creating token...')
                token = generate_token(base_url)
    else:
        token = generate_token(base_url)
    return token
