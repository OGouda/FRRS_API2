import os
from binascii import hexlify
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)
from models import *

STANDARD_API_LENGTH = 16

def addNewTable(New_table_name = None):
    # Add new API
    if db.session.query(Events.event_table_name).filter_by(event_table_name=New_table_name).first() is not None:
        print(f"Error! A table with the same name [{New_table_name}] exists already! ")

    else:
        if (New_table_name == None) and (New_table_name == " "): 
            
            print(f"Error! Table name you have inserted is [{New_table_name}] is in valid! ")
            
        else:
            key_generated = hexlify(str.encode('77a2ff77a2700e95c1767e9ac98c7f35')).decode()
            p = Events(key=key_generated, event_table_name=New_table_name)

            db.session.add(p)
            db.session.commit()

            print(f"The key [{key_generated}] has been generated correctly and table [{New_table_name}] were assgined to it")


if __name__ == "__main__":
    
    New_table_name = Table_event_1.__tablename__

    addNewTable(New_table_name)