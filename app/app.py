from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from flask import request, jsonify


app = Flask(__name__)
CORS(app, supports_credentials=True)

# Permitir solicitudes desde el frontend

def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="scraping_db"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# @app.route('/api/scrape', methods=['POST'])
# def start_scraping():
#     try:
#         scrape_all()  # Ejecuta el scraping solo al recibir una solicitud POST
#         return jsonify({"message": "Scraping iniciado y completado con éxito"}), 200
#     except Exception as e:
#         print(f"Error al iniciar el scraping: {e}")
#         return jsonify({"error": f"Error al iniciar el scraping: {str(e)}"}), 500

# Clave secreta para JWT
app.config['SECRET_KEY'] = 'mi_secreto_jwt'  # Cambia esto por una clave secreta segura

@app.route('/api/register', methods=['POST'])
def register_user():
    try:
        print("Iniciando el proceso de registro")
        data = request.get_json()
        print("Datos recibidos:", data)

        nombre = data.get('nombre')
        email = data.get('email')
        contrasena = data.get('contrasena')
        id_rol = 3  # Asignar un rol predeterminado

        if not nombre or not email or not contrasena:
            print("Error: Faltan datos para el registro")
            return jsonify({"error": "Faltan datos para el registro"}), 400

        hashed_password = generate_password_hash(contrasena, method='pbkdf2:sha256')
        print("Contraseña encriptada:", hashed_password)

        connection = connect_to_mysql()
        if connection:
            try:
                cursor = connection.cursor()
                query = "INSERT INTO usuarios (nombre, email, contrasena, id_rol) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (nombre, email, hashed_password, id_rol))
                connection.commit()
                print("Usuario registrado con éxito")
                return jsonify({"message": "Usuario registrado con éxito"}), 201
            except Error as e:
                print(f"Error al registrar el usuario: {e}")
                return jsonify({"error": "No se pudo registrar el usuario"}), 500
            finally:
                cursor.close()
                connection.close()

        print("Error: No se pudo conectar a la base de datos")
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    except Exception as e:
        print(f"Excepción no manejada: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Endpoint para verificar el rol del usuario
@app.route('/api/verify-role', methods=['GET'])
def verify_role():
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({"error": "Token no proporcionado"}), 401

    try:
        # Decodificar el token
        decoded_token = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['user_id']

        # Conectar a la base de datos y obtener el rol del usuario
        connection = connect_to_mysql()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT id_rol FROM usuarios WHERE id = %s"
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()

                if user:
                    return jsonify({"rol": user['id_rol']}), 200
                else:
                    return jsonify({"error": "Usuario no encontrado"}), 404
            except Error as e:
                print(f"Error al verificar el rol: {e}")
                return jsonify({"error": "Error en el servidor"}), 500
            finally:
                cursor.close()
                connection.close()

        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401


# Endpoint para iniciar sesión
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    contrasena = data.get('contrasena')

    if not email or not contrasena:
        return jsonify({"error": "Faltan datos para iniciar sesión"}), 400

    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, nombre, contrasena, id_rol FROM usuarios WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['contrasena'], contrasena):
                token = jwt.encode({
                    'user_id': user['id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, app.config['SECRET_KEY'], algorithm='HS256')

                # Devuelve el token, el rol y el nombre del usuario en la respuesta
                return jsonify({
                    "token": token,
                    "rol": user['id_rol'],
                    "nombre": user['nombre'],  # Incluye el nombre del usuario
                    "message": "Inicio de sesión exitoso"
                }), 200
            else:
                return jsonify({"error": "Correo o contraseña incorrectos"}), 401
        except Error as e:
            print(f"Error al iniciar sesión: {e}")
            return jsonify({"error": "Error en el servidor"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

@app.route('/api/increment-views/<int:noticia_id>', methods=['POST'])
def increment_views(noticia_id):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            update_query = "UPDATE noticias SET views = views + 1 WHERE id = %s"
            cursor.execute(update_query, (noticia_id,))
            connection.commit()
            return jsonify({"message": "Contador de vistas actualizado"}), 200
        except Error as e:
            print(f"Error al actualizar el contador de vistas: {e}")
            return jsonify({"error": "Error en el servidor"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500


@app.route('/api/incrementar-vistas', methods=['POST'])
def incrementar_vistas():
    data = request.get_json()
    noticia_id = data.get('id')

    if not noticia_id:
        return jsonify({"error": "ID de la noticia es requerido"}), 400

    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "UPDATE noticias SET views = views + 1 WHERE id = %s"
            cursor.execute(query, (noticia_id,))
            connection.commit()
            return jsonify({"message": "Vistas incrementadas exitosamente"}), 200
        except Error as e:
            print(f"Error al incrementar vistas: {e}")
            return jsonify({"error": "Error al incrementar vistas"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500



@app.route('/api/noticias-mas-leidas', methods=['GET'])
def get_mas_leidas():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM noticias ORDER BY views DESC LIMIT 5"
            cursor.execute(query)
            mas_leidas = cursor.fetchall()
            return jsonify(mas_leidas), 200
        except Error as e:
            print(f"Error al obtener las noticias más leídas: {e}")
            return jsonify({"error": "Error en el servidor"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500


# Endpoint para eliminar un usuario
@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "DELETE FROM usuarios WHERE id = %s"
            cursor.execute(query, (id,))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({"message": "Usuario eliminado correctamente"}), 200
            else:
                return jsonify({"error": "Usuario no encontrado"}), 404
        except Error as e:
            print(f"Error al eliminar el usuario: {e}")
            return jsonify({"error": "Error al eliminar el usuario"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

# Endpoint para actualizar un usuario
@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def update_usuario(id):
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')

    if not nombre or not email:
        return jsonify({"error": "Faltan datos para actualizar el usuario"}), 400

    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s"
            cursor.execute(query, (nombre, email, id))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({"message": "Usuario actualizado correctamente"}), 200
            else:
                return jsonify({"error": "Usuario no encontrado"}), 404
        except Error as e:
            print(f"Error al actualizar el usuario: {e}")
            return jsonify({"error": "Error al actualizar el usuario"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

# Endpoint para actualizar el rol de un usuario
@app.route('/api/usuarios/<int:id>/rol', methods=['PUT'])
def update_usuario_rol(id):
    data = request.get_json()
    id_rol = data.get('id_rol')

    if not id_rol:
        return jsonify({"error": "Faltan datos para actualizar el rol"}), 400

    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "UPDATE usuarios SET id_rol = %s WHERE id = %s"
            cursor.execute(query, (id_rol, id))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({"message": "Rol del usuario actualizado correctamente"}), 200
            else:
                return jsonify({"error": "Usuario no encontrado"}), 404
        except Error as e:
            print(f"Error al actualizar el rol del usuario: {e}")
            return jsonify({"error": "Error al actualizar el rol del usuario"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

@app.route('/api/noticias/fuente-count', methods=['GET'])
def get_noticias_count_by_fuente():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT fuente, COUNT(*) as total
                FROM noticias
                GROUP BY fuente
            """
            cursor.execute(query)
            fuente_counts = cursor.fetchall()
            return jsonify(fuente_counts)
        except Error as e:
            print(f"Error al obtener el conteo de noticias por fuente: {e}")
            return jsonify({"error": "Error al cargar el conteo de noticias por fuente"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre, email, id_rol FROM usuarios")
            usuarios = cursor.fetchall()
            return jsonify(usuarios)
        except Error as e:
            print(f"Error al obtener usuarios: {e}")
            return jsonify({"error": "Error al cargar los usuarios"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

# Endpoint para obtener la cantidad de noticias por categoría
@app.route('/api/noticias/count', methods=['GET'])
def get_noticias_count_by_category():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT coleccion, COUNT(*) as total
                FROM noticias
                GROUP BY coleccion
            """
            cursor.execute(query)
            counts = cursor.fetchall()
            return jsonify(counts)
        except Error as e:
            print(f"Error al obtener el conteo de noticias: {e}")
            return jsonify({"error": "Error al cargar el conteo de noticias"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500


# Endpoint para obtener todas las noticias (Home)
@app.route('/api/home', methods=['GET'])
def get_all_noticias():
    query = "SELECT titulo, descripcion, fecha, fuente, image FROM noticias ORDER BY fecha DESC"
    return fetch_noticias(query)

# Endpoint para obtener noticias de política
@app.route('/api/politica', methods=['GET'])
def get_politica_noticias():
    query = "SELECT titulo, descripcion, fecha, fuente, image FROM noticias WHERE coleccion = 'politica' ORDER BY fecha DESC"
    return fetch_noticias(query)

# Endpoint para obtener noticias de deportes
@app.route('/api/deportes', methods=['GET'])
def get_deportes_noticias():
    query = "SELECT titulo, descripcion, fecha, fuente, image FROM noticias WHERE coleccion = 'deportes' ORDER BY fecha DESC"
    return fetch_noticias(query)

# Nuevo endpoint para obtener los partidos
@app.route('/api/partidos', methods=['GET'])
def get_partidos():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT estado, logo_local, logo_visitante, fecha, hora FROM partidos_conmebol ORDER BY fecha DESC"
            cursor.execute(query)
            partidos = cursor.fetchall()
            return jsonify(partidos)
        except Error as e:
            print(f"Error al obtener partidos: {e}")
            return jsonify({"error": "Error al cargar los partidos"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

# Endpoint para obtener la tabla de posiciones
@app.route('/api/posiciones', methods=['GET'])
def get_posiciones():
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM posiciones_conmebol ORDER BY posicion ASC")
            posiciones = cursor.fetchall()
            return jsonify(posiciones)
        except Error as e:
            print(f"Error al obtener posiciones: {e}")
            return jsonify({"error": "Error al cargar las posiciones"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500


# Función auxiliar para ejecutar las consultas y devolver las noticias
def fetch_noticias(query):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            noticias = cursor.fetchall()
            return jsonify(noticias)
        except Error as e:
            print(f"Error al obtener noticias: {e}")
            return jsonify({"error": "Error al cargar las noticias"}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

if __name__ == '__main__':
    app.run(debug=True)
