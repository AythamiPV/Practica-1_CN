from flask import Flask, request, jsonify
from pydantic import ValidationError
import psycopg2
from botocore.exceptions import ClientError
from models.product import Product
from db.factory import DatabaseFactory
import time
import os  
import sys  

app = Flask(__name__)

# Inicializar base de datos de forma lazy para evitar problemas en el startup
_db_instance = None

def get_db():
    """Obtiene la instancia de base de datos (singleton lazy)"""
    global _db_instance
    if _db_instance is None:
        print("Inicializando base de datos...", file=sys.stderr)
        try:
            _db_instance = DatabaseFactory.create()
            print("Base de datos inicializada exitosamente", file=sys.stderr)
        except Exception as e:
            print(f"Error inicializando DB: {e}", file=sys.stderr)
            raise
    return _db_instance

@app.before_request
def before_request():
    """Log de requests"""
    print(f"[{time.time()}] {request.method} {request.path}", file=sys.stderr)

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
        if not data:
            return jsonify({'error': 'No se proporcionaron datos JSON'}), 400
            
        product = Product(**data)
        created = get_db().create_product(product)
        return jsonify(created.model_dump()), 201
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Obtener producto por ID
@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = get_db().get_product(product_id)
        if product:
            return jsonify(product.model_dump()), 200
        return jsonify({'error': 'Producto no encontrado'}), 404
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Listar todos los productos
@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        products = get_db().get_all_products()
        return jsonify([p.model_dump() for p in products]), 200
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Actualizar producto
@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos JSON'}), 400
            
        product = Product(**data)
        updated = get_db().update_product(product_id, product)
        if updated:
            return jsonify(updated.model_dump()), 200
        return jsonify({'error': 'Producto no encontrado'}), 404
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Eliminar producto
@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        if get_db().delete_product(product_id):
            return '', 204
        return jsonify({'error': 'Producto no encontrado'}), 404
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check SIMPLIFICADO temporalmente"""
    try:
        print("Health check iniciado", file=sys.stderr)
        
        # Primero, prueba si Flask está funcionando
        response_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'app': 'running'
        }
        
        # Luego intenta conectar a la DB (pero no falles si no puede)
        try:
            # Usa get_db() en lugar de crear nueva conexión
            db = get_db()
            
            # Hacer una consulta simple usando tu DatabaseFactory
            # Si estamos usando PostgreSQL, podemos usar una consulta directa
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                database=os.getenv('DB_NAME'),
                connect_timeout=2
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            conn.close()
            
            response_data['database'] = 'connected'
            print("Health check: DB conectada", file=sys.stderr)
            
        except Exception as db_error:
            response_data['database'] = 'disconnected'
            response_data['db_error'] = str(db_error)
            print(f"Health check: DB error - {db_error}", file=sys.stderr)
            # No fallar completamente, solo marcar DB desconectada
            # El health check aún puede retornar 200 para permitir que la app arranque
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Health check ERROR: {e}", file=sys.stderr)
        return jsonify({
            'status': 'unhealthy',
            'timestamp': time.time(),
            'error': str(e)
        }), 503

if __name__ == '__main__':
    print("Iniciando aplicación Flask...", file=sys.stderr)
    # Mostrar variables de entorno (sin password)
    print(f"DB_HOST: {os.getenv('DB_HOST')}", file=sys.stderr)
    print(f"DB_NAME: {os.getenv('DB_NAME')}", file=sys.stderr)
    print(f"DB_USER: {os.getenv('DB_USER')}", file=sys.stderr)
    app.run(host='0.0.0.0', port=8080, debug=True)