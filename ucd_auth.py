import datetime
from getpass import getpass
import base64
import os
import requests

token_file = ".ucdToken"
token_user = 'PasswordIsAuthToken'
time_format = "%m-%d-%Y-%H:%M"


def get_exp_time():
    current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    etime = current_time.strftime(time_format)
    return etime


def generate_token(base_url):
    user = input("Enter UCD username: ")
    passwd = getpass("Enter UCD password: ")
    creds = base64.b64encode(("{}:{}".format(user, passwd)).encode())
    uri = '{}cli/teamsecurity/tokens?user={}&expireDate={}'.format(base_url, user, get_exp_time())
    headers = {
        'Authorization': 'Basic ' + creds.decode('ascii'),
        'Accept': 'application/json'
    }
    r = requests.put(uri, headers=headers, verify=False)
    obj = r.json()['token']
    token_str = base64.b64encode(obj.encode()).decode('ascii')
    token = base64.b64decode(token_str)
    print('INFO: writing token to file "{}"'.format(token_file))
    with open(token_file, 'w') as file:
        file.write(token_str)
    return token


def try_token(base_url, token):
    uri = '{}cli/status/getStatuses?type=snapshot'.format(base_url)
    req_headers = {
        'Accept': 'application/json'
    }
    req = requests.get(uri, auth=(token_user, token), headers=req_headers, verify=False)
    if req.status_code == 401:
        print('INFO: token from file is invalid...')
        return False
    else:
        return True


def get_token(base_url):
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            f_lines = f.readlines()
            token = base64.b64decode(f_lines[0])
            if not try_token(base_url, token):
                print('INFO: Creating new token....\n')
                token = generate_token(base_url)
    else:
        print('INFO: token file not found, generating token...')
        token = generate_token(base_url)
    return token
