from flask import Flask, request
from google.cloud import datastore
from jsonschema import validate
import json
import logging
from jsonschema.exceptions import ValidationError


BUSINESSES= 'businesses'
REVIEWS = 'reviews'
ERROR_NOT_FOUND = {"Error" : "No business with this business_id exists"}
ERROR_REVIEW_NOT_FOUND = {"Error": "No review with this review_id exists"}
ERROR_WRONG_CONTENT = {"Error" : "The request body is missing at least one of the required attributes"}
ERROR_ALREADY_POSTED = {"Error" : "You have already submitted a review for this business. You can update your previous review, or delete it and submit a new review"}


app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return 'Welcome to the Review Site'

###################################################
#              BUSINESS FUNCTIONALITY  
##################################################

# Validate business jsons
def validate_business(content):
    body_schema = {
        "type": "object",
        "properties": {
            "owner_id": {"type": "number"},
            "name": {"type": "string"},
            "street_address": {"type": "string"},
            "city": {"type": "string"},
            "state": {"type": "string"},
            "zip_code": {"type": "number"}
        },
        "required": ["owner_id", "name", "street_address", "city", "state", "zip_code"],
        "additionalProperties": False
    }

    try:
        validate(instance=content, schema=body_schema)
        return True
    except ValidationError as e:
        logging.error(f"Validation Error: {e.message}")
        return False

# create a business
@app.route('/' + BUSINESSES, methods=['POST'])
def post_business():
    try:
        content = request.get_json()
        if not content:
            return {"Error": "Missing JSON body"}, 400
    except Exception as e:
        return {"Error": f"Invalid JSON: {str(e)}"}, 400

    if request.content_type != 'application/json':
        return {"Error": "Content-Type must be application/json"}, 400

    if not validate_business(content):
        return (ERROR_WRONG_CONTENT, 400)

    new_business = datastore.Entity(client.key(BUSINESSES))
    new_business.update({
        "owner_id": content["owner_id"],
        "name": content["name"], 
        "street_address": content["street_address"], 
        "city": content["city"],
        "state": content["state"],
        "zip_code": content["zip_code"]
        
    })
    client.put(new_business)
    new_business["id"] = new_business.key.id
    return (new_business, 201)

# get all businesses
@app.route('/' + BUSINESSES, methods=['GET'])
def get_business():
    query = client.query(kind=BUSINESSES)
    results = list(query.fetch())
    for item in results:
        item["id"] = item.key.id
    return results

# get all business by owner
@app.route('/owners' + '/<int:owner_id>' + '/' + BUSINESSES, methods=['GET'])
def get_business_by_owner(owner_id):
    query = client.query(kind=BUSINESSES)
    query.add_filter('owner_id', '=', owner_id)
    
    results = list(query.fetch())
    for item in results:
        item["id"] = item.key.id
    return results
    
# get business by id
@app.route('/' + BUSINESSES + '/<int:business_id>', methods=['GET'])
def get_business_by_id(business_id):
    business_key = client.key(BUSINESSES, business_id)
    business = client.get(key=business_key)
    if business is None:
        return (ERROR_NOT_FOUND, 404)
    else:
        business["id"] = business.key.id
        return business

# edit business
@app.route('/' + BUSINESSES + '/<int:business_id>', methods=['PUT'])
def put_business(business_id):
    try:
        content = request.get_json()
        if not content:
            return {"Error": "Missing JSON body"}, 400
    except Exception as e:
        return {"Error": f"Invalid JSON: {str(e)}"}, 400

    if request.content_type != 'application/json':
        return {"Error": "Content-Type must be application/json"}, 400

    if not validate_business(content):
        return (ERROR_WRONG_CONTENT, 400)
    
    # get key
    business_key = client.key(BUSINESSES, business_id)
    business = client.get(key=business_key)
    
    if business is None:
        return (ERROR_NOT_FOUND, 404)
    else:   
        business.update({
            "owner_id": content["owner_id"],
            "name": content["name"], 
            "street_address": content["street_address"], 
            "city": content["city"],
            "state": content["state"],
            "zip_code": content["zip_code"]
        })
        client.put(business)
        business["id"] = business.key.id
        return business

# delete business
@app.route('/' + BUSINESSES + '/<int:business_id>', methods=['DELETE'])
def delete_business(business_id):
    business_key = client.key(BUSINESSES, business_id)
    business = client.get(key=business_key)

    if business is None:
        return ERROR_NOT_FOUND, 404
    
    # delete all associated reviews 
    query = client.query(kind=REVIEWS)
    query.add_filter('business_id', '=', business_id)
    reviews = list(query.fetch())

    for review in reviews:
        client.delete(client.key(REVIEWS, review.key.id))
    
    # delete the business itself
    client.delete(business_key)
    return '', 204


###################################################
#              REVIEW FUNCTIONALITY  
##################################################

# validate review json
def validate_review(content):
    body_schema = {
        "type": "object",
        "properties": {
            "user_id": {"type" : "number"},
            "business_id": {"type" : "number"}, 
            "stars": {"type" : "number"}, 
            "review_text": {"type" : "string"},
        },
        "required": [
            "user_id",
            "business_id", 
            "stars",
        ],
        "additionalProperties": False               # only allow above
    }

    try:
        validate(instance=content, schema=body_schema)
    except:
        return False

    return True

# validate update review
def validate_update(content):
    body_schema = {
        "type": "object",
        "properties": {
            "user_id": {"type" : "number"},
            "business_id": {"type" : "number"}, 
            "stars": {"type" : "number"}, 
            "review_text": {"type" : "string"},
        },
        "required": [
            "stars",
        ],
        "additionalProperties": False               # only allow above
    }

    try:
        validate(instance=content, schema=body_schema)
    except:
        return False

    return True

# verify if already posted review
def already_reviewed(business_id,user_id):
    query = client.query(kind=REVIEWS)
    query.add_filter('user_id', '=', user_id)
    query.add_filter('business_id', '=', business_id)
    results = list(query.fetch())
    if results:
        return True
    return False

# verify business_id exists
def business_id_exists(business_id):
    # get key
    business_key = client.key(BUSINESSES, business_id)
    business = client.get(key=business_key)
    
    if business is None:
        return False
    else:   
        return True

# create a review
@app.route('/' + REVIEWS, methods=['POST'])
def post_review():
    try:
        content = request.get_json()
        if not content:
            return {"Error": "Missing JSON body"}, 400
    except Exception as e:
        return {"Error": f"Invalid JSON: {str(e)}"}, 400

    if request.content_type != 'application/json':
        return {"Error": "Content-Type must be application/json"}, 400

    if not validate_review(content):
        return (ERROR_WRONG_CONTENT, 400)
    
    business_id = content['business_id']
    
    if not business_id_exists(business_id):
        return(ERROR_NOT_FOUND, 404)

    if not already_reviewed(business_id, content["user_id"]):
        new_review = datastore.Entity(client.key(REVIEWS))
        new_review.update({
            "user_id": content["user_id"],
            "business_id": content["business_id"], 
            "stars": content["stars"], 
            
        })
        if "review_text" in content:
            new_review.update({
            "review_text": content["review_text"],
        }) 
        client.put(new_review)
        new_review["id"] = new_review.key.id
        return (new_review, 201)
    else:
        return (ERROR_ALREADY_POSTED, 409)

# get review by id
@app.route('/' + REVIEWS + '/<int:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    review_key = client.key(REVIEWS, review_id)
    review = client.get(key=review_key)
    if review is None:
        return (ERROR_REVIEW_NOT_FOUND, 404)
    else:
        review["id"] = review.key.id
        return review

# get all reviews by user
@app.route('/users' + '/<int:user_id>' + '/' + REVIEWS, methods=['GET'])
def get_review_by_user(user_id):
    query = client.query(kind=REVIEWS)
    query.add_filter('user_id', '=', user_id)
    
    results = list(query.fetch())
    for item in results:
        item["id"] = item.key.id
    return results

# edit review
@app.route('/' + REVIEWS + '/<int:review_id>', methods=['PUT'])
def put_review(review_id):
    try:
        content = request.get_json()
        if not content:
            return {"Error": "Missing JSON body"}, 400
    except Exception as e:
        return {"Error": f"Invalid JSON: {str(e)}"}, 400

    if not validate_update(content):
        return (ERROR_WRONG_CONTENT, 400)
    
    # get key
    review_key = client.key(REVIEWS, review_id)
    review = client.get(key=review_key)
    
    if review is None:
        return (ERROR_NOT_FOUND, 404)
    else:
        if "user_id" in content:
            review.update({
            "user_id": content["user_id"],
        })
        if "business_id" in content:
            review.update({
            "business_id": content["business_id"],
        })
        if "stars" in content:
            review.update({
            "stars": content["stars"],
        })
        if "review_text" in content:
            review.update({
            "review_text": content["review_text"],
        }) 
        client.put(review)
        review["id"] = review.key.id
        return review

# delete review
@app.route('/' + REVIEWS + '/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    # get key
    review_key = client.key(REVIEWS, review_id)
    review = client.get(key=review_key)
    
    if review is None:
        return ERROR_NOT_FOUND,404
    else:
        client.delete(review_key)
        return ('', 204)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
