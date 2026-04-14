from opensky_api import FlightData, FlightTrack, OpenSkyApi, StateVector, TokenManager, Waypoint
from dotenv import load_dotenv

import math
import time
import json
import os
import serial

from pathlib import Path
current_directory = Path.cwd()

RUNWAY_START, RUNWAY_END, airportBoundary = None, None, None
print("Current Working Directory:", current_directory)

class Distance:
    def __init__(self, distance):
        self.distance : float = distance
    
    @staticmethod
    def toCartesian(distance):
        return distance / 111.32
    
    @staticmethod
    def toKm(distance):
        return distance * 111.32
    
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

#make this fail if there are no env variables
def _make_api():
    load_dotenv()
    client_id = os.getenv("LUFTALAGI_CLIENT_ID")
    client_secret = os.getenv("LUFTALAGI_CLIENT_SECRET")
    return OpenSkyApi(client_id=client_id, client_secret=client_secret)

def FindNearestStateVector() -> StateVector | int:
    neabyStateVectors : list[StateVector] = MY_API.get_states(
        int(time.time()),
        None,
        airportBoundary
    )

    print(neabyStateVectors)
    if not neabyStateVectors:
        print("No nearby state vectors found.")
        return None, None
    
    start_cart = RUNWAY_START.toCartesian(ref=RUNWAY_START)
    end_cart   = RUNWAY_END.toCartesian(ref=RUNWAY_START) 

    runwayDirection = (end_cart - start_cart)
    nearestStateVector, distance = None, None

    #Landing aircraft show a baro altitude of -50
    airborne = [sv for sv in neabyStateVectors.states if not sv.on_ground and sv.baro_altitude is not None and sv.baro_altitude > 0 and sv.baro_altitude < 1000]

    for sv in airborne:  
        airplaneCoord: CartCoord = PolarCoord(sv.latitude, sv.longitude).toCartesian(RUNWAY_START)

        if airplaneCoord is None:
            print(f"Could not convert airplane coordinates for {sv.callsign}")
            continue

        magnitude = (start_cart - airplaneCoord).magnitude()
        if airplaneCoord.dot(runwayDirection) >  -0.97:
            continue

        if distance is None or magnitude < distance:
            nearestStateVector = sv
            distance = magnitude

    return nearestStateVector, distance

def FindNearestAircraft():
   nearestPlane, distance = FindNearestStateVector()
   if nearestPlane:
        print("Nearest Plane Callsign:", nearestPlane.callsign)
        print("Distance to Runway Threshold km:", Distance.toKm(distance))
        DistanceScaling = min(1, distance/MAX_DIST) 

        print(f"Distance Scaling: {distance/MAX_DIST}")

        LightsToIlluminate = math.floor(NUMBER_OF_LIGHTS * DistanceScaling)
        FinalLightPower = NUMBER_OF_LIGHTS * DistanceScaling - LightsToIlluminate

        print(f"Lights to Illuminate: {LightsToIlluminate}")
        print(f"Final Light Power: {FinalLightPower}")
   else:
        print("No planes on final to selected runway found.")

MAX_DIST = Distance.toCartesian(3)
NUMBER_OF_LIGHTS = 4
CALL_DELAY = 5
RUNWAY_START, RUNWAY_END, airportBoundary = SetupAirport(airportName="miami", runway="09")
MY_API = _make_api()

while True:
    FindNearestAircraft()
    time.sleep(CALL_DELAY)

