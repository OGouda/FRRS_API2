from app import db
from sqlalchemy import Float, column, func, Numeric
from sqlalchemy.dialects.postgresql import ARRAY


# Next we created a Events() table class and assigned it a table name of events_table. 
# We then set the attributes that we want to stor

class Events(db.Model):
    __tablename__ = 'events'

    id	= db.Column(db.Integer, primary_key=True)
    key	= db.Column(db.String())
    event_table_name = db.Column(db.String())

    def __init__(self, key, event_table_name):
    	#that will run the first time we create a new object of class
        self.key = key
        self.event_table_name = event_table_name


    def __repr__(self):
    	# to represent the object when we query for it.
        return '<id {}>'.format(self.id)



class Table_event_1 (db.Model):
    __tablename__ = 'table_event_1'

    id          = db.Column(db.Integer, primary_key=True)
    personid    = db.Column(db.Integer)
    person_name = db.Column(db.String())
    email       = db.Column(db.String())
    vec_low     = db.Column(db.ARRAY(Float))
    vec_high    = db.Column(db.ARRAY(Float))

    def __init__(self, personid, person_name, email, vec_low, vec_high):
    	#that will run the first time we create a new object of class
        
        self.personid   = personid
        self.person_name= person_name
        self.email      = email
        self.vec_low    = vec_low
        self.vec_high   = vec_high


    def __repr__(self):
    	# to represent the object when we query for it.
        return '<id {}>'.format(self.id)



class Table_event_2(db.Model):
    __tablename__ = 'table_event_2'
    id          = db.Column(db.Integer, primary_key=True)
    personid    = db.Column(db.Integer)
    person_name = db.Column(db.String())
    email       = db.Column(db.String())
    vec_low     = db.Column(db.ARRAY(Float))
    vec_high    = db.Column(db.ARRAY(Float))

    def __init__(self, personid, person_name, email, vec_low, vec_high):
        #that will run the first time we create a new object of class
        
        self.personid   = personid
        self.person_name= person_name
        self.email      = email
        self.vec_low    = vec_low
        self.vec_high   = vec_high
  

class Table_event_3(db.Model):
    __tablename__ = 'table_event_3'
    id          = db.Column(db.Integer, primary_key=True)
    personid    = db.Column(db.Integer)
    person_name = db.Column(db.String())
    email       = db.Column(db.String())
    vec_low     = db.Column(db.ARRAY(Float))
    vec_high    = db.Column(db.ARRAY(Float))

    def __init__(self, personid, person_name, email, vec_low, vec_high):
        #that will run the first time we create a new object of class
        
        self.personid   = personid
        self.person_name= person_name
        self.email      = email
        self.vec_low    = vec_low
        self.vec_high   = vec_high


class Table_event_4(db.Model):
    __tablename__ = 'table_event_4'
    id          = db.Column(db.Integer, primary_key=True)
    personid    = db.Column(db.Integer)
    person_name = db.Column(db.String())
    email       = db.Column(db.String())
    vec_low     = db.Column(db.ARRAY(Float))
    vec_high    = db.Column(db.ARRAY(Float))

    def __init__(self, personid, person_name, email, vec_low, vec_high):
        #that will run the first time we create a new object of class
        
        self.personid   = personid
        self.person_name= person_name
        self.email      = email
        self.vec_low    = vec_low
        self.vec_high   = vec_high


Table_Dict = {
    Table_event_1.__tablename__: Table_event_1,
    Table_event_2.__tablename__: Table_event_2,
    Table_event_3.__tablename__: Table_event_3,
    Table_event_4.__tablename__: Table_event_4
    }

def aget_table_from_name(table_name):
    return(Table_Dict[table_name])


