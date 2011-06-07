#!/usr/bin/python
#
# Copyright (C) 2011 Emery Hemingway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    import argparse
except ImportError:
    print"You do not have argparse installed."
    print "See: http://pypi.python.org/pypi/argparse"
    sys.exit(1)
    
import os
import subprocess
import sys

import ConfigParser
try:
    import MySQLdb
    import MySQLdb.cursors
except ImportError:
    print "You do not have the MySQL Python module installed."
    print "See: http://pypi.python.org/pypi/MySQL-python"
    sys.exit(1)


try:
    check = subprocess.check_output(['r128-scanner', '-h'],
                                    stderr=subprocess.STDOUT)
except OSError:
    print "r128-scanner not found. It can be built from the libebur128 source at  "
    print "http://www-public.tu-bs.de:8080/~y0035293/libebur128.html"
    sys.exit(1)
except subprocess.CalledProcessError:
    print "r128-scanner not working."


"""
Note: Gain is multipled by 100, Loudness by 10
"""


class rddb():
    """Interacts with the mysql database associated with a rivendell system.
    Reads /etc/rd.conf to find connection details.
    """

    def __init__(self):
        rdconf = ConfigParser.RawConfigParser()
        rdconf.read('/etc/rd.conf')
        try:
            self.conn = MySQLdb.connect (use_unicode = True,
                host = rdconf.get('mySQL', 'Hostname'),
                user = rdconf.get('mySQL', 'Loginname'),
                passwd = rdconf.get('mySQL', 'Password'),
                db = rdconf.get('mySQL', 'Database'))
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
        self.cursor = self.conn.cursor()

    def addLoudnessColumns(self):
        self.cursor.execute("""alter table CUTS 
                                add column LOUDNESS_MEASURED smallint,
                                add column LOUDNESS_TARGET smallint""")
    def describeCuts(self):
        self.cursor.execute("""describe CUTS""")
        return self.cursor.fetchall()

    def unanalyzedCuts(self, group, LkTarget):
        if group == 'ALL':
            self.cursor.execute("""select CUT_NAME from CUTS 
                                    where (LOUDNESS_TARGET is null
                                        or LOUDNESS_TARGET != %s)
                                """, (LkTarget))

        else:
            self.cursor.execute("""select CUT_NAME from CUTS left join CART
                                    on (CART.NUMBER=CUTS.CART_NUMBER)
                                    where GROUP_NAME = %s
                                    and (LOUDNESS_TARGET is null
                                    or LOUDNESS_TARGET != %s)
                                """, (group, LkTarget))
        return self.cursor.fetchall()


    def setGain(self, cut_name, gain, LkMeasured, LkTarget):
        gain *= 10
        self.cursor.execute("""update CUTS set PLAY_GAIN = %s,
                                LOUDNESS_MEASURED = %s,
                                LOUDNESS_TARGET = %s
                                where CUT_NAME = %s
                            """, (gain, LkMeasured, LkTarget, cut_name))
    def dropColumns(self):
        self.cursor.execute("""alter table CUTS drop column LOUDNESS_MEASURED,
                                drop column LOUDNESS_TARGET""")


def analyze(filename, LkTarget):
    s = subprocess.Popen(['r128-scanner', filename], stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
    output = s.communicate()[0]
    words = output.split()
    word = words[1]
    
    result = word.replace('.','')
    LkMeasured = int(word.replace('.',''))
    
    gain = LkTarget - LkMeasured

    return LkMeasured, gain

def checkTable():
    description = db.describeCuts()
    noNormField = True
    for field in description:
        if field[0] == 'LOUDNESS_TARGET':
            noNormField = False
            break
        else:
            continue

    if noNormField == True:
        db.addLoudnessColumns()

def main(LkTarget, args):
    for row in db.unanalyzedCuts(args.group, LkTarget):
        if not row:
            break

        cut_name = row[0]
        filename = '/var/snd/' + cut_name + '.wav'

        if not os.path.exists(filename):
            continue
    
        if args.verbose:
            print "Cut: ", cut_name
        LkMeasured, gain = analyze(filename, LkTarget)
        if args.verbose:
            print "\tLkMeasured:", LkMeasured / 10.0
            print "\tGain change:", gain / 10.0
            print
        db.setGain(cut_name, gain, LkMeasured, LkTarget)


parser = argparse.ArgumentParser(
        description='Normalize cuts in a group.',
        epilog="See http://tech.ebu.ch/loudness for more information."
                                )
parser.add_argument('-v', dest='verbose', action='store_true')
parser.add_argument('--drop-columns', dest='drop_columns',
        action='store_true', help=""" Remove extra columns added by to your
        database by this script. This will not restore your previous gain levels
        and will require previously normalized cuts to be re-analyzed if you run
        this script again.""" )
parser.add_argument('-l', metavar='LUFS', dest='LkTarget',
        action='store', type=float,  default=-23,
        help="""Target loudness level. Defaults to
                the recommended -23.""")
parser.add_argument('-g', metavar='GROUP', dest='group', type=str,
        help="group to set gain levels in")

args = parser.parse_args()

db = rddb()

if args.drop_columns:
    db.dropColumns()
    print "Extraneous columns dropped from database, gain levels still present."
    sys.exit(0)

checkTable()

LkTarget = int(args.LkTarget *10)
if LkTarget >= 0:
    LkTarget = 0 - LkTarget

main(LkTarget, args)
