import sqlite3
from datetime import datetime

class Db(object):

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = get_db_conn(db_file)

    def get_orbit_proctime(self, granule):
        q = self.conn.execute("SELECT MAX(proc_date) FROM sighting WHERE orbit = ? AND success = ? " 
                              "AND source = ?",
                              (granule.orbit, True, self.args.facility))
        r = q.fetchone()
        if r is None:
            return None
        else:
            return r[0]

    def get_granule_proctime(self, granule):
        q = self.conn.execute("SELECT MAX(proc_date) FROM sighting WHERE orbit = ? AND success = ? "
                              "AND source = ?",
                              (granule.orbit, True, self.args.facility))
        r = q.fetchone()
        if r is None:
            return None
        else:
            return r[0]

    def insert_obs(self, facility, granule, sight_date, size, status_code, success):

        """
        insert or replace into Book (ID, Name, TypeID, Level, Seen) values
((select ID from Book where Name = "SearchName"), "SearchName", ...);
        """

FIX THIS - granule table; sighting table

        self.conn.execute("SELECT count FROM sighting WHERE source = ? AND granule_date = ? AND grannule_channel = ? AND proc_date = ?", (facility, granule.start, granule.channel, granule.proc_date))

        self.conn.execute('''INSERT OR REPLACE INTO sighting 
                        (source, granule_date, granule_channel, orbit, sight_date, proc_date, 
                        size, status_code, count, success) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (facility, granule.start, granule.channel, granule.orbit,
                           sight_date, granule.proc_date, size, status_code, success))
        self.conn.commit()

    def get_proc_count(self, granule, facility):
        q = self.conn.execute('SELECT COUNT(*) FROM sighting WHERE granule_date = ?' +
                              ' AND granule_channel = ? AND success = ? AND source = ?',
                              (granule.start, granule.channel, True, facility))
        count = q.fetchone()[0]


def get_db_conn(db_file):
    """
    Connect to a sqlite3 database file. Create the database if needed. 
    Not using foreign key constraints to maximize compatibility.
    :param db_file: The database file to connect to 
    :return: The connection object
    """
    conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS granule (
                    source text,
                    granule_date timestamp, 
                    orbit int,
                    PRIMARY KEY (source, granule_date));''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS channel (
                    source text,
                    granule_date timestamp, 
                    granule_channel text,
                    proc_date timestamp,
                    PRIMARY KEY (source, granule_date, granule_channel, proc_date));''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sighting (
                    source text,
                    granule_date timestamp, 
                    granule_channel text,
                    proc_date timestamp,
                    sight_date timestamp, 
                    status_code int,
                    success int,
                    PRIMARY KEY (source, granule_date, granule_channel, proc_date));''')

    conn.commit()

    return conn