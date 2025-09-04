# Video Processing API

A RESTful API service for handling video processing and cleanup tasks asynchronously. Built with FastAPI, Celery, and FFmpeg for efficient video manipulation and transcoding operations.

## Project Overview

This service provides asynchronous video processing capabilities using a modern Python stack. It leverages FastAPI to serve HTTP requests, Celery as a distributed task queue for background processing, Redis as the message broker, and FFmpeg for video manipulation operations. The entire application is containerized using Docker and orchestrated with Docker Compose for easy deployment and scalability.

## Architecture

- **FastAPI**: High-performance web framework for building APIs
- **Celery**: Distributed task queue for asynchronous video processing
- **Redis**: Message broker and result backend for Celery
- **FFmpeg**: Multimedia framework for video processing operations
- **Docker**: Containerization for consistent deployment environments

## Project Structure

| File | Description |
|------|-------------|
| `.dockerignore` | Defines files/directories to exclude when building the Docker image |
| `.env.example` | Template for environment variables (broker URLs, ports, credentials) |
| `.gitignore` | Specifies files to be ignored by Git version control |
| `Dockerfile` | Builds the Docker image for the main service with FFmpeg support |
| `docker-compose.yml` | Orchestrates API service, Celery worker, and Redis broker |
| `app.py` | Main FastAPI application entry point with API endpoints |
| `settings.py` | Configuration module for environment variables and constants |
| `celery_app.py` | Initializes and configures the Celery instance |
| `tasks.py` | Defines Celery background processing tasks for video operations |
| `cleanup.py` | Handles cleanup operations for temporary files and expired jobs |
| `requirements.txt` | Python dependencies including FastAPI, Celery, and video processing libraries |
| `logo.png` | Project logo asset for branding |

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Git

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <https://github.com/ali-mansour21/Video-Processing-Assessment.git>
   cd Video-Processing-Assessment
   ```

2. **Create environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your specific configurations if needed
   ```

3. **Build and start the services**
   ```bash
   docker-compose up --build
   ```

4. **Verify the services are running**
   - API server: http://localhost:5000
   - API documentation: http://localhost:5000/docs

The application will start three services:
- `api`: FastAPI web server running on port 5000
- `worker`: Celery worker for processing background tasks
- `redis`: Redis server for message brokering and result storage

## API Usage

### Example Request - Video Merge

Test the video merge functionality with multiple video files:

```bash
curl -X 'POST' \
  'http://localhost:5000/api/videos/merge' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'videos=@testing_video_2.mp4;type=video/mp4' \
  -F 'videos=@testing_video.mp4;type=video/mp4'
```

### Interactive API Documentation

Access the automatically generated API documentation at:
- Swagger UI: http://localhost:5000/docs

## Development

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BASE_URL` | Base URL for the API service | `http://localhost:5000` |
| `VIDEOS_DIR` | Directory for storing video files | `/app/videos` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |

### File Storage

Videos are stored in the `./videos` directory, which is mounted as a volume in both the API and worker containers to ensure file accessibility across services.

### Cleanup Operations

To delete videos older than 24 hours, run the cleanup script manually:

```bash
docker-compose exec api python cleanup.py
```

> **Note**: Automatic cleanup scheduling will be implemented in future versions. For now, run this command periodically to manage storage.
