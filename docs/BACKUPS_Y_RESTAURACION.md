# Backups y restauración

## Alcance y principios

MateOlimpiadas Web mantiene dos recursos persistentes independientes:

1. PostgreSQL contiene materias, cuestionarios, preguntas, respuestas, partidas y demás datos relacionales.
2. El Persistent Disk de Render contiene las imágenes en `/opt/render/project/src/static/uploads`.

Por esa separación se usan dos workflows independientes. `Backup Database` crea diariamente un dump lógico de PostgreSQL en formato custom. `Backup Images` transmite diariamente `static/uploads` por SSH y comprime en el runner de GitHub, no en Render. Ambos también admiten ejecución manual, cifran el contenido con AES-256-CBC y PBKDF2 antes de subirlo y publican únicamente archivos cifrados como GitHub Actions Artifacts.

Los artifacts no se guardan en Git, en la rama `main`, en Flask ni en el Persistent Disk. GitHub conserva los artifacts de base de datos 30 días y los de imágenes 60 días. La contraseña de cifrado debe conservarse también en un gestor de contraseñas seguro fuera de GitHub: un secret no puede leerse después de guardarlo y, si se pierde la contraseña, los backups no se pueden recuperar.

La instancia PostgreSQL Free de Render no dispone de backups administrados ni Point-in-Time Recovery (PITR). Además, una instancia Free puede expirar. El propietario debe comprobar periódicamente en el panel de Render el tipo de instancia, la fecha o política de expiración y el estado del servicio. No se debe asumir que una característica de otro plan protege esta base.

## Diferencia entre las tres protecciones

| Protección | Contenido | Ubicación | Uso principal | Limitación |
| --- | --- | --- | --- | --- |
| Backup PostgreSQL | Dump lógico portable creado por `pg_dump` | GitHub Actions Artifact cifrado | Recrear la base en PostgreSQL compatible | No incluye imágenes ni permite PITR |
| Backup de imágenes | Árbol exacto `static/uploads` e inventario | GitHub Actions Artifact cifrado | Recuperar archivos en una carpeta temporal o un disco nuevo | Es una copia a nivel de archivos, separada de PostgreSQL |
| Snapshot del Persistent Disk | Estado del volumen a nivel de infraestructura | Render, si está disponible para el servicio y plan | Recuperación rápida del volumen completo | No protege PostgreSQL, permanece con el mismo proveedor y no sustituye la copia externa |

La disponibilidad, retención y operación de snapshots debe verificarse en el panel y la documentación vigente de Render. Estos workflows no crean snapshots.

## Activación

Cada workflow tiene dos activadores:

- `workflow_dispatch`: siempre permite una ejecución manual.
- `schedule`: intenta una ejecución programada, pero el job solo comienza cuando la Repository Variable `BACKUPS_ENABLED` vale exactamente `true`.

Las programaciones son:

- Base de datos: todos los días a las 07:17 UTC (01:17 de Guatemala).
- Imágenes: todos los días a las 07:43 UTC (01:43 de Guatemala).

GitHub ejecuta los schedules desde la rama predeterminada. Durante la implementación se debe dejar `BACKUPS_ENABLED` sin crear o con `false`. Después de integrar los workflows, se hacen y validan primero ambos backups manuales; solo entonces se cambia a `true`.

## Configuración requerida en GitHub

En **Settings > Secrets and variables > Actions**, crear exactamente estos Repository Secrets:

| Secret | Contenido |
| --- | --- |
| `BACKUP_DATABASE_URL` | External Database URL de Render o, preferiblemente, URL de un usuario dedicado de solo lectura con permisos suficientes para `pg_dump` |
| `BACKUP_ENCRYPTION_PASSWORD` | Contraseña larga, aleatoria y exclusiva para cifrar los dos tipos de backup |
| `RENDER_SSH_PRIVATE_KEY` | Clave privada dedicada exclusivamente a estos backups |

Crear exactamente estas Repository Variables:

| Variable | Contenido |
| --- | --- |
| `BACKUPS_ENABLED` | `false` durante la preparación; `true` solo después de validar los backups manuales |
| `POSTGRES_MAJOR_VERSION` | Versión mayor del servidor, por ejemplo `16`, sin asumirla ni copiar este ejemplo sin verificar Render |
| `RENDER_SSH_HOST` | Host SSH mostrado por Render, sin usuario ni opciones adicionales |
| `RENDER_SSH_USER` | Usuario SSH mostrado por Render |
| `RENDER_SSH_KNOWN_HOSTS` | Línea o líneas completas de `known_hosts`, obtenidas por un canal confiable y verificadas contra la huella de Render |

No guardar valores reales en el repositorio. No obtener ni aceptar una huella desconocida dentro del workflow. La variable `RENDER_SSH_KNOWN_HOSTS` debe prepararse fuera del workflow y compararse con la huella publicada o mostrada por Render mediante un canal confiable.

## Responsabilidades del propietario de Render

1. Confirmar el tipo y la versión mayor real de PostgreSQL.
2. Crear, si es posible, un usuario dedicado de solo lectura para el backup y otorgarle acceso de lectura a todos los esquemas, tablas y secuencias que debe incluir `pg_dump`, incluidas futuras tablas. No cambiar el esquema para esta tarea.
3. Copiar la External Database URL correspondiente y entregarla por un canal seguro al administrador de GitHub.
4. Crear un par de claves SSH dedicado. Instalar únicamente la clave pública en el Web Service y entregar la clave privada por un canal seguro.
5. Entregar el host, usuario y huella SSH oficial. Verificar independientemente la línea que se usará en `known_hosts`.
6. Confirmar que `/opt/render/project/src/static/uploads` es el punto montado y legible por el usuario SSH.
7. Revisar periódicamente expiración y salud de PostgreSQL Free y estado/capacidad del Persistent Disk de 2 GB.

La operación normal de backup SSH solo ejecuta pruebas de lectura y `tar -cf -`; no crea archivos ni comprime en Render.

## Responsabilidades del administrador de GitHub

1. Integrar los tres archivos revisados mediante pull request.
2. Crear los Secrets y Variables anteriores sin imprimir sus valores en logs o incidencias.
3. Mantener `BACKUPS_ENABLED=false` o ausente durante la configuración.
4. Ejecutar primero `Backup Database` y después `Backup Images` de forma manual.
5. Descargar ambos artifacts, verificar sus SHA-256, descifrarlos y probar su restauración local/temporal.
6. Solo después de una prueba satisfactoria, establecer `BACKUPS_ENABLED=true`.
7. Revisar periódicamente que los runs terminen correctamente y que haya artifacts dentro de sus ventanas de 30 y 60 días.
8. Rotar claves y contraseña mediante un procedimiento que conserve acceso a backups históricos. Los archivos antiguos siguen necesitando la contraseña con la que se cifraron.

## Primer backup manual de PostgreSQL

1. Asegurarse de que el workflow ya esté en la rama predeterminada de GitHub.
2. En el repositorio, abrir **Actions**.
3. Seleccionar **Backup Database**.
4. Pulsar **Run workflow**.
5. Elegir la rama que contiene el workflow aprobado y confirmar **Run workflow**. La ejecución manual funciona aunque `BACKUPS_ENABLED` sea `false` o no exista.
6. Abrir el run y comprobar que terminaron correctamente la creación con `pg_dump`, la validación con `pg_restore --list`, el cifrado y la subida.
7. Confirmar que el artifact se llama `mateolimpiadas-db-<timestamp>` y contiene solamente:
   - `mateolimpiadas-db-<timestamp>.dump.enc`;
   - su archivo `.sha256`;
   - el archivo de metadatos no sensibles.
8. Descargar, verificar y restaurar el dump en una base local vacía siguiendo las secciones posteriores.

## Primer backup manual de imágenes

1. Confirmar con el propietario de Render la clave pública instalada y la huella de host usada en `RENDER_SSH_KNOWN_HOSTS`.
2. En **Actions**, seleccionar **Backup Images**.
3. Pulsar **Run workflow**.
4. Elegir la rama aprobada y confirmar **Run workflow**. No es necesario habilitar los schedules.
5. Comprobar que el run validó el host, transmitió `static/uploads`, creó el inventario, comprimió en GitHub, cifró y subió el artifact.
6. Confirmar que el artifact se llama `mateolimpiadas-images-<timestamp>` y contiene solamente:
   - `mateolimpiadas-images-<timestamp>.tar.gz.enc`;
   - su archivo `.sha256`.
7. Descargar, verificar, descifrar y extraer el paquete primero en una carpeta temporal.

## Descargar artifacts

1. Abrir **Actions** y seleccionar el workflow correspondiente.
2. Abrir el run exitoso.
3. En la sección **Artifacts**, pulsar el nombre del artifact.
4. Extraer localmente el ZIP descargado en una carpeta dedicada.

El permiso para descargar artifacts debe limitarse a personas autorizadas. La capa de cifrado con contraseña sigue siendo obligatoria aunque GitHub proteja su almacenamiento y transporte.

## Verificar SHA-256

Ejecutar la verificación antes de descifrar. Ubicarse en la carpeta extraída del artifact.

Linux:

```bash
sha256sum --check mateolimpiadas-db-<timestamp>.dump.enc.sha256
sha256sum --check mateolimpiadas-images-<timestamp>.tar.gz.enc.sha256
```

Windows PowerShell, una vez por cada archivo:

```powershell
$encryptedFile = ".\mateolimpiadas-db-<timestamp>.dump.enc"
$checksumFile = "${encryptedFile}.sha256"
$expected = (Get-Content -LiteralPath $checksumFile -Raw).Split()[0].ToLowerInvariant()
$actual = (Get-FileHash -LiteralPath $encryptedFile -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "El SHA-256 no coincide." }
"SHA-256 correcto: $actual"
```

Para imágenes, cambiar `$encryptedFile` por `mateolimpiadas-images-<timestamp>.tar.gz.enc`.

## Descifrar backups

Se necesita OpenSSL y la contraseña exacta usada por el workflow. No escribir la contraseña como argumento ni guardarla en un script.

Linux:

```bash
read -rsp 'Contraseña de backup: ' BACKUP_ENCRYPTION_PASSWORD && echo
export BACKUP_ENCRYPTION_PASSWORD
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -in mateolimpiadas-db-<timestamp>.dump.enc \
  -out mateolimpiadas-db-<timestamp>.dump \
  -pass env:BACKUP_ENCRYPTION_PASSWORD
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -in mateolimpiadas-images-<timestamp>.tar.gz.enc \
  -out mateolimpiadas-images-<timestamp>.tar.gz \
  -pass env:BACKUP_ENCRYPTION_PASSWORD
unset BACKUP_ENCRYPTION_PASSWORD
```

Windows PowerShell:

```powershell
$env:BACKUP_ENCRYPTION_PASSWORD = Read-Host "Contraseña de backup" -MaskInput
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 `
  -in ".\mateolimpiadas-db-<timestamp>.dump.enc" `
  -out ".\mateolimpiadas-db-<timestamp>.dump" `
  -pass env:BACKUP_ENCRYPTION_PASSWORD
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 `
  -in ".\mateolimpiadas-images-<timestamp>.tar.gz.enc" `
  -out ".\mateolimpiadas-images-<timestamp>.tar.gz" `
  -pass env:BACKUP_ENCRYPTION_PASSWORD
Remove-Item Env:BACKUP_ENCRYPTION_PASSWORD
```

Trabajar únicamente con estas copias descifradas en una máquina controlada y borrarlas al finalizar la validación.

## Validar y restaurar PostgreSQL localmente

Usar `pg_restore` de la misma versión mayor configurada en `POSTGRES_MAJOR_VERSION` o una versión compatible. Primero validar el catálogo sin restaurar:

```bash
pg_restore --list mateolimpiadas-db-<timestamp>.dump > restore-list.txt
test -s restore-list.txt
```

Crear una base local realmente vacía. No apuntar nunca estos comandos a Render ni reutilizar una URL de producción:

```bash
createdb mateolimpiadas_restore
export LOCAL_DATABASE_URL='postgresql://localhost/mateolimpiadas_restore'
pg_restore \
  --exit-on-error \
  --no-owner \
  --no-acl \
  --dbname="${LOCAL_DATABASE_URL}" \
  mateolimpiadas-db-<timestamp>.dump
```

Si la base local ya contiene objetos, eliminarla y crear otra vacía en vez de usar `--clean` contra un destino dudoso. Revisar el código de salida de `pg_restore` y sus mensajes.

Comparar los conteos obtenidos de la fuente antes del cambio crítico con los de la restauración local. La consulta es de solo lectura:

```sql
SELECT 'materias' AS tabla, COUNT(*) AS total FROM materias
UNION ALL
SELECT 'cuestionarios', COUNT(*) FROM cuestionarios
UNION ALL
SELECT 'preguntas', COUNT(*) FROM preguntas
UNION ALL
SELECT 'respuestas', COUNT(*) FROM respuestas
ORDER BY tabla;
```

Ejecutarla con `psql` una vez sobre la fuente de solo lectura y guardar el resultado de forma segura; después ejecutarla sobre `mateolimpiadas_restore`. Los cuatro conteos deben coincidir. Si la fuente ya se perdió, compararlos con el último registro previo disponible y complementar con inspección de relaciones, preguntas, respuestas e imágenes. Los conteos no sustituyen una prueba funcional.

## Extraer y validar el backup de imágenes

El paquete descifrado contiene un TAR sin comprimir con `static/uploads` y un inventario JSON. Extraer siempre en una carpeta temporal nueva:

```bash
mkdir -p restore-images/package restore-images/extracted
tar -xzf mateolimpiadas-images-<timestamp>.tar.gz -C restore-images/package
cat restore-images/package/*-inventory.json
tar -tf restore-images/package/mateolimpiadas-images-<timestamp>.tar
tar -xf restore-images/package/mateolimpiadas-images-<timestamp>.tar \
  -C restore-images/extracted
```

El resultado esperado es:

```text
restore-images/extracted/static/uploads/Usuario/archivo.ext
```

Comparar la cantidad de archivos y el tamaño total con `file_count` y `total_size_bytes` del inventario. Inspeccionar algunas imágenes de cada carpeta. No extraer primero sobre el repositorio ni sobre un Persistent Disk.

## Restaurar imágenes a un Persistent Disk nuevo

Esta operación es deliberadamente manual y requiere autorización del propietario de Render:

1. Crear y montar un Persistent Disk nuevo exactamente en `/opt/render/project/src/static/uploads` según la configuración del servicio.
2. Detener escrituras de la aplicación o poner el servicio en una ventana de mantenimiento.
3. Validar localmente el inventario y el árbol extraído.
4. Confirmar que el destino está vacío y que el usuario SSH corresponde al servicio.
5. Desde el directorio que contiene `static/`, transmitir el árbol sin cambiar su ruta:

```bash
tar -C restore-images/extracted -cf - static/uploads | \
ssh -i ./render_backup_key \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=./render_known_hosts \
  RENDER_SSH_USER@RENDER_SSH_HOST \
  "tar -C /opt/render/project/src -xf -"
```

6. Comprobar remotamente conteos, tamaños, propietario y permisos.
7. Iniciar la aplicación y validar preguntas con imágenes antes de reabrir el servicio.

El `-C /opt/render/project/src` conserva exactamente `static/uploads/...`. No cambiarlo por una extracción directa dentro de `uploads`, porque duplicaría o perdería componentes de la ruta. Para recuperar solo archivos borrados accidentalmente en un disco existente, comparar primero la carpeta temporal y copiar únicamente los archivos aprobados; no sobrescribir todo el disco por defecto.

## Antes de un cambio crítico

1. Ejecutar manualmente **Backup Database**.
2. Ejecutar manualmente **Backup Images**.
3. Esperar que ambos runs terminen correctamente.
4. Descargar ambos artifacts antes de continuar.
5. Verificar los dos SHA-256.
6. Descifrar y ejecutar `pg_restore --list` sobre el dump.
7. Extraer las imágenes en una carpeta temporal y comparar el inventario.
8. Para cambios de riesgo alto, completar también una restauración PostgreSQL local vacía y comparar los cuatro conteos.

## Procedimientos ante incidentes

### Pérdida de PostgreSQL

Congelar cambios, descargar el backup válido más reciente, comprobar SHA-256 y restaurarlo primero en PostgreSQL local vacío. Validar catálogo, conteos y relaciones. El propietario crea después una instancia de reemplazo; la restauración a ese destino se hace manualmente durante una ventana aprobada y la aplicación se reconfigura solo tras validar el nuevo servicio.

### Expiración de PostgreSQL Free

Tratarla como pérdida de la instancia. No esperar que Render proporcione backup administrado o PITR. Usar el artifact externo más reciente, probarlo localmente y crear/restaurar una base de reemplazo. Revisar con mayor frecuencia la expiración para actuar antes del vencimiento.

### Pérdida completa del Persistent Disk

Crear un disco nuevo con el punto de montaje exacto, descargar y verificar el último artifact de imágenes, extraerlo localmente y seguir el procedimiento manual de restauración. Contrastar el inventario y probar imágenes desde juez, participante y pantalla pública.

### Eliminación accidental de imágenes

No restaurar todo automáticamente. Descargar y verificar el backup, extraerlo en una carpeta temporal, identificar las rutas faltantes con el inventario y copiar solo las aprobadas. Confirmar luego permisos, rutas y visualización.

## Regla de seguridad para toda restauración

Nunca restaurar automáticamente producción. Todo dump debe restaurarse primero en un PostgreSQL local vacío y todo paquete de imágenes debe extraerse primero en una carpeta temporal. La escritura posterior en un servicio o Persistent Disk de reemplazo necesita revisión humana, ventana aprobada, destino confirmado y una validación final de la aplicación.
