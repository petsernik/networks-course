import uuid
from flask import Flask, jsonify, request, send_file
import os

app = Flask(__name__)


class Product:
    def __init__(self, product_id, name="", description=""):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.enriched = False
        self.icon_path = ""

    def to_dictionary(self):
        return {
            'id': self.product_id,
            'name': self.name,
            'description': self.description,
            'enriched': self.enriched
        }


products = dict()
working_folder = 'downloads'


@app.route('/')
def index():
    return "Hello, customers, this is my mini-market"


@app.route('/product', methods=['POST'])
def add_product():
    if (
            not request.json
            or 'name' not in request.json
            or 'description' not in request.json
    ):
        return "Bad request", 400

    product_id = int(uuid.uuid4())
    products[product_id] = Product(
        product_id=product_id,
        name=request.json['name'],
        description=request.json['description']
    )

    return jsonify(products[product_id].to_dictionary()), 201


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    if product_id not in products:
        return "Not Found", 404
    return jsonify(products[product_id].to_dictionary()), 200


@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if not request.json:
        return "Empty request", 400

    if product_id not in products:
        return "Not Found", 404

    if 'name' in request.json:
        products[product_id].name = request.json['name']

    if 'description' in request.json:
        products[product_id].description = request.json['description']

    return jsonify(products[product_id].to_dictionary()), 200


@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if product_id not in products:
        return "Not Found", 404

    return jsonify(products.pop(product_id).to_dictionary()), 200


@app.route('/products', methods=['GET'])
def get_product_list():
    return jsonify([
        products[idx].to_dictionary()
        for idx in products
    ]), 200


@app.route('/product/<int:product_id>/image', methods=['POST'])
def post_image(product_id):
    if product_id not in products:
        return "Not Found", 404

    if 'file' in request.files and request.files['file'].filename != "":
        image = request.files['file']
        products[product_id].icon_path = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        products[product_id].enriched = True
        return "OK", 200

    return "Got none picture", 400


@app.route('/product/<int:product_id>/image', methods=['GET'])
def get_image(product_id):
    if product_id not in products:
        return "Not Found", 404

    if not products[product_id].enriched:
        return "No picture", 200

    path = os.path.join(app.config["UPLOAD_FOLDER"], products[product_id].icon_path)
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    if not os.path.exists(working_folder):
        os.mkdir(working_folder)
    app.config['UPLOAD_FOLDER'] = working_folder
    app.run(debug=True)
