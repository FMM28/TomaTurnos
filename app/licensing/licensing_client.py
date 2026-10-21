from __future__ import annotations

import base64
import functools
import hashlib
import json
import os
import platform
import random
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from flask_wtf.csrf import CSRFProtect
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


class LicenseError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class NetworkError(Exception):
    """No se pudo contactar al servidor (distinto de que el servidor rechace la licencia)."""


# Errores del servidor que NO deben borrar el token local (son transitorios).
_TRANSIENT_CODES = {"server_error", "rate_limited"}


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


# ---------------------------------------------------------------- utilidades de plataforma
def _machine_id() -> str:
    """Identificador estable de la máquina según el sistema operativo."""
    if os.name == "nt":
        try:
            import winreg
            # KEY_WOW64_64KEY: un Python de 32 bits en Windows de 64 bits lee la misma clave.
            access = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography", 0, access) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                if value:
                    return str(value).strip()
        except OSError:
            pass
    else:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                value = Path(path).read_text().strip()
                if value:
                    return value
            except OSError:
                continue
    # Último recurso (basado en MAC, menos estable).
    return str(uuid.getnode())


@contextmanager
def _file_lock(target: Path, timeout: float = 10.0) -> Iterator[None]:
    """Bloqueo exclusivo entre procesos usando un archivo .lock junto al destino."""
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(target.name + ".lock")
    with open(lock_path, "a+b") as fh:
        locked = False
        deadline = time.monotonic() + timeout
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        break
                    time.sleep(0.05)
        else:
            import fcntl
            while True:
                try:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        break
                    time.sleep(0.05)
        try:
            yield
        finally:
            if locked:
                try:
                    if os.name == "nt":
                        import msvcrt
                        fh.seek(0)
                        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(fh, fcntl.LOCK_UN)
                except OSError:
                    pass


def default_storage_path(product: str) -> str:
    """Ruta por defecto para license.json. Pasa una ruta explícita si corres como servicio."""
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
    return str(base / product / "license.json")


class LicenseClient:
    CLOCK_SKEW = 300          # segundos de tolerancia al comparar relojes
    HIGH_WATER_STEP = 60      # cada cuántos segundos se persiste el reloj máximo visto

    def __init__(self, server_url: str, product: str, public_key: str,
                 license_key: str | None = None, storage_path: str | None = None,
                 http=None, timeout: float = 8.0, refresh_before_days: float = 2.0,
                 clock: Callable[[], float] = time.time):
        self.server_url = server_url.rstrip("/")
        self.product = product
        self.public_key = public_key
        self.storage = Path(storage_path or default_storage_path(product))
        self.timeout = timeout
        self.refresh_before = refresh_before_days * 86400
        self.clock = clock
        self._license_key = license_key or os.getenv("LICENSE_KEY")
        self._http = http  # cualquier objeto con .post(url, json=, timeout=) (requests, httpx…)
        self._cache: tuple[float, dict] | None = None
        self._lock = threading.RLock()
        self._fingerprint: str | None = None
        self._stop = threading.Event()

    # ------------------------------------------------------------ huella de máquina
    def fingerprint(self) -> str:
        """Hash estable de la máquina, ligado al producto (no sirve para otro producto)."""
        if self._fingerprint is None:
            parts = [_machine_id(), platform.system(), platform.machine()]
            raw = "|".join(parts) + "|" + self.product
            self._fingerprint = hashlib.sha256(raw.encode()).hexdigest()
        return self._fingerprint

    # ------------------------------------------------------------ almacenamiento local
    def _load(self) -> dict:
        try:
            data = json.loads(self.storage.read_text())
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save(self, data: dict) -> None:
        """Escritura atómica. Llamar con el _file_lock tomado."""
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.storage.with_name(f"{self.storage.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(data))
        if os.name != "nt":
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
        # En Windows os.replace falla con PermissionError si alguien tiene el destino abierto
        # un instante (antivirus, otro worker leyendo). Reintentamos brevemente.
        for attempt in range(6):
            try:
                os.replace(tmp, self.storage)
                return
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.05 * (attempt + 1))

    def _update(self, mutate: Callable[[dict], None]) -> dict:
        """Lee-modifica-escribe license.json bajo bloqueo entre procesos."""
        with _file_lock(self.storage):
            data = self._load()
            mutate(data)
            self._save(data)
            return data

    # ------------------------------------------------------------ red
    def _post(self, path: str, body: dict) -> dict:
        http = self._http
        if http is None:
            import requests
            http = requests
        try:
            resp = http.post(f"{self.server_url}{path}", json=body, timeout=self.timeout)
        except Exception as exc:  # errores de conexión, DNS, timeout…
            raise NetworkError(str(exc)) from exc
        if resp.status_code >= 500:
            raise NetworkError(f"servidor respondió {resp.status_code}")
        try:
            data = resp.json()
        except ValueError:
            raise LicenseError("server_error", f"Respuesta inesperada ({resp.status_code})")
        if resp.status_code >= 400:
            err = data.get("error") if isinstance(data, dict) else None
            if isinstance(err, dict) and "code" in err:
                raise LicenseError(err["code"], err.get("message", ""))
            raise LicenseError("server_error", f"Respuesta inesperada ({resp.status_code})")
        if not isinstance(data, dict):
            raise LicenseError("server_error", "Respuesta inesperada del servidor")
        return data

    # ------------------------------------------------------------ verificación offline
    def _verify(self, token: str, fresh: bool = False) -> dict:
        """`fresh=True`: el token acaba de llegar del servidor; si la firma no cuadra, lo más
        probable es que la clave pública configurada sea otra (no que alguien lo editara)."""
        try:
            verify_key = VerifyKey(_b64d(self.public_key))
        except Exception:  # base64 roto o longitud distinta de 32 bytes
            raise LicenseError("invalid_public_key",
                               "La clave pública configurada no tiene un formato válido")
        try:
            body, sig = token.split(".")
            verify_key.verify(body.encode(), _b64d(sig))
            payload = json.loads(_b64d(body))
        except BadSignatureError:
            if not fresh:
                raise LicenseError("invalid_token", "El token de licencia no es válido")
            raise LicenseError("bad_signature",
                               "La firma del token no coincide con la clave pública configurada "
                               "(¿clave pública equivocada o servidor de licencias distinto?)")
        except (ValueError, TypeError):
            raise LicenseError("invalid_token", "El token de licencia no es válido")
        if not isinstance(payload, dict) or not isinstance(payload.get("exp"), (int, float)):
            raise LicenseError("invalid_token", "El token de licencia no es válido")
        if payload.get("product") != self.product:
            raise LicenseError("product_mismatch", "La licencia es de otro producto")
        if payload.get("fp") != self.fingerprint():
            raise LicenseError("fingerprint_mismatch",
                               "La licencia está activada en otra máquina")
        return payload

    def _advance_clock(self, data: dict) -> bool:
        """Detecta retrocesos del reloj. Actualiza data['high_water'] en memoria.

        Devuelve True si el valor avanzó lo bastante como para valer la pena persistirlo.
        """
        now = self.clock()
        high = data.get("high_water", 0)
        if now < high - self.CLOCK_SKEW:
            raise LicenseError("clock_tampered", "El reloj del sistema es inconsistente")
        if now - high > self.HIGH_WATER_STEP:
            data["high_water"] = now
            return True
        return False

    # ------------------------------------------------------------ API pública
    def activate(self, license_key: str | None = None) -> dict:
        """Activa esta instalación con la clave (requiere internet). Guarda el token."""
        key = license_key or self._license_key
        if not key:
            raise LicenseError("no_key", "Falta la clave de licencia")
        out = self._post("/v1/activate", {
            "license_key": key, "product": self.product,
            "fingerprint": self.fingerprint(), "hostname": socket.gethostname(),
            "two_phase": True})
        token = out.get("token")
        if not isinstance(token, str):
            self._abort_quietly(key, "server_error")
            raise LicenseError("server_error", "Respuesta inesperada del servidor")
        try:
            payload = self._verify(token, fresh=True)
        except LicenseError as exc:
            # El servidor dejó la activación PENDIENTE y no podemos usar el token: avisamos
            # para que la registre como fallida y libere el cupo.
            self._abort_quietly(key, exc.code)
            raise
        # Token verificado: el servidor la registra como exitosa. Si esto falla, el token no
        # se guarda (el servidor cerraría la activación pendiente de todos modos).
        self._post("/v1/activate/confirm", {"license_key": key, "fingerprint": self.fingerprint()})
        now = self.clock()
        with self._lock:
            self._update(lambda d: d.update(license_key=key, token=token, high_water=now))
            self._license_key = key
            self._cache = None
        return payload

    def _abort_quietly(self, key: str, reason: str) -> None:
        try:
            self._post("/v1/activate/abort", {"license_key": key, "reason": reason,
                                              "fingerprint": self.fingerprint()})
        except (LicenseError, NetworkError):
            pass  # mejor esfuerzo: si no llega, el servidor cierra la pendiente a los 5 min

    def _refresh(self) -> dict:
        """Pide un token nuevo. Si el servidor rechaza la licencia, se borra el token local."""
        with _file_lock(self.storage):
            data = self._load()
            key = data.get("license_key") or self._license_key
            if not key:
                raise LicenseError("not_activated", "Esta instalación no está activada")

            # Otro proceso (worker) pudo haber renovado mientras esperábamos el bloqueo.
            current = data.get("token")
            if current:
                try:
                    p = self._verify(current)
                    if p["exp"] - self.clock() >= self.refresh_before:
                        return p
                except LicenseError:
                    pass

            try:
                out = self._post("/v1/validate", {
                    "license_key": key, "product": self.product,
                    "fingerprint": self.fingerprint()})
            except LicenseError as exc:
                if exc.code not in _TRANSIENT_CODES:
                    data.pop("token", None)  # revocada / expirada / no activada: ya no sirve
                    self._save(data)
                self._cache = None
                raise

            token = out.get("token")
            if not isinstance(token, str):
                raise LicenseError("server_error", "Respuesta inesperada del servidor")
            payload = self._verify(token, fresh=True)
            data.update(token=token, license_key=key)
            self._advance_clock(data)
            self._save(data)
            self._cache = None
            return payload

    def refresh(self) -> dict:
        with self._lock:
            return self._refresh()

    def check(self, allow_refresh: bool = True) -> dict:
        """Devuelve el payload verificado o lanza LicenseError.

        Funciona sin internet mientras el token no haya expirado. Si está por expirar
        intenta renovarlo; si no hay red, sigue con el token actual hasta su vencimiento.
        """
        with self._lock:
            data = self._load()
            token = data.get("token")
            if not token:
                raise LicenseError("not_activated", "Esta instalación no está activada")
            payload = self._verify(token)
            if self._advance_clock(data):
                now = self.clock()
                self._update(lambda d: d.__setitem__("high_water", max(d.get("high_water", 0), now)))
            remaining = payload["exp"] - self.clock()

            if allow_refresh and remaining < self.refresh_before:
                try:
                    return self._refresh()
                except NetworkError:
                    pass  # sin red: nos quedamos con el token actual si aún sirve
            if remaining <= -self.CLOCK_SKEW:
                raise LicenseError(
                    "offline_grace_expired",
                    "No se pudo validar la licencia con el servidor. Conéctate a internet.")
            return payload

    def is_valid(self) -> bool:
        try:
            self.check()
            return True
        except (LicenseError, NetworkError):
            return False

    def has_feature(self, name: str) -> bool:
        try:
            return name in self.cached_check().get("features", [])
        except LicenseError:
            return False

    def deactivate(self) -> None:
        """Libera esta instalación en el servidor (para moverla a otra máquina)."""
        with self._lock:
            data = self._load()
            key = data.get("license_key") or self._license_key
            if key:
                self._post("/v1/deactivate", {"license_key": key, "fingerprint": self.fingerprint()})
            self.storage.unlink(missing_ok=True)
            self._cache = None

    # ------------------------------------------------------------ uso en la app
    def cached_check(self, ttl: float = 60.0) -> dict:
        """check() con caché corta, para llamarlo en cada petición sin leer disco siempre.

        La caché nunca sirve un token ya vencido (más allá de la tolerancia de reloj).
        """
        now = time.monotonic()
        cached = self._cache
        if (cached and now - cached[0] < ttl
                and cached[1]["exp"] + self.CLOCK_SKEW > self.clock()):
            return cached[1]
        payload = self.check(allow_refresh=False)
        self._cache = (now, payload)
        return payload

    def ensure_licensed(self) -> None:
        """Lanza LicenseError si no hay licencia válida. Úsalo dentro de servicios, workers, CLI."""
        self.cached_check()

    def licensed(self, fn):
        """Decorador para servicios/funciones: exige licencia válida antes de ejecutar.

        En métodos estáticos va DEBAJO de @staticmethod:
            @staticmethod
            @client.licensed
            def create(...): ...
        """
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            self.ensure_licensed()
            return fn(*args, **kwargs)
        return wrapper

    def requires_feature(self, feature: str):
        """Decorador de ruta Flask: exige licencia válida que incluya `feature` (p. ej. en demos)."""
        def deco(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                from flask import jsonify
                try:
                    payload = self.cached_check()
                except LicenseError as exc:
                    return jsonify(error=exc.code, message=exc.message), 403
                if feature not in payload.get("features", []):
                    return jsonify(error="feature_not_licensed",
                                   message=f"Tu licencia no incluye '{feature}'"), 403
                return fn(*args, **kwargs)
            return wrapper
        return deco

    def start_background_refresh(self, every_hours: float = 6.0) -> threading.Thread:
        """Hilo demonio que renueva el token periódicamente (las peticiones nunca esperan a la red)."""
        interval = every_hours * 3600

        def loop():
            while not self._stop.is_set():
                try:
                    self.check(allow_refresh=True)
                except (LicenseError, NetworkError):
                    pass
                except Exception:
                    pass  # el hilo nunca debe morir por un error inesperado
                # Jitter para que varios workers no pidan renovación a la vez.
                self._stop.wait(interval + random.uniform(0, interval * 0.1))

        t = threading.Thread(target=loop, name="license-refresh", daemon=True)
        t.start()
        return t

    def stop_background_refresh(self) -> None:
        self._stop.set()


def init_flask(app, csrf: CSRFProtect, client: LicenseClient,
               exempt_endpoints: tuple[str, ...] = ("static",),
               exempt_paths: tuple[str, ...] = ("/health", "/license/activate", "/license/status"),
               background_refresh: bool = True) -> None:
    """Bloquea toda la app (HTTP 403) si no hay licencia válida.

    Las rutas exentas se comparan de forma EXACTA (no por prefijo).
    Registra también POST /license/activate:
        curl -X POST localhost:5000/license/activate -d '{"license_key":"XXXXX-..."}' \\
             -H 'Content-Type: application/json'
    """
    from flask import jsonify, request

    exempt_set = {p.rstrip("/") or "/" for p in exempt_paths}

    @app.errorhandler(LicenseError)
    def _license_error(exc: LicenseError):
        return jsonify(error=exc.code, message=exc.message), 403

    @csrf.exempt
    @app.post("/license/activate")
    def _license_activate():
        key = (request.get_json(silent=True) or {}).get("license_key")
        try:
            payload = client.activate(key)
        except LicenseError as exc:
            return jsonify(error=exc.code, message=exc.message), 400
        except NetworkError:
            return jsonify(error="network", message="No se pudo contactar al servidor de licencias"), 503
        return jsonify(ok=True, features=payload.get("features", []))

    @app.get("/license/status")
    def _license_status():
        try:
            p = client.cached_check()
        except LicenseError as exc:
            return jsonify(valid=False, error=exc.code), 403
        return jsonify(valid=True, license_expires=p.get("lic_exp"))

    @app.before_request
    def _enforce_license():
        path = request.path.rstrip("/") or "/"
        if request.endpoint in exempt_endpoints or path in exempt_set:
            return None
        client.cached_check()  # LicenseError -> errorhandler (403)
        return None

    if background_refresh:
        client.start_background_refresh()
