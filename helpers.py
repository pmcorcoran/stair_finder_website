import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


"""
def lookup_address(address):

    url_address = address.strip()
    url_address = url_address.replace(' ', '+')

    api_key = os.environ.get("API_KEY")
    url = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={url_address}"


    return url
"""

def get_coord(address):
    api_key = os.environ.get("API_KEY")
    url_address = address.strip()
    url_address = url_address.replace(' ', '+')

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={url_address}&key={api_key}"
    response = requests.session().get(url)

    # error checking
    if response.json()['status'] == 'INVALID_REQUEST' or response.json()['status'] == 'ZERO_RESULTS':
        return 'no results'
    elif len(response.json()['results']) != 1:
        return 'multiple results'

    # getting coordinate dict
    coor_dict = response.json()['results'][0]['geometry']['location']

    return coor_dict


def get_add(coord):
    api_key = os.environ.get("API_KEY")
    if type(coord) is dict:
        coord = [coord['lat'], coord['lng']]

    coord_string = str(coord[0]) + ',' + str(coord[1])
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={coord_string}&key={api_key}"

    response = requests.session().get(url)
    json = response.json()
    r = json['results']

    return r[0]['formatted_address']