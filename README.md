Para ejecutar este script, copiar y editar el archivo config.py:

* `mv config.py.example config.py` 

y editar las variables `CX_ID`, `SMTP_HOST`, `SMTP_PORT`, `EMAIL_ADDRESS` y `EMAIL_PASSWORD`.

Ejecutar el script para crear la base de datos:

* `python3 paste_utils/create_db.py`

Editar el archivo `paste_utils/recipients.txt` con las direcciones de correo electrónico a quienes será enviado el email del script.

Ejecutar periodicamente el script:

* `python3 paste.py --query "string_busqueda" --site "site_url"`

Para ver más opciones:

* `python3 paste.py --help`

