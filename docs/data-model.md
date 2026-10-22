# Modelo de datos lógico

## 1. Objetivos

El modelo de datos debe permitir gestionar datasets por usuario, almacenar las filas importadas, configurar reglas de calidad y conservar resultados históricos que no cambien cuando se editen las reglas.

Los nombres y tipos descritos aquí son una especificación lógica. Los tipos físicos, restricciones específicas de Oracle, índices y sintaxis de migración se decidirán durante el preflight técnico.

## 2. Entidades

### USERS

Representa una cuenta de usuario.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador | PK, UUID lógico |
| `email` | Correo de inicio de sesión | Obligatorio, único |
| `password_hash` | Hash de contraseña | Obligatorio |
| `created_at` | Fecha de creación | Obligatorio |

El hash de contraseña nunca se devuelve mediante la API.

### DATASETS

Representa un conjunto de datos perteneciente a un usuario.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador | PK |
| `user_id` | Propietario | FK a `USERS.id` |
| `name` | Nombre visible | Obligatorio |
| `status` | Estado del dataset | Valor controlado |
| `created_at` | Fecha de creación | Obligatorio |

El estado podrá representar, como mínimo, un dataset vacío y uno con datos importados. Los valores definitivos se enumerarán en los schemas del backend.

### DATASET_ROWS

Representa una fila importada desde un dataset.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador interno | PK |
| `dataset_id` | Dataset de pertenencia | FK a `DATASETS.id` |
| `row_number` | Número de fila de origen | Obligatorio |
| `row_data` | Valores de la fila como JSON | Obligatorio |

`row_number` identifica la posición de la fila de datos en el archivo original; no incluye la línea de encabezados. El modelo conserva el contenido original de cada celda en lo posible y no lo modifica durante la validación.

Se recomienda una restricción única sobre `(dataset_id, row_number)` para evitar filas de origen duplicadas dentro de una importación finalizada.

### QUALITY_RULES

Representa una regla de calidad configurable.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador | PK |
| `dataset_id` | Dataset asociado | FK a `DATASETS.id` |
| `rule_type` | Tipo de regla | Valor enumerado |
| `column_name` | Columna única de la regla, si aplica | Nullable según tipo |
| `parameters` | Parámetros específicos como JSON | Obligatorio |
| `is_active` | Si participa en nuevas ejecuciones | Obligatorio |
| `created_at` | Fecha de creación | Obligatorio |
| `updated_at` | Fecha de actualización | Obligatorio |

Tipos admitidos en el MVP: `REQUIRED`, `EMAIL_FORMAT`, `UNIQUE` y `NUMERIC_RANGE`.

Para `UNIQUE`, `column_name` será nulo y las columnas se especificarán en `parameters.columns`. Para las demás reglas, `column_name` identifica la columna objetivo.

La API valida los parámetros según el tipo de regla. No se almacenará código ejecutable como configuración.

### VALIDATION_RUNS

Representa una ejecución de validación.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador | PK |
| `dataset_id` | Dataset validado | FK a `DATASETS.id` |
| `status` | Estado de ejecución | Valor enumerado |
| `total_rows` | Filas evaluadas | Entero no negativo |
| `valid_rows` | Filas válidas | Entero no negativo |
| `invalid_rows` | Filas inválidas | Entero no negativo |
| `total_issues` | Incidencias encontradas | Entero no negativo |
| `compliance_rate` | Tasa de cumplimiento | Nullable si no hay filas |
| `started_at` | Inicio | Obligatorio |
| `completed_at` | Finalización | Nullable mientras no finalice |

En una ejecución completada, `valid_rows + invalid_rows = total_rows`. Las métricas deben corresponder a las incidencias y a la fotografía de reglas de esa ejecución.

### RUN_RULES

Conserva la fotografía de cada regla aplicada a una ejecución.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador de la fotografía | PK |
| `run_id` | Ejecución | FK a `VALIDATION_RUNS.id` |
| `original_rule_id` | Identificador de la regla de origen | Referencia lógica a `QUALITY_RULES.id` |
| `rule_snapshot` | Tipo, columna y parámetros utilizados | Obligatorio |

La fotografía no depende del contenido actual de `QUALITY_RULES`. La eliminación de una regla no debe destruir la información histórica necesaria para interpretar resultados previos.

La referencia a la regla original debe diseñarse de modo que su eliminación no provoque la pérdida de fotografías históricas. Una opción es permitir que `original_rule_id` quede nulo tras la eliminación, conservando `rule_snapshot`.

### VALIDATION_ISSUES

Representa una infracción individual encontrada durante una ejecución.

| Campo | Propósito | Restricción lógica |
|---|---|---|
| `id` | Identificador | PK |
| `run_id` | Ejecución asociada | FK a `VALIDATION_RUNS.id` |
| `dataset_row_id` | Fila afectada | Referencia a `DATASET_ROWS.id` |
| `run_rule_id` | Fotografía de la regla que falló | FK a `RUN_RULES.id` |
| `code` | Código estable de la incidencia | Obligatorio |
| `message` | Explicación legible | Obligatorio |
| `actual_value` | Valor observado, cuando sea apropiado | Nullable |

Los valores y mensajes devueltos por la API deben serializarse de forma segura. No se almacenarán trazas internas ni secretos en los mensajes.

## 3. Relaciones

```text
USERS 1 ───── N DATASETS
DATASETS 1 ── N DATASET_ROWS
DATASETS 1 ── N QUALITY_RULES
DATASETS 1 ── N VALIDATION_RUNS
VALIDATION_RUNS 1 ── N RUN_RULES
VALIDATION_RUNS 1 ── N VALIDATION_ISSUES
DATASET_ROWS 1 ── N VALIDATION_ISSUES
RUN_RULES 1 ── N VALIDATION_ISSUES
```

Las relaciones se aplicarán con claves foráneas y restricciones de integridad compatibles con la versión de Oracle seleccionada.

## 4. Persistencia JSON

El contenido de una fila se representa lógicamente como un objeto JSON cuyas claves son los nombres de las columnas del CSV. Por ejemplo:

```json
{
  "name": "Ana",
  "email": "ana@example.com",
  "age": "25"
}
```

La representación anterior es ilustrativa. La estrategia de importación debe documentar si los valores CSV se conservan como cadenas o si algún tipo se infiere; para el MVP se prioriza conservar los valores originales como texto y aplicar conversiones únicamente durante la validación.

La representación física se elegirá tras verificar la versión de Oracle Database Free y la compatibilidad con el driver y el ORM. Se preferirá el tipo JSON nativo si resulta compatible; en caso contrario se evaluará `CLOB` con una restricción JSON cuando esté disponible.

## 5. Índices iniciales a evaluar

- Índice sobre `DATASETS.user_id` para listar datasets del propietario.
- Índice sobre `DATASET_ROWS.dataset_id` y restricción única `(dataset_id, row_number)`.
- Índice sobre `QUALITY_RULES.dataset_id`.
- Índice sobre `VALIDATION_RUNS.dataset_id` y fecha de inicio para el historial.
- Índices sobre `VALIDATION_ISSUES.run_id`, `dataset_row_id` y `run_rule_id`.

Los índices definitivos se validarán con consultas reales y no se añadirán indiscriminadamente.

## 6. Transacciones e integridad

### Importación

La inserción de filas debe ser atómica. Si una importación falla, no deben quedar filas parciales asociadas a una importación que se reporte como exitosa.

### Ejecución de validación

La persistencia de una ejecución completada debe mantener coherentes el registro de ejecución, las fotografías de reglas, las incidencias y las métricas. Un fallo debe provocar rollback de los cambios de esa ejecución cuando corresponda.

### Historial

Las fotografías de reglas son inmutables. Editar o eliminar una regla activa no altera resultados históricos.

### Eliminación de datasets

La eliminación de un dataset debe definir explícitamente qué sucede con sus filas, reglas, ejecuciones, fotografías e incidencias. La política elegida debe evitar referencias huérfanas y ser coherente con los requisitos de borrado de datos.

## 7. Decisiones pendientes de implementación

- Versión exacta de Oracle Database Free.
- Tipo físico JSON y sus restricciones.
- Tipos de columna y estrategia para UUID y fechas.
- Política definitiva de cascadas y retención.
- Índices confirmados mediante consultas representativas.
- Límites transaccionales y estrategia de inserción masiva de filas.

Estas decisiones se cerrarán y documentarán con evidencia durante el preflight técnico.
