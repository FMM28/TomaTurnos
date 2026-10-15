import json

import click
import requests


@click.command("activate")
@click.argument("clave")
@click.option(
    "--url",
    default="http://localhost:5000",
    show_default=True,
    help="URL base del servidor Flask.",
)
def activate(clave, url):
    """Activa una licencia llamando a POST /license/activate.

    Uso: flask activate 638SU-47MRV-DTH5D-ZF4VS
    """
    endpoint = f"{url.rstrip('/')}/license/activate"

    try:
        resp = requests.post(
            endpoint,
            json={"license_key": clave},
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        raise click.ClickException(
            f"No se pudo conectar a {endpoint}. ¿Está corriendo el servidor?"
        )
    except requests.exceptions.Timeout:
        raise click.ClickException(f"Tiempo de espera agotado en {endpoint}.")

    try:
        body = json.dumps(resp.json(), indent=2, ensure_ascii=False)
    except ValueError:
        body = resp.text

    if resp.ok:
        click.secho(f"Licencia activada (HTTP {resp.status_code})", fg="green")
        click.echo(body)
    else:
        click.secho(f"Error al activar (HTTP {resp.status_code})", fg="red", err=True)
        click.echo(body, err=True)
        raise SystemExit(1)