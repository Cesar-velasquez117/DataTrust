# Requisitos de DataTrust

## 1. Propósito

DataTrust permite importar datos tabulares y evaluar su calidad mediante reglas configurables. El MVP prioriza resultados reproducibles, aislamiento de datos por usuario y una experiencia de uso sencilla.

## 2. Usuarios objetivo

- **Analista de datos:** importa datasets, define reglas, ejecuta validaciones e investiga incidencias.
- **Administrador de la plataforma:** mantiene el servicio y su configuración técnica. El MVP no requiere un panel administrativo avanzado.

## 3. Alcance funcional

### Incluido

- Registro e inicio de sesión.
- Gestión de datasets propios.
- Importación CSV acotada.
- Creación, consulta, edición, activación, desactivación y eliminación de reglas.
- Ejecución síncrona de validaciones.
- Métricas de calidad e incidencias por fila.
- Historial de ejecuciones con una fotografía de las reglas aplicadas.
- Exportación segura de incidencias a CSV.
- Pruebas automatizadas, CI y documentación de instalación.

### Fuera del MVP

- Importación de Excel, PDF u otros formatos.
- Integraciones con ERP, CRM o almacenes de datos externos.
- Procesamiento en tiempo real de grandes volúmenes.
- Colas, workers distribuidos o ejecución asíncrona.
- Corrección automática de datos.
- Reglas definidas mediante código arbitrario del usuario.
- Funcionalidades de IA generativa.
- Facturación, planes comerciales y administración multiempresa avanzada.

## 4. Requisitos funcionales

- **RF-01 — Autenticación:** permitir registrar una cuenta e iniciar sesión mediante credenciales.
- **RF-02 — Autorización:** cada usuario solo podrá acceder a sus propios datasets y a los recursos dependientes.
- **RF-03 — Datasets:** permitir crear, consultar, listar y eliminar datasets propios.
- **RF-04 — Importación:** aceptar CSV con encabezados válidos, almacenar las filas y conservar su número de origen.
- **RF-05 — Reglas:** permitir gestionar reglas `REQUIRED`, `EMAIL_FORMAT`, `UNIQUE` y `NUMERIC_RANGE`.
- **RF-06 — Validación:** ejecutar las reglas activas de un dataset de forma síncrona y persistir el resultado.
- **RF-07 — Métricas:** mostrar filas totales, válidas e inválidas, incidencias y tasa de cumplimiento.
- **RF-08 — Historial:** conservar el resultado y una fotografía de las reglas de cada ejecución.
- **RF-09 — Exportación:** permitir descargar las incidencias de una ejecución en CSV, protegiendo contra inyección de fórmulas.
- **RF-10 — Entorno reproducible:** ofrecer configuración local basada en Docker y comprobaciones automatizadas de calidad en CI.

## 5. Reglas de calidad

### REQUIRED

Comprueba que una celda tenga valor. `null`, una cadena vacía y una cadena compuesta únicamente por espacios se consideran ausentes. Los números `0` y el booleano `false` son valores válidos. La regla falla si la columna configurada no existe.

### EMAIL_FORMAT

Comprueba una estructura sintáctica básica de dirección de correo. No verifica que la dirección exista ni que pueda recibir mensajes. Los valores ausentes o no textuales incumplen esta regla.

### UNIQUE

Comprueba la unicidad de una columna o de una combinación de columnas. Todas las filas que formen parte de un grupo duplicado se marcan como incumplidoras, incluida la primera. Si algún componente de una clave compuesta está ausente, esa fila se omite en esta comprobación; la ausencia se puede detectar con `REQUIRED`.

Parámetros de normalización previstos: `trim_whitespace` y `case_sensitive`. Por defecto se recortan espacios externos y la comparación de texto no distingue mayúsculas de minúsculas.

### NUMERIC_RANGE

Comprueba que un valor sea numérico, finito y esté dentro de los límites configurados. `min` y `max` son opcionales, pero debe existir al menos uno. Se admiten opciones de inclusión para cada límite. La conversión textual utiliza el punto como separador decimal; no se interpretan booleanos como números.

### Comportamiento común

- Los datos originales no se modifican durante la validación.
- Solo se aceptan los tipos de regla enumerados.
- Los parámetros deben cumplir el esquema de cada tipo.
- No se permite ejecutar código Python, expresiones arbitrarias ni SQL proporcionado por usuarios.
- Cada incidencia identifica la fila, la regla, un código estable y un mensaje legible.
- Una fila que incumpla varias reglas genera varias incidencias, pero cuenta una sola vez como fila inválida.

## 6. Límites iniciales propuestos

Estos límites deberán comprobarse durante las pruebas del entorno de referencia:

- Tamaño máximo de CSV: 10 MB.
- Máximo de filas de datos: 10.000.
- Máximo de columnas: 30.
- Máximo de reglas activas por dataset: 20.
- Objetivo de validación: menos de 10 segundos para 10.000 filas y hasta 20 reglas activas en el entorno de referencia documentado.

Los límites deben comprobarse durante la lectura y el procesamiento, no únicamente después de cargar todo el archivo en memoria.

## 7. Definiciones de métricas

- `total_rows`: número de filas de datos evaluadas; excluye el encabezado.
- `valid_rows`: filas que no incumplen ninguna regla activa.
- `invalid_rows`: filas que incumplen una o más reglas activas.
- `total_issues`: número de incidencias individuales.
- `compliance_rate`: `valid_rows / total_rows * 100`.
- `violation_rate`: filas que incumplen una regla divididas por las filas evaluadas por esa regla, multiplicado por 100.

Debe cumplirse `valid_rows + invalid_rows = total_rows`. Cuando `total_rows` sea cero, la tasa de cumplimiento será `null`. Si no hay reglas activas, todas las filas se consideran válidas y no se generan incidencias. La tasa por regla será `null` si no se evaluaron filas para esa regla.

## 8. Contratos generales de API

La API estará versionada bajo `/api/v1` y usará JSON, salvo carga y descarga de archivos.

- Identificadores: UUID en formato de cadena.
- Fechas: ISO 8601 en UTC.
- Autenticación de endpoints privados: `Authorization: Bearer <access_token>`.
- Paginación de listados: `page` y `page_size`; predeterminado 20, máximo 100.
- Errores con estructura común: `error.code`, `error.message`, `error.details` y `error.request_id`.
- No se expondrá la existencia de recursos de otros usuarios; cuando corresponda se devolverá `404`.
- Los errores de datos de entrada no se confundirán con incidencias de calidad producidas por una ejecución válida.

### Endpoints previstos

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/auth/register` | Registrar usuario |
| POST | `/auth/login` | Iniciar sesión y obtener access token |
| GET | `/auth/me` | Consultar usuario autenticado |
| POST | `/datasets` | Crear dataset |
| GET | `/datasets` | Listar datasets propios |
| GET | `/datasets/{dataset_id}` | Consultar metadatos |
| POST | `/datasets/{dataset_id}/import` | Importar CSV |
| GET | `/datasets/{dataset_id}/rows` | Consultar filas paginadas |
| DELETE | `/datasets/{dataset_id}` | Eliminar dataset y dependencias según política definida |
| POST | `/datasets/{dataset_id}/rules` | Crear regla |
| GET | `/datasets/{dataset_id}/rules` | Listar reglas |
| GET | `/datasets/{dataset_id}/rules/{rule_id}` | Consultar regla |
| PATCH | `/datasets/{dataset_id}/rules/{rule_id}` | Modificar regla |
| DELETE | `/datasets/{dataset_id}/rules/{rule_id}` | Eliminar regla |
| POST | `/datasets/{dataset_id}/runs` | Ejecutar validación síncrona |
| GET | `/datasets/{dataset_id}/runs` | Consultar historial |
| GET | `/datasets/{dataset_id}/runs/{run_id}` | Consultar ejecución |
| GET | `/datasets/{dataset_id}/runs/{run_id}/issues` | Consultar incidencias paginadas |
| GET | `/datasets/{dataset_id}/runs/{run_id}/export` | Descargar incidencias en CSV |

### Códigos HTTP principales

- `200`: consulta o acción completada.
- `201`: recurso creado.
- `204`: eliminación sin cuerpo de respuesta.
- `400`: solicitud malformada o parámetros de consulta inválidos.
- `401`: autenticación ausente o inválida.
- `403`: acción no permitida para el usuario autenticado.
- `404`: recurso inexistente o que no debe revelarse.
- `409`: conflicto con el estado actual.
- `413`: archivo demasiado grande.
- `415`: tipo de contenido no admitido.
- `422`: estructura o parámetros semánticamente inválidos.
- `429`: exceso de solicitudes, si se configura limitación.
- `500`: error inesperado.
- `503`: dependencia necesaria no disponible.

Una validación que termina correctamente, pero encuentra filas incorrectas, es una ejecución exitosa; no debe responder con un error HTTP por esa razón.

## 9. Requisitos no funcionales

- **Seguridad:** contraseñas con hash resistente, tokens de corta duración, secretos fuera del repositorio y autorización por recurso.
- **Integridad:** importaciones atómicas y resultados de ejecución consistentes con sus métricas, incidencias y reglas históricas.
- **Mantenibilidad:** separación entre API, servicios, repositorios y motor de reglas.
- **Pruebas:** cobertura de reglas y casos límite, persistencia, permisos y flujo completo.
- **Usabilidad:** mensajes de error accionables, métricas comprensibles y navegación clara por dataset, ejecución e incidencia.
- **Reproducibilidad:** instrucciones de configuración y ejecución documentadas y verificadas.

## 10. Criterios de aceptación del MVP

1. Un desarrollador puede levantar el entorno siguiendo la documentación.
2. La aplicación se conecta a Oracle y aplica las migraciones.
3. Los CSV que exceden los límites o tienen estructura inválida se rechazan sin importación parcial.
4. Las cuatro reglas producen resultados correctos para casos normales y límite.
5. Las métricas son coherentes, incluida la validación sin filas o sin reglas.
6. Los usuarios no pueden consultar ni modificar recursos ajenos.
7. Las ejecuciones históricas no cambian al modificar reglas posteriormente.
8. El frontend permite completar el flujo de importar, configurar reglas, validar, consultar incidencias y exportar.
9. Las comprobaciones automatizadas se ejecutan en CI.
10. El README explica alcance, arquitectura, configuración y pruebas.

## 11. Riesgos y verificaciones previas

- Confirmar compatibilidad entre la versión elegida de Oracle Database Free, el driver de Python, SQLAlchemy y Alembic.
- Verificar el tipo de almacenamiento JSON disponible y su integración con el ORM.
- Medir consumo de memoria y duración de las validaciones síncronas.
- Probar rollback y consistencia transaccional.
- Revisar aislamiento entre usuarios y seguridad de la exportación.
- Mantener el alcance acotado para evitar introducir procesamiento distribuido antes de necesitarlo.
