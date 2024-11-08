# Añade al inicio las importaciones para MySQL
import mysql.connector
from mysql.connector import Error

# Define las funciones para MySQL
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="scraping_db"
        )
        if connection.is_connected():
            print("Conexión exitosa a MySQL")
            return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def upload_to_mysql(data, coleccion):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO noticias (titulo, descripcion, fecha, fuente, image, coleccion)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (data['titulo'], data['descripcion'], data['fecha'], data['fuente'], data['image'], coleccion)
            cursor.execute(query, values)
            connection.commit()
            print(f"Datos insertados exitosamente en MySQL en la colección '{coleccion}'")
        except Error as e:
            print(f"Error al insertar datos en MySQL: {e}")
        finally:
            cursor.close()
            connection.close()


# Usa upload_to_mysql() en lugar de la función de Firebase en el flujo de scraping
data = {
    "titulo": "Ejemplo de noticia",
    "descripcion": "Esta es una noticia de prueba.",
    "fecha": "2024-11-05",
    "fuente": "Fuente de prueba",
    "image": "https://ejemplo.com/imagen.jpg"
}
upload_to_mysql(data)
