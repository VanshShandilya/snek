from mysql import connector
import json

def main():
    with open('config.json', 'r') as f:
        info = json.load(f)
        cnx = connector.connect(host=info['SQL']['host'], user=info['SQL']['user'], password=info['SQL']['password'])
        cnx.autocommit
        csr = cnx.cursor()
        csr.execute('SHOW DATABASES;')
        data = csr.fetchall()
        if (info['SQL']['database'],) not in data:
            csr.execute(f'CREATE DATABASE {info["SQL"]["database"]};')
            print('Database successfully made')
        csr.execute(f'USE {info["SQL"]["database"]};')
        csr.execute('SHOW TABLES;')
        data = csr.fetchall()
        if ('snekscores',) not in data:
            csr.execute('CREATE TABLE snekscores(id int primary key, Username varchar(255), highScore int);')
            print('Table successfully made')

if __name__ == '__main__':
    main()