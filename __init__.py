from flask import Flask, render_template, session, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from court import Court
import os
import config
import requests
import json

#Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

#Token response
YELP_ACCESS_TOKEN = "aqKeXPatJnHAFTXPoyuhkrIbgDvt5KfFrkwitxXGVGrtexzENT57Pk2EPmGoebTeQT7-iMC6Ul-Q568toAA4oe8LUNlL571AjfEHfNktKUKzhYD--mizotdiG4bdV3Yx"
EMPTY_RESPONSE = json.dumps('')

#DB models
class CourtMan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    count = db.Column(db.Integer)

    def __init__(self, name, count):
        self.name = name
        if count == None:
        	self.count = 0
        self.count = count

    def __repr__(self):
        return '<Court %r, count %r>' % (self.name, self.count)

db.drop_all()                                                                                                                               
db.create_all()   

def get_auth_dict(access_token):
    return {'Authorization' : "Bearer " + access_token}

def get_yelp_access_token():
    # WARNING: Ideally we would also expire the token. An expiry is sent with the token which we ignore.
    if YELP_ACCESS_TOKEN in session:
        print "access token found in session"
    else:
        print "access token needs to be retrieved"
        response = requests.post('https://api.yelp.com/oauth2/token', data=config.yelp_api_auth)
        if response.status_code == 200:
            session[YELP_ACCESS_TOKEN] = response.json()['access_token']
            print "stored access token in session:", session[YELP_ACCESS_TOKEN]
        else:
            raise RuntimeError("Unable to get token, received status code " + str(response.response))
    
    return session[YELP_ACCESS_TOKEN]

@app.route("/db", methods=['POST', 'GET'])
def dbapp():
	court1 = CourtMan('court1', 'court2')
	try:
		db.session.add(court1)
		db.session.commit()
		print (CourtMan.query.all())
	except: 
		print "did not add"
	return "bleh"

def getData(response):
    try:
        result = response.json()
        allcourts = result["businesses"]
        if not allcourts:
            raise ValueError("Search is invalid.") 
        courts = []
    except ValueError as e:
        print e
    for a in allcourts:
        name  = a["name"]
        image_url = a["image_url"]
        location = a["location"]
        coordinates = a["coordinates"]

        mycourt = db.session.query(CourtMan).filter(CourtMan.name==name).first()
        courtCount = 0
        if not mycourt == None:
        	courtCount = mycourt.count

        court = Court(name, image_url, location, coordinates, courtCount)
        courts.append(court)
    loadSearch(allcourts)
    return courts

def loadSearch(allcourts):
	for court in allcourts:
		courtName = court["name"]
		courtLocation = court["location"]["city"]
		print courtName
		print courtLocation

		if db.session.query(CourtMan).filter(CourtMan.name==courtName).count() == 0:
			currentCourt = CourtMan(courtName, 0)
			db.session.add(currentCourt)
	db.session.commit()
	print (CourtMan.query.all())

@app.route("/increment", methods=['POST'])
def increment():
	mycourt = db.session.query(CourtMan).first()
	mycourt.count = mycourt.count + 1
	db.session.commit()
	print (CourtMan.query.all())
	return EMPTY_RESPONSE

@app.route("/decrement", methods=['POST'])
def decrement():
	mycourt = db.session.query(CourtMan).first()
	mycourt.count = mycourt.count - 1
	db.session.commit()
	print (CourtMan.query.all())
	return EMPTY_RESPONSE

@app.route("/search", methods=['POST', 'GET'])
def search():
    term = request.form['term']
    location = request.form['location']

    response = requests.get('https://api.yelp.com/v3/businesses/search',
    params=get_search_params(term, location),
    headers=get_auth_dict(get_yelp_access_token()))

    if response.status_code == 200:
        print "Got 200 for business search"
        courts = getData(response)
        return results(courts)
    else:
        print "Received non-200 response({}) for business search, returning empty response".format(response.status_code)
        return EMPTY_RESPONSE

def get_search_params(term, location):
    return {'term': term, 'location' : location}

@app.route("/results")
def results(courts):
    return render_template('results.html', courts=courts)

@app.route('/')
def homepage():
	return render_template('index.html')

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(host='0.0.0.0', port=int(port), debug=True)