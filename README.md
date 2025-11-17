# QuizGeniusAI-Backend

## Testing Endpoints

## **Endpoints de Usuarios (`users.py`)**

Estos endpoints se encuentran bajo el prefijo `/api/v1/users`.

**1. Registrar un nuevo usuario**

- **Endpoint:** `POST /register`
- **Descripción:** Crea un nuevo usuario en la base de datos.

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
-H "Content-Type: application/json" \
-d '{
  "email": "test@example.com",
  "password": "a_strong_password"
}'
```

**2. Obtener el progreso de un usuario**

- **Endpoint:** `GET /users/{user_id}/progress`
- **Descripción:** Recupera el progreso de estudio de un usuario específico. Reemplaza `{user_id}` con el ID del usuario.

```bash
curl -X GET "http://localhost:8000/api/v1/users/me/progress" \
-H "Authorization: Bearer tu_token_de_acceso_aqui"
```

**3. Iniciar Sesión**

- **Endpoint:**   `POST /users/token`
- **Descripción:** Inicias sesión, este nos retornará un `ACCESS_TOKEN`.

```bash
curl -X POST "http://localhost:8000/api/v1/users/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=test@example.com&password=a_strong_password"
```

Output example:
```bash
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqYXJleDY2NkBnbWFpbC5jb20iLCJleHAiOjE3NDk0ODYwNzN9.PRChaiNDhFEiunT1hl0X9I7zzN-g15u-mFnVWoWVhkA","token_type":"bearer"}
```

---

### **Endpoints de Workspaces (`workspaces.py`)**

Estos endpoints se encuentran bajo los prefijos `/api/v1/workspaces`, `/api/v1/subtopics`, y `/api/v1/quizzes`.

**1. Crear un nuevo Workspace**

- **Endpoint:** `POST /workspaces/`
- **Descripción:** Crea un nuevo espacio de trabajo para el usuario actual.

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/" \
-H "Authorization: Bearer ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{"title": "Mi Workspace Seguro", "description": "Descripción"}'
```

![[Pasted image 20250608112526.png]]

**2. Obtener todos los Workspaces de un usuario**

- **Endpoint:** `GET /workspaces/`
- **Descripción:** Lista todos los espacios de trabajo pertenecientes al usuario actual.

```bash
curl -X GET "http://localhost:8000/api/v1/workspaces/" \
-H "Authorization: Bearer ACCESS_TOKEN" 
```

**3. Obtener un Workspace en específico**

- **Endpoint:**  `GET /workspaces/{workspace_id}`
- **Descripción:** Obtener workspace en específico.

```bash
curl -X GET "http://localhost:8000/api/v1/workspaces/{workspace_id}" \
-H "Authorization: Bearer ACCESS_TOKEN" 
```

**4. Subir un documento para análisis**

- **Endpoint:** `POST /workspaces/{workspace_id}/upload-document/`
- **Descripción:** Carga un archivo PDF a un workspace específico para ser procesado y analizado.

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/1/upload-document/" \
-F "file=@/ruta/a/tu/documento.pdf;type=application/pdf"
```

**5. Obtener los subtemas de un Workspace**

- **Endpoint:** `GET /workspaces/{workspace_id}/subtopics`
- **Descripción:** Lista todos los subtemas (vistos como conjuntos de tarjetas) dentro de un workspace.

```bash
# Reemplaza '1' con el ID del workspace
curl -X GET "http://localhost:8000/api/v1/workspaces/1/subtopics"
```

**6. Obtener las Flashcards de un Subtema**

- **Endpoint:** `GET /subtopics/{subtopic_id}/flashcards`
- **Descripción:** Recupera todas las flashcards asociadas a un subtema específico.

```bash
# Reemplaza '1' con el ID del subtema
curl -X GET "http://localhost:8000/api/v1/subtopics/1/flashcards"
```

**7. Obtener los Quizzes de un Subtema**

- **Endpoint:** `GET /subtopics/{subtopic_id}/quizzes`
- **Descripción:** Lista todos los quizzes disponibles para un subtema.

```bash
# Reemplaza '1' con el ID del subtema
curl -X GET "http://localhost:8000/api/v1/subtopics/1/quizzes"
```

**8. Obtener los detalles y preguntas de un Quiz**

- **Endpoint:** `GET /quizzes/{quiz_id}`
- **Descripción:** Obtiene toda la información de un quiz, incluyendo su lista de preguntas, opciones y respuestas.

```bash
# Reemplaza '1' con el ID del quiz
curl -X GET "http://localhost:8000/api/v1/quizzes/1"
```


## Testing Database

### Nuestro `docker-compose` file:

```yaml
version: '3.8'

services:
	db:
		image: postgres:13-alpine
		container_name: quizgenius_db
		volumes:
			- postgres_data:/var/lib/postgresql/data/
		environment:
			- POSTGRES_USER=quizuser
			- POSTGRES_PASSWORD=quizpassword
			- POSTGRES_DB=quizgenius_db
		ports:
		- "5432:5432"
		restart: unless-stopped
	app:
		build: .
		container_name: quizgenius_app
		ports:
			- "8000:8000"
		volumes:
			- .:/app
		environment:
			- DATABASE_URL=postgresql://quizuser:quizpassword@db:5432/quizgenius_db
			- GEMINI_API_KEY=${GEMINI_API_KEY}
		depends_on:
			- db
		command: >
			sh -c "
			echo 'Waiting for PostgreSQL to be ready...' &&
			while ! nc -z db 5432; do
				sleep 0.1;
			done;
			echo 'PostgreSQL started!' &&
			uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
			"
volumes:
	postgres_data:
```

Dado tu `docker-compose.yaml`, el nombre de tu servicio PostgreSQL es `db`. Aquí te explico cómo hacerlo:

**1. Abrir una terminal interactiva dentro del contenedor de PostgreSQL:**

Para ejecutar un comando dentro de un contenedor en ejecución, usas `docker exec`. Para que sea interactivo, necesitas las banderas `-it`.

```bash 
docker exec -it quizgenius_db psql -U quizuser -d quizgenius_db
```

**Explicación del comando:**

- `docker exec`: Este comando se usa para ejecutar un comando dentro de un contenedor en ejecución.
- `-it`:
    - `-i` (interactive): Mantiene la entrada estándar abierta incluso si no está conectada.
    - `-t` (tty): Asigna un pseudo-TTY, lo que hace que la terminal sea interactiva.
- `quizgenius_db`: Este es el nombre de tu contenedor de PostgreSQL, tal como lo definiste en `container_name` en tu `docker-compose.yaml`.
- `psql`: Este es el cliente de línea de comandos de PostgreSQL.
- `-U quizuser`: Especifica el usuario de la base de datos con el que te conectarás. Según tu `docker-compose.yaml`, es `quizuser`.
- `-d quizgenius_db`: Especifica la base de datos a la que te conectarás. Según tu `docker-compose.yaml`, es `quizgenius_db`.

**2. Una vez dentro de `psql`:**

Después de ejecutar el comando anterior, se te pedirá la contraseña del usuario `quizuser`. Ingresa `quizpassword` (la que tienes en tu `docker-compose.yaml`).

Una vez que te hayas autenticado con éxito, verás el prompt de `psql`, que generalmente se parece a:

```
quizgenius_db=#
```

**3. Comandos para ver las tablas y más:**

Dentro del prompt de `psql`, puedes usar los siguientes meta-comandos (precedidos por una barra invertida `\`) para explorar la base de datos:

- **Listar todas las tablas en la base de datos actual:**
        
```sql
    \dt
```
    
- **Listar todas las bases de datos en el servidor:**
    
```sql
\l
```
    
- **Describir la estructura de una tabla específica (columnas, tipos de datos, restricciones):**
    
```sql
\d nombre_de_la_tabla
```
    
- **Listar las relaciones (tablas, vistas, secuencias, etc.):**
        
```sql 
\d
```
    
- **Ver la configuración de `psql`:**
    
```sql
\set
```
    
- Ejecutar consultas SQL normales:
    Puedes escribir cualquier consulta SQL que desees, por ejemplo:
    
```sql
SELECT * FROM users;
```
    
    Recuerda terminar cada consulta SQL con un punto y coma (`;`).
    
- **Salir de `psql`:**

```sql
\q
```
    
    O simplemente presiona `Ctrl+D`.
    
