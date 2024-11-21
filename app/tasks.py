from apscheduler.schedulers.background import BackgroundScheduler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from app import connect_to_mysql  # Importa tu función de conexión a MySQL
import datetime

# Configuración del programador
scheduler = BackgroundScheduler()

# Función para enviar correos diarios
def enviar_correos_diarios():
    try:
        connection = connect_to_mysql()
        if not connection:
            print("No se pudo conectar a la base de datos")
            return

        # Obtener las últimas 3 noticias
        cursor = connection.cursor(dictionary=True)
        query_news = """
            SELECT titulo, descripcion, fecha 
            FROM noticias 
            ORDER BY fecha DESC 
            LIMIT 3
        """
        cursor.execute(query_news)
        noticias = cursor.fetchall()

        if not noticias:
            print("No hay noticias recientes para enviar.")
            return

        # Obtener los correos de los usuarios con rol 5
        query_users = "SELECT email FROM usuarios WHERE id_rol = 5"
        cursor.execute(query_users)
        usuarios = cursor.fetchall()

        if not usuarios:
            print("No hay usuarios VIP para enviar correos.")
            return

        # Configuración del servidor SMTP
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "llamasmanis@gmail.com"  # Cambia esto
        smtp_password = "triciclistak@ch3ro"  # Cambia esto

        # Crear y enviar correos
        for usuario in usuarios:
            email = usuario['email']
            message = MIMEMultipart("alternative")
            message["Subject"] = "Últimas Noticias de Diario Mani"
            message["From"] = smtp_user
            message["To"] = email

            html_content = "<h1>Últimas Noticias</h1><ul>"
            for noticia in noticias:
                html_content += f"""
                <li>
                    <h2>{noticia['titulo']}</h2>
                    <p>{noticia['descripcion']}</p>
                    <small>{noticia['fecha'].strftime('%d/%m/%Y %H:%M')}</small>
                </li>
                """
            html_content += "</ul>"

            message.attach(MIMEText(html_content, "html"))

            # Enviar el correo
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, email, message.as_string())

        print("Correos enviados exitosamente.")
    except Exception as e:
        print(f"Error al enviar correos: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Agregar la tarea al programador
scheduler.add_job(enviar_correos_diarios, 'cron', hour=8, minute=0)  # Ajusta la hora
