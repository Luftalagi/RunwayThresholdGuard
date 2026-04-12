from opensky_api import FlightData, FlightTrack, OpenSkyApi, StateVector, TokenManager, Waypoint
from dotenv import load_dotenv

import math
import time
import json
import os
import serial

#dot product is being weird

from pathlib import Path
current_directory = Path.cwd()

RUNWAY_START, RUNWAY_END, airportBoundary = None, None, None
print("Current Working Directory:", current_directory)



_CREDENTIALS_PATH = "credentials.json"
_has_credentials = os.path.exists(_CREDENTIALS_PATH)

class PolarCoord:
    def __init__(self, Lat: float, Lon: float):
        self.Lat = Lat
        self.Lon = Lon

    def toCartesian(self, ref=None):
        if ref is None:
            return CartCoord(0, 0, 0)
        x = (self.Lon - ref.Lon) * math.cos(math.radians(ref.Lat))
        y = self.Lat - ref.Lat
        z = 0
        return CartCoord(x, y, z)

    def __str__(self):
        return f"Lat: {self.Lat} Lon: {self.Lon}"

class CartCoord:
    def __init__(self, X: float, Y: float, Z: float):
        self.X = X
        self.Y = Y
        self.Z = Z

    def __sub__(self, Coord):
        return CartCoord(self.X - Coord.X, self.Y - Coord.Y, self.Z - Coord.Z)
    
    def __str__(self):
        return f"{self.X} {self.Y} {self.Z}"

    def dot(self, Coord : CartCoord):
        mag_self = self.magnitude()
        mag_other = Coord.magnitude()
        if mag_self == 0 or mag_other == 0:
            return 0
        return (self.X * Coord.X + self.Y * Coord.Y + self.Z * Coord.Z) / (mag_self * mag_other)
    
    def magnitude(self):
        return math.sqrt((self.X ** 2) + (self.Y ** 2) + (self.Z ** 2))
    
def LoadJSON():
    try:
        with open('locations.json', 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return
    except json.JSONDecodeError:
        return
    
def SetupAirport(airportName:str, runway:str):
    data = LoadJSON()
    if not data:
        return None, None, None
    
    airportData = data[airportName]
    airportBoundary = [airportData["lamin"], airportData["lamax"], airportData["lomin"], airportData["lomax"]]

    rwyReference = airportData["runway"][runway]
    
    RUNWAY_START = PolarCoord(rwyReference["runwayStart"][0], rwyReference["runwayStart"][1])
    RUNWAY_END = PolarCoord(rwyReference["runwayEnd"][0], rwyReference["runwayEnd"][1])

    return RUNWAY_START, RUNWAY_END, airportBoundary

def _make_api():
    load_dotenv()
    client_id = os.getenv("LUFTALAGI_CLIENT_ID")
    client_secret = os.getenv("LUFTALAGI_CLIENT_SECRET")
    if _has_credentials:
        return OpenSkyApi(client_id=client_id, client_secret=client_secret)
    else:
        print("NO credntials")
    return OpenSkyApi()

def FindNearestStateVector() -> StateVector | int:
    neabyStateVectors : list[StateVector] = api.get_states(
        int(time.time()),
        None,
        airportBoundary
    )
    
    print(f"Function runway start: {RUNWAY_START}")
    start_cart = RUNWAY_START.toCartesian(ref=RUNWAY_START)
    end_cart   = RUNWAY_END.toCartesian(ref=RUNWAY_START) 

    runwayDirection = (end_cart - start_cart)
    nearestStateVector, distance = None, 10*100

    airborne = [sv for sv in neabyStateVectors.states if not sv.on_ground and sv.baro_altitude is not None and sv.baro_altitude > 100 and sv.baro_altitude < 1000]  # CHANGED
    
    print(airborne)
    for sv in airborne:  
        if nearestStateVector is None:
             return None, None
        airplaneCoord: CartCoord = PolarCoord(sv.latitude, sv.longitude).toCartesian(RUNWAY_START)

        if airplaneCoord is None:
            print("airplane state cord is removed")
            return None, None

       # print(f"AIRPLANECOORD{airplaneCoord}")
        print(f"{sv.callsign} dot: {airplaneCoord.dot(runwayDirection)}")

        magnitude = (start_cart - airplaneCoord).magnitude()
        if airplaneCoord.dot(runwayDirection) >  -0.97:
            continue

        if magnitude < distance:
            nearestStateVector = sv
            distance = magnitude

    return nearestStateVector, (start_cart - airplaneCoord).magnitude()

api = _make_api()
RUNWAY_START, RUNWAY_END, airportBoundary = SetupAirport(airportName="miami", runway="09")

MAX_DIST = 3
nearestPlane, distance = FindNearestStateVector()
if nearestPlane:
    print(f"NEAREST PLANE: {nearestPlane.callsign, distance*60}")
else:
    print("NO NEARBY AIRCRAFT")
