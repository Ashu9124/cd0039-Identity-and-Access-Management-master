import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json

from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    formatted_drink = [drink.short() for drink in drinks]
    return jsonify({'success': True,
                    'drinks': formatted_drink,
                    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details():
    drinks = Drink.query.all()
    formatted_drink = [drink.long() for drink in drinks]
    return jsonify({'success': True,
                    'drinks': formatted_drink,
                    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    body = request.get_json()
    drinks = Drink.query.all()
    formatted_drink_old = [drink.long() for drink in drinks]
    recipe = body.get('recipe', None)
    title = body.get('title', None)
    drinks = Drink(recipe=recipe, title=title)
    drinks.insert()
    drinks = Drink.query.all()
    formatted_drink_new = [drink.long() for drink in drinks]
    inserted_drink = formatted_drink_old - formatted_drink_new
    if inserted_drink:
        return jsonify({'success': True,
                        'drinks': inserted_drink,
                        }), 200
    else:
        return jsonify({'success': False
                        }), 422


@app.route('/questions/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink():

    try:
        body = request.get_json()
        update_id = body.get('id', None)
        recipe = body.get('recipe', None)
        title = body.get('title', None)
        drink = Drink.query.filter(Drink.id == update_id).one_or_none()
        if not drink:
            abort(422)
        if recipe:
            drink.recipe = recipe

        if title:
            drink.title = title

        drink.update()
        return jsonify({'success': True,
                        'drinks': [drink.long()]
                        }), 200
    except Exception as e:
        print(e)
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('patch:drinks')
def delete_question(drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).all()

        if len(drink) == 0:
            abort(422)

        drink[0].delete()

    except Exception as e:
        print(e)
        abort(422)

    return jsonify({'success': True,
                    'delete': drink_id
                    }), 200



# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def notfound(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def authenticationerror(error):
    return jsonify({
        "success": False,
        "error": error.error["code"],
        "message": error.error['description']
    }), AuthError
