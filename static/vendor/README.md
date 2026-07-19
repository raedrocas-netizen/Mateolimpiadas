# Dependencias frontend locales

Estos archivos se versionan en el repositorio para que la aplicación no
dependa de CDN externos durante la ejecución. No requieren npm ni un proceso de
build.

| Dependencia | Versión | Archivo | URL original | SHA-256 |
| --- | --- | --- | --- | --- |
| Bootstrap CSS | 5.3.3 | `bootstrap/css/bootstrap.min.css` | `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css` | `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8` |
| Bootstrap Bundle JS | 5.3.3 | `bootstrap/js/bootstrap.bundle.min.js` | `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js` | `0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c` |
| Socket.IO Client | 4.7.5 | `socket.io/socket.io.min.js` | `https://cdn.socket.io/4.7.5/socket.io.min.js` | `73eba16bc895fdfa454e27ecb80def31ede8d861f99e175ff93b110eabec044f` |

`bootstrap.bundle.min.js` ya incluye Popper. Las licencias MIT originales se
conservan en `bootstrap/LICENSE` y `socket.io/LICENSE`, además de los avisos que
incluyen los propios archivos distribuidos.

Para actualizar una dependencia se debe justificar la compatibilidad, copiar
el artefacto oficial exacto y actualizar su versión y SHA-256 en este archivo y
en `tests/test_frontend_vendor_assets.py`.
