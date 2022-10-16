import os
import socket
import subprocess
import platform
import logging
import configparser
import threading
import requests
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
from waitress import serve

CONFIG = os.path.join(os.path.dirname(__file__), 'config.ini')
if not os.path.exists(CONFIG):
    logging.info('No config file found')
    quit()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
config = configparser.ConfigParser()
config.read(CONFIG)

MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'static/media')
PLAYLIST = os.path.join(MEDIA_DIR, 'playlist.m3u')
APP_PORT = config.getint('default', 'app_port')
MEDIA_EXTENSIONS = tuple(config.get('default', 'media_extensions').split())
NAME_MAX_CHAR = config.getint('default', 'name_max_char')
DEBUG = config.getboolean('default', 'debug')
VLC_HOST = config.get('vlc_rc', 'host').replace(' ', '')
VLC_PORT = config.getint('vlc_rc', 'port')
VLC_OPTIONS = tuple(config.get('vlc_rc', 'options').split())


def get_dir_size(path: str, units: int = 0) -> int | float:
    '''Return folder size (in bytes by default)

        units: int [optional]
            1 - KiB, 2 - MiB, 3 - GiB, 4 - TiB
    '''
    size = 0
    if os.path.isdir(path):
        for file in os.scandir(path):
            try:
                size += os.path.getsize(file)
            except OSError:
                logging.error(f'Get dir size: cant get {file}')

    if 0 < units < 5:
        size = size / 1024 ** units
    return size


def get_from_dir(path: str, extensions: list = None) -> list:
    '''Return list of files for given directory'''
    files = []
    if os.path.isdir(path):
        if extensions:
            for file in os.scandir(path):
                if file.name.endswith(extensions):
                    files.append(file.name)
        else:
            for file in os.scandir(path):
                files.append(file.name)
    return sorted(files)


def save_to_dir(list: list, path: str) -> None:
    if os.path.isdir(path):
        for file in list:
            file.save(os.path.join(
                path, secure_filename(file.filename)))
        logging.info(f'{len(list)} file(s) uploaded')
    else:
        logging.error('Save to dir: wrong path')


def remove_from_dir(list: list, path: str) -> None:
    if os.path.isdir(path):
        for element in list:
            for file in os.scandir(path):
                error = True
                if file.name == secure_filename(element):
                    while error:
                        try:
                            os.remove(file.path)
                        except:
                            pass
                        else:
                            error = False
        logging.info(f'{len(list)} file(s) removed')
    else:
        logging.error('Remove from dir: wrong path')


def create_playlist(list: list, path: str) -> None:
    '''Create playlist

        list: list
            list of files to add to a playlist

        path: str
            where to save playlist
    '''
    with open(path, 'w') as file:
        file.write('#EXTM3U\n')
        for media in list:
            file.write(f'{media}\n')
    logging.info('Playlist created')


def get_playlist_files(path: str) -> list:
    '''Return playlist content'''
    playlist = []
    try:
        if path and os.stat(path).st_size != 0:
            with open(path, 'r') as file:
                playlist = file.read().splitlines()
            playlist.pop(0)
    except OSError as error:
        logging.error(error)
    return playlist


def update_config() -> None:
    with open(CONFIG, 'w') as file:
        config.write(file)
    logging.info('CONFIG updated')


def vlc_rc(command: str, host: str = VLC_HOST, port: int = VLC_PORT) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(command.encode())
        s.close()
        logging.info(f'VLC RC: {command}')
        return True
    except OSError as error:
        logging.error(f'VLC RC: {error}')
        return False


def machine_control(command: str) -> bool:
    system = platform.system()
    match command:
        case 'shutdown':
            if system == 'Windows':
                subprocess.run(['shutdown', '/s', '/t', '0'])
            if system == 'Linux':
                subprocess.run(['sudo', 'shutdown', 'now'])
        case 'reboot':
            if system == 'Windows':
                subprocess.run(['shutdown', '/r', '/t', '0'])
            if system == 'Linux':
                subprocess.run(['sudo', 'shutdown', '-r', 'now'])
        case 'hostname':
            hostname = os.path.join(
                os.path.dirname(__file__), 'scripts/hostname')
            if os.path.isfile(hostname):
                os.remove(hostname)
                logging.info(f'Machine control: hostname file removed')
            else:
                logging.info(f"Machine control: hostname file doesn't exist")
        case _:
            return False
    logging.info(f'Machine control: {command} performed')
    return True


def control_request(node: str, query: str) -> None:
    block_list = (f'{socket.gethostname()}:{APP_PORT}',
                  f'{socket.gethostbyname(socket.gethostname())}:{APP_PORT}',
                  f'localhost:{APP_PORT}', f'127.0.0.1:{APP_PORT}')
    url = f'http://{node}{query}'

    try:
        if node not in block_list:
            requests.get(url)
    except requests.exceptions.ConnectionError:
        logging.error(f'Control request: cannot reach {node}')


def control_remote_nodes(node_list: str) -> None:
    node_list = tuple(filter(lambda rn: rn != '', node_list.split(' ')))

    if node_list:
        for node in node_list:
            t = threading.Thread(
                target=control_request, args=(node, request.full_path))
            t.start()


def control_playback(functions: list, args: list) -> None:
    '''
        If player is on, stop playback, clear playlist call functions and play playlist
        If player is off, call functions
    '''
    if vlc_rc('status'):
        vlc_rc('stop')
        vlc_rc('clear')
        for function in functions:
            index = functions.index(function)
            function(*args[index])
        vlc_rc(f'add {PLAYLIST}')
    else:
        for function in functions:
            index = functions.index(function)
            function(*args[index])


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html',
                           node_name=config.get('default', 'node_name'),
                           hostname=socket.gethostname(),
                           name_max_char=NAME_MAX_CHAR,
                           media_extensions=MEDIA_EXTENSIONS,
                           used_space=get_dir_size(MEDIA_DIR, 2),
                           volume=config.get('vlc_rc', 'volume'),
                           module=config.get('vlc_rc', 'module'),
                           options=config.get('vlc_rc', 'options').split(),
                           remote_nodes=config.get('vlc_rc', 'remote_nodes'),
                           playlist=get_playlist_files(PLAYLIST))


@app.route('/info/<query>', methods=['GET', 'POST'])
@cross_origin()
def info_handler(query):
    match request.method:
        case 'GET':
            match query:
                case 'name':
                    return config.get('default', 'node_name')
                case 'used-space':
                    return str(get_dir_size(MEDIA_DIR, 2))
            return 'wrong query', 404
        case 'POST':
            match query:
                case 'name':
                    string = request.data.decode()
                    if len(string) <= NAME_MAX_CHAR:
                        config.set('default', 'node_name', string)
                        update_config()
                        return 'name was updated'
                    else:
                        return config.get('default', 'node_name'), 400
            return 'wrong query', 404


@app.route('/machine-control/<command>')
@cross_origin()
def machine_control_handler(command):
    if machine_control(command):
        return f'{command} performed'
    else:
        return 'wrong command', 400


@app.route('/player-settings/<query>', methods=['GET', 'POST'])
def player_handler(query):
    match request.method:
        case 'GET':
            match query:
                case 'volume' | 'module' | 'options':
                    return config.get('vlc_rc', query)
                case 'remote-nodes':
                    return {'addresses': config.get('vlc_rc', 'remote_nodes').split()}
            return 'wrong query', 404
        case 'POST':
            result = None
            data = request.get_json()
            if not 'value' in data:
                return 'no value', 404

            match query:
                case 'volume':
                    if type(data['value']) != int or 0 < data['value'] > 320:
                        return 'wrong value', 400

                    vlc_rc(f"{query} {data['value']}")
                    result = ['volume', str(data['value'])]
                case 'module':
                    m_list = ('any', 'gles2')
                    if data['value'] not in m_list:
                        return 'wrong value', 400

                    result = ['module', str(data['value'])]
                case 'options':
                    o_list = ('', '-L', '-R')
                    if type(data['value']) is list:
                        for option in data['value']:
                            if option not in o_list:
                                return 'wrong value', 400
                        result = ['options', ' '.join(data['value'])]
                    else:
                        return 'wrong value', 400
                case 'remote-nodes':
                    if type(data['value']) is list:
                        for address in data['value']:
                            if type(address) != str:
                                return 'wrong value', 400
                        result = ['remote_nodes', ' '.join(data['value'])]
                    else:
                        return 'wrong value', 400
                case _:
                    return 'wrong query', 404

            config.set('vlc_rc', result[0], result[1])
            update_config()
            return f'settings applied - {query}'


@app.route('/playlist', methods=['GET', 'POST'])
@cross_origin()
def playlist_handler():
    match request.method:
        case 'GET':
            list = ('play', 'stop', 'prev', 'next', 'goto', 'quit')
            command = request.args.get('command')

            if command:
                if not vlc_rc('status'):
                    return 'player is off', 503

                if command not in list:
                    return 'no command found', 400

                match command:
                    case 'goto':
                        value = request.args.get('value')
                        if value:
                            vlc_rc(f'{command} {value}')
                        else:
                            return 'wrong value', 400
                    case _:
                        vlc_rc(command)

                control_remote_nodes(config.get('vlc_rc', 'remote_nodes'))
                return f'{command} - success'
            else:
                return {'playlist': get_playlist_files(PLAYLIST)}
        case 'POST':
            control_playback([create_playlist], [
                             [request.get_json(), PLAYLIST]])
            return 'playlist created'


@ app.route('/media', methods=['GET', 'POST', 'DELETE'])
def media_handler():
    match request.method:
        # Upload media and create playlist
        case 'POST':
            if 'media' not in request.files:
                return 'no media files', 204

            save_to_dir(request.files.getlist('media'), MEDIA_DIR)
            control_playback([create_playlist], [
                             [get_from_dir(MEDIA_DIR, MEDIA_EXTENSIONS), PLAYLIST]])
            return 'upload is done', 201

        # Remove media and create playlist
        case 'DELETE':
            list = request.get_json()
            if list:
                control_playback([remove_from_dir], [[list, MEDIA_DIR]])
                control_playback([create_playlist], [
                                 [get_from_dir(MEDIA_DIR, MEDIA_EXTENSIONS), PLAYLIST]])
            return 'delete done'


# Set volume level at start
if vlc_rc('status'):
    vlc_rc(f'volume { config.get("vlc_rc", "volume") }')

if DEBUG:
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
else:
    serve(app, host='0.0.0.0', port=APP_PORT)
