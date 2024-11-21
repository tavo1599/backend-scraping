import requests
from bs4 import BeautifulSoup
import schedule
import time
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import locale
import dateparser
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Función para convertir fechas usando dateparser
def convertir_fecha(fecha_texto):
    try:
        # Utiliza dateparser para convertir automáticamente la fecha al formato datetime
        fecha = dateparser.parse(fecha_texto, languages=['es'])
        if fecha:
            return fecha.strftime('%Y-%m-%d')  # Formato MySQL
        else:
            print(f"Error al interpretar la fecha: {fecha_texto}")
            return None
    except Exception as e:
        print(f"Error inesperado al convertir la fecha: {e}")
        return None

# locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# # Diccionario de traducción de meses
# meses_espanol_a_ingles = {
#     "enero": "January", "febrero": "February", "marzo": "March", "abril": "April",
#     "mayo": "May", "junio": "June", "julio": "July", "agosto": "August",
#     "septiembre": "September", "octubre": "October", "noviembre": "November", "diciembre": "December"
# }

# def traducir_mes(fecha_texto):
#     for mes_es, mes_en in meses_espanol_a_ingles.items():
#         if mes_es in fecha_texto.lower():
#             fecha_texto = fecha_texto.lower().replace(mes_es, mes_en)
#             break
#     return fecha_texto

# Función para convertir fechas al formato MySQL
# def convertir_fecha(fecha_texto):
#     try:
#         fecha_texto = traducir_mes(fecha_texto)  # Traducir el mes al inglés
#         return datetime.strptime(fecha_texto, '%d %B, %Y').strftime('%Y-%m-%d')
#     except ValueError as e:
#         print(f"Error al convertir la fecha: {e}")
#         return None

chrome_options = Options()
chrome_options.add_argument("--headless")  # Ejecutar en segundo plano
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# Configurar la conexión a MySQL
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
    
    # Función para verificar si un partido ya existe en la base de datos
def partido_existe(estado, fecha):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT COUNT(*) FROM partidos_conmebol WHERE estado = %s AND fecha = %s"
            cursor.execute(query, (estado, fecha))
            result = cursor.fetchone()
            return result[0] > 0
        except Error as e:
            print(f"Error al verificar la existencia del partido: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

# Función para guardar partidos en MySQL
def save_partido(data):
    if partido_existe(data['estado'], data['fecha']):
        print(f"Partido ya existente: {data['estado']} - {data['fecha']}")
        return

    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO partidos_conmebol (estado, logo_local, logo_visitante, fecha, hora)
            VALUES (%s, %s, %s, %s, %s)
            """
            values = (data['estado'], data['logo_local'], data['logo_visitante'], data['fecha'], data['hora'])
            cursor.execute(query, values)
            connection.commit()
            print("Partido guardado en MySQL.")
        except Error as e:
            print(f"Error al guardar el partido en MySQL: {e}")
        finally:
            cursor.close()
            connection.close()
            
            # Función para verificar si una posición ya existe en la base de datos
def posicion_existe(posicion):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT COUNT(*) FROM posiciones_conmebol WHERE posicion = %s"
            cursor.execute(query, (posicion,))
            result = cursor.fetchone()
            return result[0] > 0
        except Error as e:
            print(f"Error al verificar la existencia de la posición: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
            
            # Función para guardar la posición en la base de datos
def save_posicion(data):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            if posicion_existe(data['posicion']):
                # Actualizar la fila existente
                query = """
                UPDATE posiciones_conmebol
                SET bandera_url = %s, equipo = %s, jugados = %s, victoria = %s, empate = %s, 
                    derrota = %s, diferencia_goles = %s, puntos = %s
                WHERE posicion = %s
                """
                values = (
                    data['bandera_url'],
                    data['equipo'],
                    data['jugados'],
                    data['victoria'],
                    data['empate'],
                    data['derrota'],
                    data['diferencia_goles'],
                    data['puntos'],
                    data['posicion']
                )
                cursor.execute(query, values)
                print(f"Posición actualizada: {data['posicion']} - {data['equipo']}")
            else:
                # Insertar una nueva fila
                query = """
                INSERT INTO posiciones_conmebol (posicion, bandera_url, equipo, jugados, victoria, empate, derrota, diferencia_goles, puntos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    data['posicion'],
                    data['bandera_url'],
                    data['equipo'],
                    data['jugados'],
                    data['victoria'],
                    data['empate'],
                    data['derrota'],
                    data['diferencia_goles'],
                    data['puntos']
                )
                cursor.execute(query, values)
                print(f"Posición guardada: {data['posicion']} - {data['equipo']}")
            
            connection.commit()
        except Error as e:
            print(f"Error al guardar o actualizar la posición: {e}")
        finally:
            cursor.close()
            connection.close()

# Función para verificar si una noticia ya existe en la base de datos
def noticia_existe(titulo):
    connection = connect_to_mysql()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT COUNT(*) FROM noticias WHERE titulo = %s"
            cursor.execute(query, (titulo,))
            result = cursor.fetchone()
            return result[0] > 0
        except Error as e:
            print(f"Error al verificar la existencia de la noticia: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

# Función para subir datos a MySQL, evitando duplicados
# Función para subir datos a MySQL, evitando duplicados y asignando colección
def upload_to_mysql(data, coleccion):
    if noticia_existe(data['titulo']):
        print(f"Noticia ya existente: {data['titulo']}")
        return False  # Omitir la inserción si la noticia ya existe

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
            return True
        except Error as e:
            print(f"Error al insertar datos en MySQL: {e}")
            return False
        finally:
            cursor.close()
            connection.close()


# Función para convertir fechas al formato MySQL
# def convertir_fecha(fecha_texto):
#     try:
#         return datetime.strptime(fecha_texto, '%d %B, %Y').strftime('%Y-%m-%d')
#     except ValueError as e:
#         print(f"Error al convertir la fecha: {e}")
#         return None
    

# Función para el scraping de TV Sur

def scrape_posiciones():
    # Configurar opciones de Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.conmebol.com/eliminatorias-sudamericanas-2026-tabla-de-posiciones/")

    # Esperar a que cargue el contenido
    time.sleep(5)
    
    # Parsear con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    rows = soup.select("tbody tr")

    for row in rows:
        try:
            posicion = row.find("th").text.strip()
            bandera_url = row.find("img")["src"]
            equipo = row.find("td", class_="Opta-Team").text.strip()
            stats = [td.text.strip() for td in row.find_all("td")[2:]]
            
            data = {
                "posicion": int(posicion),
                "bandera_url": bandera_url,
                "equipo": equipo,
                "jugados": int(stats[0]),
                "victoria": int(stats[1]),
                "empate": int(stats[2]),
                "derrota": int(stats[3]),
                "diferencia_goles": int(stats[4]),
                "puntos": int(stats[5])
            }
            
            save_posicion(data)
        except Exception as e:
            print(f"Error al procesar una fila: {e}")

def scrape_conmebol_partidos():
    url = "https://www.conmebol.com/eliminatorias-sudamericanas-mundial-2026/"
    driver.get(url)
    
    # Esperar a que el contenido esté completamente cargado
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "opta-match"))
    )

    # Obtener el HTML generado y analizarlo con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Extraer los datos de los partidos
    matches_extracted = 0
    for match in soup.find_all("div", class_="opta-match"):
        try:
            estado = match.find("div", class_="opta-match__result").text.strip()
            logo_local = match.find("div", class_="opta-match__team-info--home").find("img")["src"]
            logo_visitante = match.find("div", class_="opta-match__team-info--away").find("img")["src"]
            
            # Fechas y horarios
            date_info = match.find_all("div", class_="opta-match__date")
            fecha = date_info[0].find("time").text.strip() if len(date_info) > 0 else "Fecha no disponible"
            hora = date_info[1].find("time").text.strip() if len(date_info) > 1 else "Horario no disponible"
            
            data = {
                "estado": estado,
                "logo_local": logo_local,
                "logo_visitante": logo_visitante,
                "fecha": fecha,
                "hora": hora
            }
            save_partido(data)
            matches_extracted += 1
        except AttributeError:
            print("Error en el procesamiento de un partido.")
    
    print(f"Total partidos guardados: {matches_extracted}")

def scrape_tvsur():
    url = 'https://www.tvsur.com.pe/category/noticias/local/'
    response = requests.get(url)
    noticias = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')
        img_elements = soup.find_all('img', class_='entry-thumb')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)

            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                title_tag = article_soup.find('h1', class_='entry-title')
                content_div = article_soup.find('div', class_='td-post-content')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join([p.text.strip() for p in paragraphs])
                    
                    # Convertir fecha
                    fecha_convertida = convertir_fecha(date.text.strip())

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title_tag.text.strip(),
                        'fuente': 'TV SUR',
                        'descripcion': description,
                        'image': img.get('data-img-url', 'No Image')
                    }

                    noticias.append(data)

        if noticias:
            for noticia in noticias:
                upload_to_mysql(noticia, 'noticia')
            print("Scraping completado y datos subidos a MySQL")
        else:
            print("No se encontraron noticias.")
    else:
        print("Error al realizar scraping.")

# Función para el scraping de Sin Fronteras
def scraping_sinfronteras():
    url = 'https://diariosinfronteras.com.pe/category/puno/'
    response = requests.get(url)
    noticiassf = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')

        for title_element in title_elements:
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                image_element = article_soup.find('img', class_='attachment-bd-normal size-bd-normal wp-post-image')
                content_div = article_soup.find('div', class_='post-content-bd')
                image_url = image_element['src'] if image_element else 'No Image'

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
                    
                    # Usa la fecha actual para esta fuente
                    fecha_convertida = datetime.now().strftime('%Y-%m-%d')

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'Sin Fronteras',
                        'descripcion': description,
                        'image': image_url
                    }
                    noticiassf.append(data)

        if noticiassf:
            for noticia in noticiassf:
                upload_to_mysql(noticia, 'noticia')
            print("Scraping completado y datos subidos a MySQL")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')

# Función para el scraping de Los Andes
def scraping_andes():
    url = 'https://losandes.com.pe/category/regional/'
    response = requests.get(url)
    noticiasandes = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title td-module-title')
        img_elements = soup.find_all('span', class_='entry-thumb td-thumb-css')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            image_url = img.get('data-img-url')
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                content_div = article_soup.find('div', class_='td_block_wrap tdb_single_content tdi_107 td-pb-border-top td_block_template_1 td-post-content tagdiv-type')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join([paragraph.text.strip() for paragraph in paragraphs])

                    # Convertir fecha
                    fecha_convertida = convertir_fecha(date.text.strip())

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'Los Andes',
                        'descripcion': description,
                        'image': image_url
                    }
                    noticiasandes.append(data)

        if noticiasandes:
            for noticia in noticiasandes:
                upload_to_mysql(noticia, 'noticia')
            print("Scraping completado y datos subidos a MySQL")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')
        
def scraping_sinfronterasdeportes():
    url = 'https://diariosinfronteras.com.pe/category/deportes/'
    response = requests.get(url)
    noticiassf = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')

        for title_element in title_elements:
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                image_element = article_soup.find('img', class_='attachment-bd-normal size-bd-normal wp-post-image')
                content_div = article_soup.find('div', class_='post-content-bd')
                image_url = image_element['src'] if image_element else 'No Image'

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join(paragraph.text.strip() for paragraph in paragraphs)

                    # Usa la fecha actual y conviértela
                    fecha_convertida = datetime.now().strftime('%Y-%m-%d')

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'Sin Fronteras',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticiassf.append(data)

        if noticiassf:
            for noticia in noticiassf:
                upload_to_mysql(noticia, 'deportes')
            print("Scraping completado y datos subidos a MySQL en la colección 'deportes'.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')


def scraping_andes_deportes():
    url = 'https://losandes.com.pe/category/deportes/'
    response = requests.get(url)
    noticias_andes = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title td-module-title')
        img_elements = soup.find_all('span', class_='entry-thumb td-thumb-css')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            image_url = img.get('data-img-url')
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                content_div = article_soup.find('div', class_='td_block_wrap tdb_single_content tdi_107 td-pb-border-top td_block_template_1 td-post-content tagdiv-type')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join(paragraph.text.strip() for paragraph in paragraphs)

                    # Convertir fecha
                    fecha_convertida = convertir_fecha(date.text.strip())

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'Los Andes',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_andes.append(data)

        if noticias_andes:
            for noticia in noticias_andes:
                upload_to_mysql(noticia, 'deportes')
            print("Scraping completado y datos subidos a MySQL en la colección 'deportes'.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')


def scraping_andes_politica():
    url = 'https://losandes.com.pe/category/politica/'
    response = requests.get(url)
    noticias_politica = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title td-module-title')
        img_elements = soup.find_all('span', class_='entry-thumb td-thumb-css')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            image_url = img.get('data-img-url')
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                content_div = article_soup.find('div', class_='td_block_wrap tdb_single_content tdi_107 td-pb-border-top td_block_template_1 td-post-content tagdiv-type')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join(paragraph.text.strip() for paragraph in paragraphs)

                    # Convertir fecha
                    fecha_convertida = convertir_fecha(date.text.strip())

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'Los Andes',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_politica.append(data)

        if noticias_politica:
            for noticia in noticias_politica:
                upload_to_mysql(noticia, 'politica')
            print("Scraping completado y datos subidos a MySQL en la colección 'politica'.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')


def scraping_sinfronteras_politica():
    url = 'https://diariosinfronteras.com.pe/category/politica/'
    response = requests.get(url)
    noticias_politica = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')

        for title_element in title_elements:
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                image_element = article_soup.find('img', class_='attachment-bd-normal size-bd-normal wp-post-image')
                content_div = article_soup.find('div', class_='post-content-bd')
                image_url = image_element['src'] if image_element else 'No Image'

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '

                    data = {
                        'fecha': 'septiembre 4, 2024',  # Puedes ajustar esto según necesites
                        'titulo': title,
                        'fuente': 'Sin Fronteras',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_politica.append(data)

        if noticias_politica:
            for noticia in noticias_politica:
                upload_to_mysql(noticia, 'politica')
            print("Scraping completado y datos subidos a MYSQL en la colección 'politica'.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página')
        
def scraping_tvsur_politica():
    url = 'https://www.tvsur.com.pe/category/noticias/nacional/'
    response = requests.get(url)
    noticias = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')
        img_elements = soup.find_all('img', class_='entry-thumb')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)

            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                title_tag = article_soup.find('h1', class_='entry-title')
                content_div = article_soup.find('div', class_='td-post-content')
                title = title_tag.text.strip()

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join(paragraph.text.strip() for paragraph in paragraphs)

                    # Convertir fecha
                    fecha_convertida = convertir_fecha(date.text.strip())

                    data = {
                        'fecha': fecha_convertida,
                        'titulo': title,
                        'fuente': 'TV SUR',
                        'descripcion': description.strip(),
                        'image': img.get('data-img-url', 'No Image')
                    }

                    noticias.append(data)

        if noticias:
            for noticia in noticias:
                upload_to_mysql(noticia, 'politica')
            print("Scraping completado y datos subidos a MySQL en la colección 'politica'.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al realizar scraping.')

def scrape_bbc():
    url = 'https://www.bbc.com/mundo/topics/c2lej05epw5t'  # URL de la página
    response = requests.get(url)
    noticias = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontrar todos los elementos de noticias
        noticia_elements = soup.find_all('li', class_='bbc-t44f9r')

        for noticia in noticia_elements:
            try:
                # Extraer imagen
                img_element = noticia.find('img')
                img_src = img_element['src'] if img_element else 'No Image'

                # Extraer título
                title_element = noticia.find('h2', class_='bbc-1slyjq2 e47bds20')
                title = title_element.text.strip() if title_element else 'No disponible'

                # Extraer fecha
                date_element = noticia.find('time', class_='promo-timestamp bbc-16jlylf e1mklfmt0')
                date = date_element.text.strip() if date_element else 'No disponible'

                # Convertir la fecha al formato MySQL
                fecha_convertida = convertir_fecha(date)

                # Guardar los datos en un diccionario
                data = {
                    'titulo': title,
                    'descripcion': 'No disponible',  # En este caso, no tienes una descripción específica
                    'fecha': fecha_convertida,
                    'fuente': 'BBC Mundo',
                    'image': img_src
                }

                noticias.append(data)
            except Exception as e:
                print(f"Error al procesar una noticia: {e}")

        if noticias:
            # Insertar cada noticia en la base de datos
            for noticia in noticias:
                upload_to_mysql(noticia, 'internacionales')  # 'internacionales' es la colección de la noticia
            print("Scraping de BBC completado y datos subidos a MySQL en la colección 'internacionales'.")
        else:
            print("No se encontraron noticias en BBC.")
    else:
        print("Error al realizar scraping en BBC. Código de estado:", response.status_code)


        
# Función para ejecutar todos los scrapers
def scrape_all():
    scrape_posiciones()
    scrape_conmebol_partidos()
    scrape_tvsur()
    scraping_sinfronteras()
    scraping_andes()
    scraping_sinfronterasdeportes()
    scraping_andes_deportes()
    scraping_andes_politica()
    scraping_sinfronteras_politica()
    scrape_bbc()
    # Agrega las demás funciones de scraping aquí
    
    

driver = webdriver.Chrome(options=chrome_options)
scrape_all()
driver.quit()

# Programación del scraping
schedule.every(0.0001).minutes.do(scrape_all)

while True:
    schedule.run_pending()
    time.sleep(1)
