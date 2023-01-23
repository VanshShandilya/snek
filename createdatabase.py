import os
import sqlite3

def main():
    if not os.path.exists('Databases'):
        os.makedirs('Databases')
    cnx = sqlite3.connect('./Databases/snekscores.db')
    csr = cnx.cursor()
    csr.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    data = csr.fetchall()
    if ('snekscores',) not in data:
        csr.execute("CREATE TABLE snekscores(id integer primary key autoincrement, Username varchar(255), highScore integer);")
        print('Table successfully made')

if __name__ == '__main__':
    main()
