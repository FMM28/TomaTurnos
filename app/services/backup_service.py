import os
import json
import shutil
import zipfile
import subprocess
from datetime import datetime
from typing import Tuple, Optional, Callable
import tempfile

from flask import current_app


class BackupService:

    @staticmethod
    def _get_backup_root() -> str:
        path = os.path.join(current_app.root_path, "backups")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _get_uploads_path() -> str:
        return os.path.join(current_app.root_path, "static", "uploads")

    @staticmethod
    def crear_respaldo(progress_callback: Optional[Callable[[str, int], None]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Genera respaldo completo del sistema:
        - Base de datos (solo datos, sin estructura - se usa Alembic para migraciones)
        - Archivos uploads
        """
        temp_folder = None
        credentials_file = None
        
        def report_progress(message: str, percentage: int):
            """Helper para reportar progreso"""
            if progress_callback:
                progress_callback(message, percentage)
            current_app.logger.info(f"Backup progress ({percentage}%): {message}")
        
        try:
            report_progress("Iniciando proceso de respaldo...", 5)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_root = BackupService._get_backup_root()

            temp_folder = os.path.join(backup_root, f"temp_{timestamp}")
            os.makedirs(temp_folder, exist_ok=True)

            report_progress("Obteniendo credenciales de base de datos...", 10)

            config = current_app.config
            db_user = config.get('DB_USER')
            db_password = config.get('DB_PASSWORD')
            db_host = config.get('DB_HOST', 'localhost')
            db_port = config.get('DB_PORT', 3306)
            db_name = config.get('DB_NAME')

            if not all([db_user, db_password, db_name]):
                return None, "Faltan credenciales de base de datos en la configuración"

            report_progress("Preparando archivo de credenciales...", 15)

            credentials_file = tempfile.NamedTemporaryFile(
                mode='w', 
                delete=False,
                suffix='.cnf'
            )
            credentials_file.write("[client]\n")
            credentials_file.write(f"user={db_user}\n")
            credentials_file.write(f"password={db_password}\n")
            credentials_file.write(f"host={db_host}\n")
            credentials_file.write(f"port={db_port}\n")
            credentials_file.close()

            os.chmod(credentials_file.name, 0o600)

            dump_path = os.path.join(temp_folder, "database.sql")

            report_progress("Generando respaldo de la base de datos...", 25)

            # Comando mariadb-dump usando archivo de credenciales
            # --no-create-info = solo datos, sin estructura (ya que usas Alembic)
            # --skip-triggers = omitir triggers (se crean con Alembic)
            dump_command = [
                "mariadb-dump",
                f"--defaults-file={credentials_file.name}",
                db_name,
                "--no-create-info",  # SOLO DATOS
                "--skip-triggers",    # Omitir triggers
                "--skip-routines",    # Omitir procedimientos almacenados
                "--skip-events",      # Omitir eventos
                "--single-transaction",
                "--quick",
                "--lock-tables=false",
                "--default-character-set=utf8mb4",
                "--complete-insert"   # Inserts completos
            ]

            # Ejecutar dump
            with open(dump_path, "w", encoding="utf-8") as dump_file:
                result = subprocess.run(
                    dump_command,
                    stdout=dump_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300
                )

            if result.returncode != 0:
                return None, f"Error al generar dump de base de datos: {result.stderr}"

            report_progress("Base de datos respaldada correctamente", 50)

            uploads_src = BackupService._get_uploads_path()
            uploads_dst = os.path.join(temp_folder, "uploads")

            if os.path.exists(uploads_src) and os.listdir(uploads_src):
                report_progress("Copiando archivos adjuntos...", 60)
                shutil.copytree(uploads_src, uploads_dst)
                report_progress("Archivos adjuntos copiados", 70)
            else:
                report_progress("No hay archivos adjuntos para respaldar", 70)

            # Generar metadata
            report_progress("Generando información del respaldo...", 75)
            
            metadata = {
                "fecha": timestamp,
                "database": db_name,
                "host": db_host,
                "port": db_port,
                "tipo": "respaldo_datos",
                "estructura": "alembic",
                "version": "2.0",
                "nota": "Este respaldo contiene solo datos. La estructura de la base de datos se gestiona mediante migraciones de Alembic."
            }

            with open(os.path.join(temp_folder, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

            instructions = """
INSTRUCCIONES DE RESTAURACIÓN
==============================

Este respaldo contiene SOLO LOS DATOS del sistema.
La estructura de la base de datos se gestiona mediante Alembic.

PASOS PARA RESTAURAR:

1. Restaurar la estructura de la base de datos:
   - Ejecuta las migraciones de Alembic: flask db upgrade

2. Restaurar los datos:
   - mysql -u [usuario] -p [nombre_db] < database.sql

3. Restaurar archivos adjuntos:
   - Copia la carpeta 'uploads' a static/uploads/

4. Reinicia la aplicación

IMPORTANTE:
- Asegúrate de tener la misma versión de Alembic
- Verifica que las migraciones estén actualizadas
- Haz un respaldo antes de restaurar
"""
            
            with open(os.path.join(temp_folder, "INSTRUCCIONES.txt"), "w", encoding="utf-8") as f:
                f.write(instructions)

            report_progress("Comprimiendo archivos...", 80)
            
            zip_filename = f"backup_{timestamp}.zip"
            zip_path = os.path.join(backup_root, zip_filename)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_folder)
                        zipf.write(full_path, rel_path)

            report_progress("Respaldo completado exitosamente", 100)
            
            current_app.logger.info(f"Backup creado exitosamente: {zip_filename}")
            return zip_path, None

        except subprocess.TimeoutExpired:
            report_progress("Error: Tiempo de espera excedido", 0)
            return None, "El proceso de backup excedió el tiempo límite"
        except Exception as e:
            current_app.logger.error(f"Error al crear backup: {str(e)}")
            report_progress(f"Error: {str(e)}", 0)
            return None, f"Error inesperado: {str(e)}"
        
        finally:
            if credentials_file is not None:
                try:
                    if hasattr(credentials_file, 'name') and os.path.exists(credentials_file.name):
                        os.unlink(credentials_file.name)
                        current_app.logger.info(f"Archivo de credenciales eliminado: {credentials_file.name}")
                except Exception as e:
                    current_app.logger.warning(f"No se pudo eliminar archivo de credenciales: {e}")
            
            if temp_folder and os.path.exists(temp_folder):
                try:
                    shutil.rmtree(temp_folder)
                    current_app.logger.info(f"Carpeta temporal eliminada: {temp_folder}")
                except Exception as e:
                    current_app.logger.warning(f"No se pudo eliminar carpeta temporal: {e}")