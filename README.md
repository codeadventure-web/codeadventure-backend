# CodeAdventure Backend

CodeAdventure is a robust, scalable backend system for an interactive programming learning platform. It provides a comprehensive set of features for course management, student progress tracking, and an automated code execution (judge) system.

## 🚀 Key Features

- **User Authentication & Profiles**: Secure JWT-based authentication, Google Social Auth, and password recovery.
- **Course Management**: Structured curriculum with Courses, Lessons, and Tags.
- **Multi-modal Lessons**: Support for Markdown content, interactive Quizzes, and Programming Challenges.
- **Automated Judge System**: Asynchronous code execution for Python and C++ using Docker-based sandboxes for security.
- **Progress Tracking**: Real-time tracking of student completion and performance across courses.
- **API Documentation**: Interactive OpenAPI 3.0 documentation via Swagger UI.

## 🛠 Tech Stack

- **Framework**: [Django 5.0](https://www.djangoproject.com/) & [Django REST Framework](https://www.django-rest-framework.org/)
- **Database**: [PostgreSQL 16](https://www.postgresql.org/)
- **Task Queue**: [Celery](https://docs.celeryq.dev/) with [Redis](https://redis.io/)
- **API Docs**: [drf-spectacular](https://github.com/tfranzel/drf-spectacular) (OpenAPI 3.0)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Linting**: [Ruff](https://github.com/astral-sh/ruff)

## 📦 Project Structure

```text
├── accounts/      # User management, auth, and social login
├── common/        # Shared models, utils, and permissions
├── config/        # Project settings and configuration
├── courses/       # Course, lesson, and progress logic
├── judge/         # Code execution engine and submission handling
├── notifications/ # User notification system
├── quizzes/       # Quiz and grading logic
└── docker/        # Dockerfiles and environment configuration
```

## 🛠 Setup & Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/codeadventure-backend.git
   cd codeadventure-backend
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory (refer to `docker/compose.yml` for required variables).

3. **Build and start the services**:
   ```bash
   docker compose -f docker/compose.yml up --build
   ```

4. **Apply migrations**:
   ```bash
   docker compose -f docker/compose.yml exec web python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   docker compose -f docker/compose.yml exec web python manage.py createsuperuser
   ```

6. **Seed demo data (optional)**:
   ```bash
   docker compose -f docker/compose.yml exec web python manage.py seed_demo
   ```

The API will be available at `http://localhost:8000/`.

### Local Development Setup

If you prefer to run the project locally (outside Docker):

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

## 📖 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Redoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

## 🧪 Testing

The project uses `pytest` for testing.

### Running tests with Docker:
```bash
docker compose -f docker/compose.yml exec web pytest
```

### Running tests locally:
```bash
pytest
```

## 🧹 Code Quality

We use `Ruff` for linting and formatting.

```bash
ruff check .
ruff format .
```

## 📄 License

This project is licensed under the MIT License.