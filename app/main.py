from flask import Flask, request, jsonify
from pydantic import ValidationError
import psycopg2
from botocore.exceptions import ClientError
from models.product import Product
from db.factory import DatabaseFactory

app = Flask(__name__)

try:
    db = DatabaseFactory.create()
except ValueError as e:
    raise RuntimeError(f"Error initializing DB: {e}") from e

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,x-api-key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# Crear producto
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        product = Product(**data)
        created = db.create_product(product)
        return jsonify(created.model_dump()), 201
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

# Obtener producto por ID
@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = db.get_product(product_id)
        if product:
            return jsonify(product.model_dump()), 200
        return jsonify({'error': 'Producto no encontrado'}), 404
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

# Listar todos los productos
@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        products = db.get_all_products()
        return jsonify([p.model_dump() for p in products]), 200
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

# Actualizar producto
@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        product = Product(**data)
        updated = db.update_product(product_id, product)
        if updated:
            return jsonify(updated.model_dump()), 200
        return jsonify({'error': 'Producto no encontrado'}), 404
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

# Eliminar producto
@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        if db.delete_product(product_id):
            return '', 204
        return jsonify({'error': 'Producto no encontrado'}), 404
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
