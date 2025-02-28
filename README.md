# Review Site API

## Overview
This is a Flask-based RESTful API that allows users to create and manage businesses and reviews. The application uses Google Cloud Datastore for data storage and follows best practices for API design.

## Features
- Create, retrieve, update, and delete businesses.
- Create, retrieve, update, and delete reviews for businesses.
- Prevent users from submitting multiple reviews for the same business.
- Automatically delete reviews when a business is removed.

## Technologies Used
- Python
- Flask
- Google Cloud Datastore
- JSON Schema Validation

## Installation
### Prerequisites
- Python 3.x installed
- Google Cloud SDK installed and authenticated
- Google Cloud Datastore enabled

### Steps
1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the Flask server:
   ```sh
   python app.py
   ```

## API Endpoints
### Businesses
#### Create a Business
**POST /businesses**
```json
{
  "owner_id": 1,
  "name": "Example Business",
  "street_address": "123 Main St",
  "city": "Sample City",
  "state": "CA",
  "zip_code": 90001
}
```
Response:
```json
{
  "id": 123,
  "owner_id": 1,
  "name": "Example Business",
  "street_address": "123 Main St",
  "city": "Sample City",
  "state": "CA",
  "zip_code": 90001
}
```

#### Get a Business by ID
**GET /businesses/{business_id}**

#### Update a Business
**PUT /businesses/{business_id}**
```json
{
  "name": "Updated Business Name"
}
```

#### Delete a Business
**DELETE /businesses/{business_id}**

### Reviews
#### Create a Review
**POST /reviews**
```json
{
  "user_id": 2,
  "business_id": 123,
  "stars": 5,
  "review_text": "Great place!"
}
```

#### Update a Review
**PUT /reviews/{review_id}**
```json
{
  "stars": 4,
  "review_text": "Updated review text."
}
```

#### Delete a Review
**DELETE /reviews/{review_id}**

## Deployment
To deploy on Google App Engine:
1. Modify `app.yaml` if needed.
2. Deploy using:
   ```sh
   gcloud app deploy
   ```


