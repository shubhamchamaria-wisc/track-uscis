#!/usr/bin/python3
from flask import Flask, request, render_template, jsonify, session
import track_case
import sys

app = Flask(__name__)
app.secret_key = 'djkskskkkalallaq!!!!2333uscissucks'
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/detailed')
def detail():
	return render_template('details.html')

@app.route('/_process')
def calculate():
	key = request.args.get('key')
	if(len(key) == 13):
		processed, processing, other, status, ret_list = track_case.main(key)
		if(processed == 0 and processing == 0 and other == 0):
			return jsonify({"status" : status})
		else:
			session['details'] = ret_list
			return jsonify({"status" : status, "processed" : processed, "processing" : processing, "other" : other})
	else:
		return jsonify({"status" : 0})

@app.route('/_more')
def viewMore():
	ret_list = session.get("details", None)
	session.clear()
	return jsonify(ret_list)