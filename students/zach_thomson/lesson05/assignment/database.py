# pylint: disable=R0914, C0103
'''
Mongo DB assignment
'''
import csv
import os
import logging
from pymongo import MongoClient

#logging setup
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

#formatting and file name
LOG_FORMAT = "%(asctime)s %(filename)s:%(lineno)-3d %(levelname)s %(message)s"
FORMATTER = logging.Formatter(LOG_FORMAT)
LOG_FILE = 'db.log'

#handling setup
FILE_HANDLER = logging.FileHandler(LOG_FILE)
FILE_HANDLER.setFormatter(FORMATTER)

CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setFormatter(FORMATTER)

LOGGER.addHandler(FILE_HANDLER)
LOGGER.addHandler(CONSOLE_HANDLER)


class MongoDBConnection():
    """MongoDB Connection"""

    def __init__(self, host='127.0.0.1', port=27017):
        """ be sure to use the ip address not name for local windows"""
        self.host = host
        self.port = port
        self.connection = None

    def __enter__(self):
        self.connection = MongoClient(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


def import_data(directory_name, product_file, customer_file, rentals_file):
    '''
    Function takes a directory name and three csv files as input (product data,
    customer data, rentals data) and creates a MongoDB database.
    Returns 2 tuples:
    1) Record count of number of products, customers and rentals added
    2) A count with any errors that occured in same order
    '''
    product_added = 0
    customer_added = 0
    rentals_added = 0

    product_errors = 0
    customer_errors = 0
    rental_errors = 0

    mongo = MongoDBConnection()

    with mongo:
        db = mongo.connection.media

        #Create product collection
        product_db = db['product']
        #only use drop for resetting database
        #product_db.drop()
        try:
            with open(os.path.join(directory_name, product_file)) as csvfile:
                product_reader = csv.DictReader(csvfile)
                for row in product_reader:
                    product_added += 1
                    new_product = {'product_id':row['product_id'],
                                   'description':row['description'],
                                   'product_type':row['product_type'],
                                   'quantity_available':row['quantity_available']}
                    LOGGER.info('%s added to database', new_product['product_id'])
                    product_db.insert_one(new_product)
        except FileNotFoundError:
            product_errors += 1

        #Create customer collection
        customer_db = db['customer']
        #only use drop for resetting database
        #customer_db.drop()
        try:
            with open(os.path.join(directory_name, customer_file)) as csvfile:
                customer_reader = csv.DictReader(csvfile)
                for row in customer_reader:
                    customer_added += 1
                    new_customer = {'user_id':row['user_id'],
                                    'name':row['name'],
                                    'address':row['address'],
                                    'phone_number':row['phone_number'],
                                    'email':row['email']}
                    LOGGER.info('%s added to database', new_customer['user_id'])
                    customer_db.insert_one(new_customer)
        except FileNotFoundError:
            customer_errors += 1

        #Create rentals collection
        rentals_db = db['rentals']
        #only use drop for resetting database
        #rentals_db.drop()
        try:
            with open(os.path.join(directory_name, rentals_file)) as csvfile:
                rental_reader = csv.DictReader(csvfile)
                for row in rental_reader:
                    rentals_added += 1
                    new_rental = {'user_id':row['user_id'],
                                  'product_id':row['product_id']}
                    LOGGER.info('%s rental added to database', new_rental['product_id'])
                    rentals_db.insert_one(new_rental)
        except FileNotFoundError:
            rental_errors += 1

    return [(product_added, customer_added, rentals_added),
            (product_errors, customer_errors, rental_errors)]


def show_available_products():
    '''returns a dict of products listed as available with fields:
    product_id, description, product_type, quantity available'''

    mongo = MongoDBConnection()

    product_dict = {}
    with mongo:
        db = mongo.connection.media
        product_db = db['product']
        avail_product = product_db.find({'quantity_available': {'$gt': '0'}})
        for item in avail_product:
            product_dict[item['product_id']] = {'description': item['description'],
                                                'product_type': item['product_type'],
                                                'quantity_available': item['quantity_available']}
    return product_dict


def show_rentals(product_id):
    '''returns a dict with the info from users who rented matching product_id:
    user_id, name, address, phone_number, email'''

    mongo = MongoDBConnection()

    rentals_dict = {}
    with mongo:
        db = mongo.connection.media
        customer_db = db['customer']
        rentals_db = db['rentals']
        for renter in rentals_db.find({'product_id': product_id}):
            for customer in customer_db.find({'user_id': renter['user_id']}):
                rentals_dict[customer['user_id']] = {'name': customer['name'],
                                                     'address': customer['address'],
                                                     'phone_number': customer['phone_number'],
                                                     'email': customer['email']}
    return rentals_dict
