from libs.geoloc import *
from libs.planes import *

import numpy as np
import argparse
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os
import time
import psycopg2
from psycopg2.extensions import adapt, register_adapter, AsIs
import re

PSQL_DB = "planes"
PSQL_TABLE = "planes"

def main():
    parser  = argparse.ArgumentParser()
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--reg", type=str)
    parser.add_argument("-daydir", type=str)
    parser.add_argument("-psql_user", type=str)
    parser.add_argument("-psql_pass", type=str)
    args  = parser.parse_args()
    list_of_files = sorted(os.listdir(args.daydir))
    conn = psycopg2.connect(host='localhost', dbname=PSQL_DB, user=args.psql_user, password=args.psql_pass)
    curs = conn.cursor()
    if args.plot:
        plane_numb = args.reg
        path = get_path(plane_numb, curs)
        print('Path is: ' + str(path))
        plt.scatter(*zip(*path))
        plt.savefig(str(plane_numb)+'.png')

    else:
        # For each file of the day
        for filename in list_of_files:
            os.system('clear')
            with open(args.daydir + '/' + filename, encoding='utf-8') as f:
                try:
                    print('loading planes from file ' + filename)
                    j = json.load(f) # Loads the whole thing when we don't really need it
                    aviatos_list_from_file = j['acList']
                    leng = len(aviatos_list_from_file)
                    # This is the innefficient loop
                    for i, aviato in enumerate(aviatos_list_from_file):
                        # TODO: query db with plane number instead of looking in long list
                        os.sys.stdout.write('\r' + str(i+1) + '/' + str(leng))
                        #webi = aviato.get('Reg')
                        numb = aviato.get('Reg')
                        callsign = aviato.get('Call')
                        latitude = aviato.get('Lat')
                        longitude = aviato.get('Long')
                        flg = False

                        curs.execute('SELECT * FROM planes WHERE number = %s', (numb,))
                        entry = curs.fetchone()

                        # If the plane is already in the DB and we got its position
                        if entry is not None and entry[0]==numb and latitude is not None:
                            #if plane_obj[0] == numb and latitude is not None:
                            flg = True
                            curs.execute('SELECT * from path where number = %s ORDER BY index DESC LIMIT 1', (numb,)) # order by index
                            rep = curs.fetchone()
                            if rep is not None:
                                path_index = rep[1]
                            #print('Path index is ' + str(path_index))
                                path_index = path_index + 1
                                curs.execute('INSERT INTO path (number, index, point_x, point_y) values (%s, %s, %s, %s)', (numb, path_index, latitude, longitude))
                                conn.commit()

                        # Else it is not yet in db. Add to db if we have number and position
                        elif not flg and numb is not None and latitude is not None:
                            curs.execute('INSERT INTO planes(number, callsign) values (%s, %s)', (numb, callsign))
                            conn.commit()
                        time.sleep(0.001)
                    time.sleep(0.5) # Pause between files

                except ValueError as e:
                    pass


def get_path(plane_numb, curs):
    curs.execute('SELECT point_x, point_y from path where number = %s order by index DESC', (plane_numb,))
    return curs.fetchall()

def printpath_and_classify(array):
    plt.plot(array)
    plt.show()


if __name__ == "__main__":
    main()
