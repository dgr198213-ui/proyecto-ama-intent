# 📡 Documentación de la API de AMA-Intent

Esta guía detalla los endpoints disponibles en el Dashboard Personal de AMA-Intent v2.0.

## 1. Autenticación
El sistema utiliza JWT para la gestión de sesiones.

| Endpoint | Método | Descripción |
| :--- | :--- | :--- |
| `/login` | `POST` | Inicia sesión y devuelve un token de sesión. |
| `/logout` | `GET` | Cierra la sesión actual. |

## 2. Dashboard y Gestión de Proyectos
Endpoints para la gestión de la interfaz principal.

| Endpoint | Método | Descripción |
| :--- | :--- | :--- |
| `/api/overview` | `GET` | Obtiene estadísticas generales (proyectos, sesiones de debug). |
| `/api/projects` | `GET` | Lista todos los proyectos del usuario. |
| `/api/projects` | `POST` | Crea un nuevo proyecto. |
| `/api/projects/{id}` | `DELETE` | Elimina un proyecto específico. |

## 3. Asistente de Debug y Contenido
Interfaces para las herramientas de desarrollo.

| Endpoint | Método | Descripción |
| :--- | :--- | :--- |
| `/api/debug/session` | `POST` | Inicia una nueva sesión de depuración. |
| `/api/debug/analyze` | `POST` | Envía código para análisis de errores. |
| `/api/content/generate` | `POST` | Genera contenido (blogs, posts) basado en prompts. |

## 4. API de Plugins (Knowledge Graph)
Endpoints específicos del plugin de Grafo de Conocimiento.

| Endpoint | Método | Descripción |
| :--- | :--- | :--- |
| `/api/v1/kg/query` | `POST` | Ejecuta una consulta GraphRAG sobre el código. |
| `/api/v1/kg/rebuild` | `POST` | Reconstruye el grafo de conocimiento del proyecto. |
| `/api/v1/kg/overview` | `GET` | Obtiene métricas y estadísticas del grafo. |

---
*Nota: Todos los endpoints de la API requieren el encabezado `Authorization: Bearer <token>` o una cookie de sesión válida.*
