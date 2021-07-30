import hashlib
import json
from ucd_auth import get_token
import urllib3
import requests
from urllib.parse import quote_plus
import glob
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
import argparse
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

user = 'PasswordIsAuthToken'
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
ucd_url_suffix = {
    'create_version': 'cli/version/createVersion?component={}&name={}&description={}',
    'get_version_id': 'cli/version/getVersionId?component={}&version={}',
    'add_version_files': 'cli-internal/version/addVersionFilesFull'
}


def get_digest(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)


def get_metadata(file):
    if os.path.isfile(file):
        f_type = 'REGULAR'
    elif os.path.islink(file):
        f_type = 'LINK'
    else:
        f_type = None
        print('ERROR: Unknown file type...')
        exit(1)
    return json.dumps({
        'path': os.path.basename(file),
        'contentHash': 'SHA-256{{{0}}}'.format(get_digest(file)),
        'version': 1,
        'type': f_type,
        'length': os.path.getsize(file),
        'modified': int(1000 * os.path.getmtime(file))
    }).encode()


def create_component_version(base_url, component, version, description=''):
    version_id = get_version_id(base_url, component, version)
    if version_id:
        print('ERROR: Version "{}" for component "{}" already exist!'.format(version, component))
        exit(1)
    req_url = base_url + ucd_url_suffix['create_version'].format(component, version, quote_plus(description))
    print(' INFO: creating "{}" version for component "{}"...'.format(version, component))
    req = requests.post(req_url, auth=(user, token), headers=headers, verify=False)
    if req.status_code == 200:
        return req.content.decode()
    else:
        print('ERROR: Error creating version "{}" for component "{}"...'.format(version, component))
        print("ERROR: Server reply: {}".format(req.content.decode()))
        exit(1)


def add_ver_files_api(base_url, component, version, base_folder):
    files_list = glob.glob('{}/*'.format(base_folder))
    print(files_list)
    if len(files_list) == 0:
        print('INFO: No files to add from {}, exiting...'.format(base_folder))
        exit(0)
    print('INFO: Adding files "{}" into version "{}" for component {}...'.format(
        glob.glob('{}/*'.format(base_folder)), version, component))
    req_url = base_url + ucd_url_suffix['add_version_files']
    for file in files_list:
        print('INFO: Adding Tile {} into "{}" vension for component "{}"...'.format(file, version, component))
        file_lister_fields = {
            'component': component,
            'version': version,
            'entryMetadata': get_metadata(file),
            'entryContent-{}'.format(get_digest(file)): (os.path.basename(file), open(file, 'rb'),
                                                         'application/octet-stream')
        }
        mp_encoder = MultipartEncoder(fields=file_lister_fields)
        print('INF0: File metadata:\n{}'.format(
            json.dumps(json.loads(file_lister_fields['entryMetadata'].decode(), indent=4))))
        req_headers = {'Content-Type': mp_encoder.content_type}
        req = requests.post(req_url, auth=(user, token), data=mp_encoder, headers=req_headers, verify=False)
        if req.status_code == 204:
            print('INFO: File "{}" was uploaded successfully...'.format(file))
        else:
            print('ERROR: Error adding files into version "{}" fon component "{}"...'.format(version, component))
            print('ERROR: Server reply: {}, code: {}'.format(req.content.decode(), req.status_code))
            exit(1)


def get_version_id(base_url, component, version):
    req_url = base_url + ucd_url_suffix['get_version_id'].format(component, version)
    req = requests.get(req_url, auth=(user, token), headers={"Accept": "text/plain"}, verify=False)
    http_code = req.status_code
    if http_code == 200:
        return req.content.decode()
    else:
        print('INFO: Cannot find version "{}" for component "{}"'.format(version, component))
    return None


parser = argparse.ArgumentParser()
parser.add_argument('--base_url', help='UCD server base url: https://server:port/', type=str)
parser.add_argument('--component', help='UCD component name', type=str)
parser.add_argument('--version', help='UCD component version name', type=str)
parser.add_argument('--description', help='UCD component version description', type=str, default='')
parser.add_argument('--base_folder', help='Base folder to upload to version', type=Path)
args = parser.parse_args()

token = get_token(args.base_url)

version_request = create_component_version(args.base_url, args.component, args.version, args.description)
version_name = json.loads(version_request)['name']
add_ver_files_api(args.base_url, args.component, version_name, args.base_folder)

