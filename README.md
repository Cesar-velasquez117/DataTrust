# DataTrust

**DataTrust** es una plataforma de calidad de datos que permite importar conjuntos de datos CSV, definir reglas de validación, detectar problemas y consultar resultados históricos.

El proyecto se construye como un portafolio de ingeniería de software con énfasis en código mantenible, pruebas automatizadas, seguridad, documentación y decisiones técnicas justificadas.

> **Estado del proyecto:** planificación funcional y de arquitectura completada. La implementación aún no ha comenzado.

## Problema

Los datos incompletos, duplicados o con formatos incorrectos pueden afectar reportes, análisis y decisiones de negocio. DataTrust busca facilitar la detección de esos problemas mediante reglas explícitas y resultados reproducibles.

## Alcance del MVP

- Registro e inicio de sesión con JWT.
- Creación y administración de datasets por usuario.
- Importación de archivos CSV con límites explícitos.
- Configuración de reglas de calidad.
- Ejecución síncrona de validaciones.
- Panel con métricas de calidad.
- Consulta de incidencias y ejecuciones anteriores.
- Exportación de incidencias a CSV.
- Entorno de desarrollo local reproducible y comprobaciones automáticas en CI.

## Tecnologías previstas

- **Backend:** Python, FastAPI, Pydantic.
- **Base de datos:** Oracle Database Free.
- **Persistencia y migraciones:** SQLAlchemy y Alembic, sujetos a verificación de compatibilidad.
- **Frontend:** React, TypeScript, Vite y Tailwind CSS.
- **Pruebas:** pytest en backend; Vitest y React Testing Library en frontend.
- **Entorno y automatización:** Docker Compose y GitHub Actions.

Las versiones exactas y la compatibilidad del stack con Oracle se verificarán antes de depender de ellas en la implementación.

## Documentación

- [Requisitos y alcance del MVP](docs/requirements.md)
- [Arquitectura propuesta](docs/architecture.md)
- [Modelo de datos lógico](docs/data-model.md)

## Desarrollo

La implementación se realizará de manera incremental, con pruebas para cada funcionalidad. Los comentarios del código explicarán decisiones y conceptos no obvios, sin repetir literalmente lo que ya expresa el código.

La guía de instalación se completará cuando se haya configurado y probado el entorno de desarrollo.

## Licencia

La licencia del proyecto está pendiente de definir.
