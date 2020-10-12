import os
import time
import face_recognition
from io import BytesIO
from binascii import hexlify

import base64
from PIL import Image
import numpy as np

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy.schema import CreateTable
from sqlalchemy import Column, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base


from flask_restful import Resource, Api,reqparse
from multiprocessing import Pool

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)
parser = reqparse.RequestParser()

from models import *
from src import  alighmentFunctions

PRIVATE_KEY = '123'


# Global Variables 
MaxImageSize = 500       # Max image size allowed to be processed, if image exceeds this size, it will be resized. 
Threshold_FaceRec = 0.47 # Threshold used to accept that two faces are for the same person
STANDARD_API_LENGTH = 16 # Maximum length of the API keys

# Default replies

NO_FACE_FOUND      ='NO_FACE_FOUND'
DUBLICATION_OCCURED='DUBLICATION_OCCURED'
WORKED_SUCCESSFULLY='PERSON_ADDED_CORRECTLY'
NO_TABLES_FOUND_FOR_API ='NO_TABLES_FOUND_FOR_API'
ERROR_WHILE_PROCESSING_IMAGE_FILE ='ERROR_WHILE_PROCESSING_IMAGE_FILE'
MATCH_FOUND = 'MATCH_FOUND'
MATCH_NOT_FOUND = 'MATCH_NOT_FOUND'



class registration(Resource):

    # Class to handle registration operations. 
    
    def __init__(self):

        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('name'  , type = str, required = True, 
        help = 'No person name provided')
        self.reqparse.add_argument('email' , type = str, required = True,
        help = 'No person email provided')
        self.reqparse.add_argument('img64b', type = str, required = True,
        help = 'No encoded image provided')
        self.reqparse.add_argument('api'   , type = str, required = True,
        help = 'No API provided')

        super(registration, self).__init__()


    def post(self):
        # Post function to handle post requests. 
        # Requests are received from the servers that host the SignIn at the event location. It will be called external_Server

        # There is four different scenarios, each has its own API respond
        # 1) Ok                  - [OK] Image is valid and face encodings have been extracted 
        # 2) Duplication occured - [DUBLICATION_OCCURED]The person has been registered already
        # 3) Wrong Image or file - [INVALID_IMAGE_FILE] Image is NOT valid
        # 4) No faces found      - [NO_FACE_FOUND]      No face encodings have been extracted from the image, maybe user uploaded a wrong image. 

        # The externel_server is requested to provide the following information: person's image, person's name, person's email, person's gender


        # for performance measuring the time counter will start here and ends when the process of registration is done. 
        start_time= time.time()

        # Prepare the parser to read it.
        args = self.reqparse.parse_args()

        client_API= args['api']
        
        query = Events.query.with_entities(Events.event_table_name).filter_by(key=client_API).first()

        if query is None: # Not found

            print(f'No tables found for the API recieved: [{client_API}]')

            return {'message': NO_TABLES_FOUND_FOR_API}, 400

        else:
            TableName = query[0]
            Table_object = aget_table_from_name(TableName)

            try: 
                # Get information form args
                person_name_fromRequest     = args['name']
                person_email_fromRequest    = args['email']
                person_imageb64_fromRequest = args['img64b']

                # Try to read the image and process it. If any error was happened, return back an API code: INVALID_IMAGE_FILE
                image_64_decode= base64.b64decode(person_imageb64_fromRequest)     # Read the  image and decode it to base64
                Img_PILversion = Image.open(BytesIO(image_64_decode)) # Covert the decoded image to PIL Image
              

                # Try to down sample the image if its size is more than "MaxImageSize"
                img_width,img_height= Img_PILversion.size
                ratio = img_height/img_width
                
                if max(img_height, img_width) > MaxImageSize:

                    if (max(img_height, img_width) == img_width):
                        img_width = MaxImageSize
                        img_height = MaxImageSize * ratio

                    else:
                        img_height = MaxImageSize
                        img_width = MaxImageSize / ratio  

                    img_height=int(img_height)
                    img_width=int(img_width)   

                Img_PILversion = Img_PILversion.resize((img_width,img_height),  Image.NEAREST) #Apply resizing 

                if Img_PILversion.mode != 'RGB': Img_PILversion = Img_PILversion.convert("RGB") 
            

            except Exception as e:

                print("Error occured in the process of reading the image. ")
                print('Error message: ', e)
                return {'message': ERROR_WHILE_PROCESSING_IMAGE_FILE, 'error_message':str(e)}, 400

        # if image was read successfully, start processing the image and extract faces.      

        pool = Pool(processes=3)
        resutls =[]
        resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_1_and_2,[Img_PILversion, "METHOD_1"]))        
        resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_1_and_2,[Img_PILversion, "METHOD_2"]))
        resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_3_only,[Img_PILversion]))
        pool.close()
        pool.join()

        EncodingResults = []

        for i in resutls:
            Arr = i.get(timeout=1)
            if Arr is not None and Arr != []:
                EncodingResults.append(Arr)



        List_of_obtained_names     = []
        List_of_obtained_distances = []


        if  len(EncodingResults) == 0:
            return {'message': NO_FACE_FOUND}, 400

        else: 
            for functionNumber, face_encoding in EncodingResults:
            
                if len(face_encoding) > 0:

                    print('A face encoding was extracted by function No. ', functionNumber )

                    face_encoding =face_encoding[0]
                    vlow = face_encoding[0:64].tolist()
                    vhigh= face_encoding[64:128].tolist()            


                    clause =text("""SQRT(POW(CUBE(vec_low) <-> CUBE(:vlow),2) + POW( CUBE(vec_high) <-> CUBE(:vhigh),2)) <= :vThreshold 
                    ORDER BY SQRT(POW(CUBE(vec_low) <-> CUBE(:vlow),2) + POW( CUBE(vec_high) <-> CUBE(:vhigh),2)) ASC LIMIT 1;""")
                    query = Table_object.query.filter(clause).params(vlow=vlow,vhigh=vhigh, vThreshold=Threshold_FaceRec)

                    Answers = []
                    for i in query:
                        Answers.append(i)

                    if Answers ==[]:
                        List_of_obtained_names.append('No_Duplication')

                    else:
                        for Answer in Answers:
                            print(f'{Answer.personid}  {Answer.person_name}')
                            personID    = Answer.personid
                            person_name = Answer.person_name
                            email       = Answer.email
                            low_enc     = Answer.vec_low
                            high_enc    = Answer.vec_high 

                            encoding_fromDatabase = np.asarray(low_enc + high_enc)

                            print("functionNumber is [{}]  name found is [{}]".format(functionNumber, person_name))
                            List_of_obtained_names.append(person_name)

                            face_distances= np.linalg.norm( encoding_fromDatabase - np.array(face_encoding) ) 
                            List_of_obtained_distances.append(
                                {'personID':personID,
                                'person_name':person_name,
                                'email':email, 
                                'face_distances':face_distances})
                            print("face_distances: ", face_distances)    

 
            print('Number of results obtained: {}'.format(len(List_of_obtained_names)))
            
            results_ID = 0
            poolResults_highOcc_name= max(set(List_of_obtained_names), key = List_of_obtained_names.count)       
            for i in List_of_obtained_distances:
                if poolResults_highOcc_name == i['person_name']:
                    results_ID=i['personID']
                    break


            if poolResults_highOcc_name == 'No_Duplication':

                query = Table_object.query.with_entities(Table_object.personid).order_by(Table_object.personid.desc()).first()

                results_ID = 0
                if query != None:results_ID = query[0]

                results_status = WORKED_SUCCESSFULLY 
                results_ID     = results_ID + 1 
                results_NAME   = person_name_fromRequest

                print('No duplication found, the new face will be added to the database.')

                for functionNumber, face_encoding in EncodingResults:
                    if len(face_encoding) > 0:
                        face_encoding =face_encoding[0]

                        newRow = Table_object(
                            personid     = results_ID, 
                            person_name  = person_name_fromRequest,
                            email        = person_email_fromRequest, 
                            vec_low      = face_encoding[0:64] , 
                            vec_high     = face_encoding[64:128])

                        db.session.add(newRow) 
                        db.session.commit()  

                        print("Person [{}] with functionNumber [{}] has been added to database".format(results_NAME, functionNumber))

                stop_time=time.time()
                print('Processing Time: ', stop_time-start_time)
                return {
                    'message': WORKED_SUCCESSFULLY,
                    'ID'     : results_ID,
                    'PERSON_NAME' : results_NAME ,
                    }, 200

            else:
                results_status = DUBLICATION_OCCURED 
                results_ID     = personID   
                results_NAME   = poolResults_highOcc_name        


                stop_time=time.time()
                print('Processing Time: ', stop_time-start_time)
                return {
                    'message': DUBLICATION_OCCURED,
                    'ID'     : results_ID,
                    'PERSON_NAME' : results_NAME ,
                    }, 201




class signIn(Resource):
# Class to handle SignIn operations. 


    def __init__(self):

        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('img64b', type = str, required = True,
        help = 'No encoded image provided')
        self.reqparse.add_argument('api'   , type = str, required = True,
        help = 'No API provided')

        super(signIn, self).__init__()


    def post(self):
        # Post function to handle post requests. 
        # Requests are received from the servers that host the SignIn at the event location. It will be called external_Server


        # There is four different scenarios, each has its own API respond
        # 1) not match           - [MATCH_NOT_FOUND] 
        # 2) person_found        - [MATCH_FOUND]
        # 3) Wrong Image or file - [INVALID_IMAGE_FILE] 
        # 4) No faces found      - [NO_FACE_FOUND]   

        start_time  =time.time()


        # Prepare the parser to read it.
        args = self.reqparse.parse_args()

        client_API= args['api']
        query = Events.query.with_entities(Events.event_table_name).filter_by(key=client_API).first()
        
        if query is None: # Not found

            print(f'No tables found for the API recieved: [{client_API}]')

            return {'message': NO_TABLES_FOUND_FOR_API}, 400

        else:
            TableName = query[0]
            print("TableName" , TableName)
            Table_object = aget_table_from_name(TableName)


        image_64_decode= base64.b64decode(args['img64b'])     # Read the  image and decode it to base64
        Img_PILversion = Image.open(BytesIO(image_64_decode)) # Covert the decoded image to PIL Image


        # Try to down sample the image if its size is more than "MaxImageSize"
        img_width,img_height= Img_PILversion.size
        ratio = img_height/img_width
        
        if max(img_height, img_width) > MaxImageSize:

            if (max(img_height, img_width) == img_width):
                img_width = MaxImageSize
                img_height = MaxImageSize * ratio

            else:
                img_height = MaxImageSize
                img_width = MaxImageSize / ratio  

            img_height=int(img_height)
            img_width=int(img_width)   

        # if image was read successfully, start processing the image and extract faces.      
        pool = Pool(processes=2)
        resutls =[]
        resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_1_and_2,[Img_PILversion, "METHOD_1"]))        
        resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_1_and_2,[Img_PILversion, "METHOD_2"]))
        #resutls.append(pool.apply_async(alighmentFunctions.handleImage_method_3_only,[Img_PILversion]))

        pool.close()
        pool.join()

        EncodingResults = []

        for i in resutls:
            Arr = i.get(timeout=1)
            if Arr is not None and Arr != []:
                EncodingResults.append(Arr)



        List_of_obtained_names     = []
        List_of_obtained_distances = []

        if  len(EncodingResults) == 0:
            # If no face encodings were generated at all, that means the image has something wrong. 
            # Return back an API code: NO_FACE_FOUND
            return {'message': NO_FACE_FOUND}, 400

        else:          

            for functionNumber, face_encoding in EncodingResults:
            
                if len(face_encoding) > 0:

                    print('A face encoding was extracted by function No. ', functionNumber )
                    face_encoding =face_encoding[0]
                    vlow = face_encoding[0:64].tolist()
                    vhigh= face_encoding[64:128].tolist()            

                    clause =text("""SQRT(POW(CUBE(vec_low) <-> CUBE(:vlow),2) + POW( CUBE(vec_high) <-> CUBE(:vhigh),2)) <= :vThreshold 
                    ORDER BY SQRT(POW(CUBE(vec_low) <-> CUBE(:vlow),2) + POW( CUBE(vec_high) <-> CUBE(:vhigh),2)) ASC LIMIT 1;""")
                    query = Table_object.query.filter(clause).params(vlow=vlow,vhigh=vhigh, vThreshold=Threshold_FaceRec)

                    Answers = []
                    for i in query:
                        Answers.append(i)

                    if Answers ==[]:
                        List_of_obtained_names.append('No_Duplication')

                    else:
                        for Answer in Answers:
                            print(f'{Answer.personid}  {Answer.person_name}')
                            personID    = Answer.personid
                            person_name = Answer.person_name
                            email       = Answer.email
                            low_enc     = Answer.vec_low
                            high_enc    = Answer.vec_high 

                            encoding_fromDatabase = np.asarray(low_enc + high_enc)

                           
                            List_of_obtained_names.append(person_name)

                            face_distances= np.linalg.norm( encoding_fromDatabase - np.array(face_encoding) ) 
                            List_of_obtained_distances.append(
                                {'personID':personID,
                                'person_name':person_name,
                                'email':email, 
                                'face_distances':face_distances})
                            
                            print("functionNumber is [{}]  name found is [{}] with distance [{}]".format(functionNumber, person_name, face_distances))


            # Create a pool to find the repeated result
            print('Number of results obtained: {}'.format(len(List_of_obtained_names)))

            poolResults_highOcc_name= max(set(List_of_obtained_names), key = List_of_obtained_names.count)       
            results_ID              = 0
       
            if poolResults_highOcc_name == 'No_Duplication':
                # MATCH wasnt found in the database
                stop_time=time.time()
                print('Processing Time: ', stop_time-start_time)
                return{'message': MATCH_NOT_FOUND}, 201  

            else:
                # MATCH is found in the database
                face_distance = 0
                for i in List_of_obtained_distances:
                    if poolResults_highOcc_name == i['person_name']:
                        results_ID=i['personID']
                        face_distance = i['face_distances']
                        break

                stop_time=time.time()
                print('Processing Time: ', stop_time-start_time)

                results_NAME   = poolResults_highOcc_name  
                return {
                    'message': MATCH_FOUND,
                    'ID'     : results_ID,
                    'PERSON_NAME' : results_NAME ,
                }, 200



class NewEvent(Resource):
# Class to handle NewEvent operations. 

    def __init__(self):

        self.reqparse = reqparse.RequestParser()
        # no help parameter is provided into this add_argument function to not reveal the parameters of this function
        self.reqparse.add_argument('key', type = str, required = True,  help = 'No key provided') 
        self.reqparse.add_argument('event_table_name', type = str, required = True,  help = 'No event_table_name provided') 
        super(NewEvent, self).__init__()

    def post(self):

        # Prepare the parser to read it.
        args = self.reqparse.parse_args()

        private_key= args['key']

        if (private_key == PRIVATE_KEY):
            key_generated = hexlify(os.urandom(STANDARD_API_LENGTH)).decode()
            

            event_table_name= args['event_table_name']

            if(event_table_name in db.metadata.tables): #If table name exists already

                new_row = Events(key=key_generated, event_table_name=event_table_name)

                db.session.add(new_row) 
                db.session.commit()
                

                print(f"The key [{key_generated}] has been generated correctly and table [{event_table_name}] were assgined to it")  
        
                Message = f'The key [{key_generated}] has been generated correctly and table [{event_table_name}] were assgined to it'
                Code    = 200   

            else:
         
                Message = f'Table name chosen [{event_table_name}] is not within the reserved list'
                Code    = 200                  

        else:
            Message = f'Key Error!'
            Code    = 400

        return {
            'message': Message,
        }, Code        



class EventName(Resource):
# Class to handle EventName operations. 

    def __init__(self):

        self.reqparse = reqparse.RequestParser()
        # no help parameter is provided into this add_argument function to not reveal the parameters of this function
        self.reqparse.add_argument('key', type = str, required = True,  help = 'No key provided') 
        self.reqparse.add_argument('api'   , type = str, required = True, help = 'No API provided')
        super(EventName, self).__init__()

    def post(self):

        # Prepare the parser to read it.
        args = self.reqparse.parse_args()

        private_key= args['key']


        if (private_key == PRIVATE_KEY):
            api_key= args['api']

            query = Events.query.with_entities(Events.event_table_name).filter_by(key =api_key).first()
            if  query is not None:
                table_name = query[0]
                Message = f'Table [{table_name}] is assigned for the requested key'
                Code    = 200

            else:
                Message = f'No table found for this API key'
                Code    = 400

        else:
                Message = f'Key Error!'
                Code    = 400

        return {
            'message': Message,
        }, Code        

  

api.add_resource(registration, '/registration')
api.add_resource(signIn , '/signIn')
api.add_resource(NewEvent, '/new-event')
api.add_resource(EventName, '/event-name')

if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5000, debug=False)

