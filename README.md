# SEO Bot AI

Platform for automated SEO analysis and web page auditing with artificial intelligence integration.

## Overview

SEO Bot AI is a full-stack application built with Angular 21 and Python FastAPI that provides comprehensive SEO analysis, web page auditing, and performance monitoring capabilities.

### Technology Stack

**Frontend:**
- Angular 21.0.0
- TypeScript 5.7
- Bootstrap 5.3
- Chart.js 4.5
- ngx-translate (i18n support)
- Server-Side Rendering (SSR)

**Backend:**
- Python 3.13
- FastAPI
- PostgreSQL
- Selenium (web scraping)
- OpenAI GPT integration

## Architecture

The project follows Clean Architecture principles with three main layers:

- **Domain Layer**: Business logic and entity definitions
- **Application Layer**: Use cases and application-specific logic  
- **Infrastructure Layer**: External services, repositories, and framework implementations
- **Presentation Layer**: UI components and pages

## Getting Started

### Prerequisites

- Node.js 20+ and npm 11.6.2+
- Docker and Docker Compose
- PostgreSQL (if running locally without Docker)

### Development Environment

Start the development server:

```bash
npm install
npm start
```

The application will be available at `http://localhost:4200/`.

### Production Build

Build the application for production:

```bash
npm run build
```

Build artifacts will be stored in the `dist/` directory.

### Docker Deployment

Run the complete stack with Docker Compose:

```bash
docker-compose up -d
```

Services:
- Frontend: Port 3100
- API: Port 3101

## Project Structure

```
seo-bot-ai/
├── src/
│   ├── app/
│   │   ├── domain/          # Business entities and repository interfaces
│   │   ├── infrastructure/  # External services and implementations
│   │   ├── application/     # Use cases
│   │   └── presentation/    # UI components and pages
│   └── assets/
├── api/                     # Python FastAPI backend
├── commands/                # Development automation scripts
└── docker-compose.yml
```

## Development Tools

The project includes automated code generation tools. See [DEV-GUIDE.md](DEV-GUIDE.md) for detailed information on:

- Module generation
- Repository scaffolding
- Service creation
- Use case templates

Run the development menu:

```bash
./dev.sh
```

## Internationalization

The application supports multiple languages using ngx-translate. Language files are located in `src/assets/i18n/`.

Default language: Spanish (es)

## Testing

Execute unit tests:

```bash
npm test
```

## Configuration

### Environment Files

The application uses environment-specific configuration files located in `src/environments/`:

- `environment.example.ts` - Template file with default values (committed to repository)
- `environment.ts` - Development configuration (excluded from repository)
- `environment.prod.ts` - Production configuration (excluded from repository)

**Initial Setup:**

Before running the application, configure your environment files. You can use the automated setup script:

```bash
./setup-env.sh
```

Or manually copy the example file:

```bash
cp src/environments/environment.example.ts src/environments/environment.ts
cp src/environments/environment.example.ts src/environments/environment.prod.ts
```

Edit the files with your specific configuration values:
- API URLs
- Prometheus endpoints
- Timeout settings
- Authentication parameters

**Security Note:** The actual environment files (`environment.ts` and `environment.prod.ts`) are excluded from version control to protect sensitive configuration. Only the example template is committed to the repository.

## Additional Documentation

- [Development Guide](DEV-GUIDE.md) - Module generation and development workflows
- [Quick Start](QUICK-START.txt) - Quick reference guide

## License

Private - Internal use only
