from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
from mods.routers import basic_app_file
from mods.utils import STATUS_OK, get_value_with_check, failed_with_explain
from mods.usrp_server.server import USRPServers
from mods.skg.client import SKGClient
import requests

app = Flask(__name__)

## Register basic app file (router for index.html and static files).
app.register_blueprint(basic_app_file)

## This is required by flask_socketio, don't touch it.
app.config['SECRET_KEY'] = 'secret!'

cors = CORS(app)
socketio = SocketIO(app)

## Auto reload the template, so we don't have to restart
## the server every time.
app.config['TEMPLATES_AUTO_RELOAD'] = True

usrp_servers = USRPServers()
skg_client = SKGClient(usrp_servers, socketio, app)

## This routine is for testing the connection.
@socketio.on("connect")
def connected():
    print("websocket connected, with socket.id='{}'".format(request.sid))

## This routine is for testing the connection with the usrp_server.
@socketio.on("usrp_server_ping")
def usrp_server_test_connection(req):
    addr, ok = get_value_with_check(req, "usrp_server_addr")
    if not ok:
        return failed_with_explain(addr)
    pong = usrp_servers.ping(addr)
    if pong != "pong":
        return failed_with_explain("Cannot connect to usrp server: {}".format(addr))
    return STATUS_OK

## This routine is for loading the configuration for the usrp_server.
@socketio.on("usrp_server_load_config")
def usrp_server_load_config(req):
    usrp_server_addr, ok = get_value_with_check(req, "usrp_server_addr")
    if not ok:
        return failed_with_explain(usrp_server_addr)
    usrp_server_config_fields, ok = get_value_with_check(req, "usrp_server_config_fields")
    if not ok:
        return failed_with_explain(usrp_server_config_fields)
    return usrp_servers.load_config(usrp_server_addr,
                                    usrp_server_config_fields )

## This routine is for updating the configuration for the usrp_server.
@socketio.on("usrp_server_update_config")
def usrp_server_update_config(req):
    usrp_server_addr, ok = get_value_with_check(req, "usrp_server_addr")
    if not ok:
        return failed_with_explain(usrp_server_addr)
    usrp_server_config, ok = get_value_with_check(req, "usrp_server_config")
    if not ok:
        return failed_with_explain(usrp_server_config)
    return usrp_servers.update_config(usrp_server_addr,
                                      usrp_server_config)

## This routine is for testing the connection with peer_server.
@socketio.on("skg_peer_server_ping")
def skg_peer_server_ping(req):
    peer_server_addr, ok = get_value_with_check(req, "peer_server_addr")
    if not ok:
        return failed_with_explain(peer_server_addr)
    try:
        connect_info = requests.get(peer_server_addr + "/ping")
        if (connect_info.text == "pong"):
            return STATUS_OK
        return failed_with_explain("Cannot establish the connection with {}"
                                   .format(peer_server_addr))
    except Exception as e:
        return failed_with_explain(str(e))

## This routine is for loading the configuration from skg_client.
@socketio.on("skg_client_load_config")
def skg_client_load_config(req):
    return skg_client.get_config()

## This routine is for updating the configuration for skg_client.
@socketio.on("skg_client_update_config")
def skg_client_update_config(req):
    try:
        explain, ok = skg_client.update_config(req)
        if not ok:
            return failed_with_explain(explain)
        return STATUS_OK
    except Exception as e:
        return failed_with_explain(str(e))

## This routine is for starting the skg_client.
@socketio.on("skg_start")
def skg_start(req):
    return skg_client.run()

## This routine is for stopping the skg_client.
@socketio.on("skg_stop")
def skg_stop(req):
    return skg_client.stop()

if __name__ == "__main__":
    socketio.run(app, debug=True)
