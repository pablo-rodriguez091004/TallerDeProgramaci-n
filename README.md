# Sistema de Reservas y Control de Aforo

Proyecto de la materia [nombre de la materia]. Sistema genérico de reservas para pequeñas y medianas empresas colombianas (canchas, salones de eventos, coworking, consultorios, etc.).

## Stack tecnológico

- **Frontend:** HTML / CSS / JavaScript (vanilla, sin frameworks)
- **Backend:** Python + Flask
- **Base de datos:** PostgreSQL
- **Microservicio auxiliar:** Python (reportes y tareas programadas)

## Estructura del proyecto

```
PROYECTO_FINAL/
├── backend/            # API en Flask
├── frontend/           # Interfaz vanilla
├── database/           # Scripts SQL
├── python-services/    # Reportes y jobs programados
├── docs/               # Documentación y diagramas
└── README.md
```

## Requisitos previos

- Python 3.10 o superior
- PostgreSQL instalado localmente
- Git
- VSCode (recomendado, con extensión Live Server para el frontend)

## Instalación del backend

### 1. Ubicarse en la carpeta backend

```bash
cd backend
```

### 2. Crear entorno virtual

**Fedora / Linux / Mac:**
```bash
python3 -m venv venv
```

**Windows (CMD o PowerShell):**
```bash
python -m venv venv
```

### 3. Activar el entorno virtual

**Fedora / Linux / Mac:**
```bash
source venv/bin/activate
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

> Si en PowerShell aparece un error de "ejecución de scripts deshabilitada", correr una vez:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar el archivo de ejemplo y completar con los datos locales de cada uno:

**Fedora / Linux / Mac:**
```bash
cp .env.example .env
```

**Windows:**
```bash
copy .env.example .env
```

Editar `.env` con las credenciales de tu PostgreSQL local.

### 6. Levantar el servidor

```bash
python app.py
```

El servidor debería quedar corriendo en `http://localhost:5000`

## Frontend

No requiere instalación. Abrir `frontend/index.html` con la extensión **Live Server** de VSCode (clic derecho → "Open with Live Server") para tener recarga automática.

## Base de datos

Los scripts de creación de tablas están en `database/schema.sql`. Ejecutarlos contra tu instancia local de PostgreSQL antes de levantar el backend.

## Convenciones del equipo

- Nombres de archivos siempre en **minúsculas** y con **guion bajo** (`auth_routes.py`, no `Auth_Routes.py`) — importante porque Linux distingue mayúsculas/minúsculas y Windows no.
- Ramas de trabajo: `feature/nombre-del-modulo` (ej. `feature/backend-auth`, `feature/frontend-calendario`)
- Los Pull Requests van hacia `develop`, no directo a `main`.

## Notas para equipo con sistemas operativos mixtos (Fedora / Windows)

- El archivo `.gitattributes` en la raíz normaliza los saltos de línea (LF) para evitar conflictos falsos en Git entre Windows y Linux/Mac.
- Nunca subir la carpeta `venv/` ni el archivo `.env` al repositorio (ya están en `.gitignore`).

