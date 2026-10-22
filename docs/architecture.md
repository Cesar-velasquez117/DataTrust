# Arquitectura propuesta

## 1. Objetivos de diseño

DataTrust se implementará como un **monolito modular**: una aplicación backend desplegable como una unidad, organizada en módulos con responsabilidades claras.

La arquitectura busca:

- facilitar la comprensión por parte de desarrolladores;
- permitir probar el motor de calidad sin servidor ni base de datos;
- mantener autorización y reglas de negocio fuera de los componentes de interfaz;
- conservar resultados históricos reproducibles;
- evitar complejidad operativa que el MVP todavía no necesita.

## 2. Vista general

```text
┌──────────────────────────────────────────┐
│ Frontend: React + TypeScript + Tailwind  │
│ Vistas, formularios, estado y API client  │
└────────────────────┬─────────────────────┘
                     │ HTTPS / JSON / CSV
┌────────────────────▼─────────────────────┐
│ Backend: FastAPI                         │
│                                          │
│ API routes → schemas → application       │
│                 services                 │
│                     │                    │
│       ┌─────────────┼──────────────┐     │
│       ▼             ▼              ▼     │
│  Repositories  Security       Quality    │
│                              Engine      │
└────────────────────┬─────────────────────┘
                     │ SQL / transactions
┌────────────────────▼─────────────────────┐
│ Oracle Database Free                     │
│ Usuarios, datasets, filas, reglas, runs  │
│ e incidencias                            │
└──────────────────────────────────────────┘
```

El diagrama es conceptual. Los módulos podrán ajustarse a medida que se implementen, siempre que se mantengan las responsabilidades y las reglas de dependencia.

## 3. Componentes y responsabilidades

### Frontend

React, TypeScript, Vite y Tailwind CSS.

Responsabilidades:

- presentar datasets, reglas, métricas e incidencias;
- validar formularios para mejorar la experiencia, sin reemplazar la validación del servidor;
- enviar archivos CSV y mostrar el resultado de la importación;
- gestionar estados de carga, éxito y error;
- conservar el access token en memoria cuando sea viable, evitando `localStorage` como almacenamiento predeterminado de tokens.

El frontend no decide si un usuario tiene permiso para acceder a un recurso. Esa decisión siempre corresponde al backend.

### API y schemas

FastAPI expone los endpoints versionados bajo `/api/v1`. Pydantic define y valida los contratos de entrada y salida.

Las rutas traducen solicitudes HTTP a llamadas de servicios y transforman sus resultados en respuestas HTTP. No deberían contener el algoritmo principal de calidad ni consultas complejas directamente.

### Seguridad

Gestiona contraseñas, emisión y validación de access tokens JWT y obtención del usuario autenticado.

Cada servicio o consulta que acceda a recursos privados debe aplicar comprobaciones de propiedad. Conocer un UUID no constituye autorización.

### Servicios de aplicación

Orquestan operaciones como crear datasets, importar CSV, administrar reglas, ejecutar validaciones y exportar resultados.

Los servicios coordinan repositorios y motor de calidad y definen límites transaccionales. Las decisiones de negocio no deben depender de detalles visuales del frontend.

### Repositorios y persistencia

Los repositorios encapsulan las operaciones de lectura y escritura de Oracle. SQLAlchemy y Alembic son las herramientas previstas, sujetas a un preflight de compatibilidad.

Las migraciones versionan el esquema de la base de datos. Las transacciones deben garantizar que las importaciones y ejecuciones no queden en estados parcialmente persistidos.

### Motor de calidad

Módulo Python independiente de FastAPI, SQLAlchemy y Oracle.

Recibe filas y definiciones de reglas ya validadas, evalúa las reglas activas y produce incidencias estructuradas. Debe ser determinista: las mismas filas y los mismos parámetros deben generar los mismos resultados.

No ejecuta código arbitrario proporcionado por usuarios y no modifica los datos originales.

### Base de datos

Oracle Database Free almacenará usuarios, datasets, filas JSON, reglas, ejecuciones, fotografías de reglas e incidencias.

La representación física de JSON, índices, restricciones y cascadas se decidirá tras comprobar la versión de Oracle y su compatibilidad con el stack Python.

## 4. Flujo principal: validar un dataset

1. El usuario solicita ejecutar una validación.
2. La API autentica la solicitud y comprueba la propiedad del dataset.
3. El servicio carga las filas y reglas activas.
4. Se validan los parámetros y se crea una fotografía de las reglas.
5. El motor evalúa las reglas y produce incidencias y métricas.
6. El servicio persiste la ejecución, la fotografía de reglas y las incidencias dentro de una estrategia transaccional.
7. La API devuelve el resumen de la ejecución completada.

La respuesta de éxito solo se envía cuando el resultado está persistido. Si ocurre un error de persistencia, no se debe presentar el resultado como una ejecución completada correctamente.

## 5. Flujo de importación CSV

1. Autenticar al usuario y verificar la propiedad del dataset.
2. Comprobar tamaño y tipo de contenido.
3. Leer el archivo de manera acotada y verificar codificación, encabezados, número de columnas y número de filas.
4. Rechazar encabezados vacíos o duplicados según la normalización acordada.
5. Preparar los registros conservando nombres de columna, valores y números de fila de origen.
6. Persistir la importación en una transacción.
7. Confirmar la operación únicamente si se importaron todos los registros válidos.

No se conservarán archivos cargados de manera permanente en el MVP, salvo que una necesidad técnica documentada lo requiera.

## 6. Seguridad y límites

- Access tokens JWT de corta duración; inicialmente no se implementará refresh token.
- Contraseñas con un algoritmo de hash adecuado, preferiblemente Argon2id.
- Secretos mediante variables de entorno y archivo de ejemplo sin credenciales reales.
- Consultas acotadas y paginación de listados.
- Límite de tamaño y cantidad de filas en importaciones.
- Máximo inicial de 20 reglas activas por dataset.
- Exportación CSV protegida contra fórmulas ejecutables en hojas de cálculo.
- Errores públicos sin trazas, contraseñas, tokens ni credenciales.
- Autorización comprobada en backend para cada recurso privado.

## 7. Pruebas y calidad

### Backend

- Unitarias: reglas, normalización, métricas y casos límite.
- Integración: persistencia Oracle, migraciones, transacciones y repositorios.
- Seguridad: autenticación, permisos y acceso cruzado entre usuarios.
- Extremo a extremo: importar CSV, crear reglas, ejecutar, consultar y exportar.

### Frontend

- Pruebas de componentes y formularios con Vitest y React Testing Library.
- Estados de carga, error, listas vacías y resultados.
- Validación del flujo principal con pruebas de extremo a extremo cuando la infraestructura esté disponible.

### Automatización

GitHub Actions ejecutará las comprobaciones pertinentes de formato, linting, tipos y pruebas. Las pruebas que requieran Oracle necesitarán un servicio de base de datos configurado o una estrategia de integración documentada.

El objetivo inicial de cobertura de líneas para el motor de calidad es del 80 %, acompañado de pruebas explícitas para cada regla y sus casos límite. La cobertura no sustituye la revisión de los casos que deben probarse.

## 8. Decisiones de alcance

No se incorporarán microservicios, Redis, Kafka, Kubernetes ni workers distribuidos al MVP. Se reconsiderarán únicamente si mediciones o requisitos concretos demuestran que son necesarios.

La ejecución síncrona y los límites de entrada se probarán con datos de referencia. Si el objetivo de rendimiento no se cumple, primero se revisarán el algoritmo, las consultas y los límites antes de ampliar la arquitectura.

## 9. Preflight técnico pendiente

Antes de depender del stack de persistencia:

1. fijar una versión de Oracle Database Free;
2. levantarla en el entorno local/Docker elegido;
3. conectar desde Python con el driver seleccionado;
4. comprobar integración con SQLAlchemy y Alembic;
5. aplicar y revertir una migración;
6. guardar y consultar datos JSON;
7. probar commit, rollback y restricciones;
8. documentar resultados y versiones.

Los resultados de este preflight se registrarán como una decisión técnica independiente.
