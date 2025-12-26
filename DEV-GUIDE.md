# Development Guide - Module Generation System

Automated system for standardized module creation following Clean Architecture principles in Angular.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Available Commands](#available-commands)
- [Workflows](#workflows)
- [Conventions](#conventions)
- [Examples](#examples)
- [Maintenance](#maintenance)

## Quick Start

```bash
# Run main menu
./dev.sh

# View complete help
./commands/help.sh
```

## Architecture

The project follows a 3-layer architecture pattern:

### Domain Layer (Business Rules)
```
domain/
├── models/           # Domain entities
├── repositories/     # Repository interfaces (contracts)
└── mappers/         # DTO to Model transformers
```

### Infrastructure Layer (Technical Implementation)
```
infrastructure/
├── dto/             # Data Transfer Objects
├── repositories/    # Repository implementations
└── services/        # HTTP services
```

### Application Layer (Use Cases)
```
application/
└── use-cases/       # Application logic
```

## Available Commands

### Main Menu - `./dev.sh`

Interactive menu with all options:

1. **Create Model** - Models + DTOs + Mappers
2. **Create Service** - Service with auto-detection of Mappers
3. **Create Repository** - Repository Domain + Implementation
4. **Create Complete Module** - Full automated workflow
5. **Create Use Case** - Use cases with auto-detection of Repositories
6. **View Structure** - Display architecture
7. **Validate Structure** - Validate and show statistics
8. **Inspect Module** - Analyze specific module
9. **Clean Module** - Remove complete module
0. **Exit**

### Individual Commands

#### `./commands/model.sh`
Creates models with configurable options:
- Request/Response or simple Model
- Optional DTOs
- Optional Mappers

#### `./commands/service.sh`
Creates services with:
- Auto-detection of Mappers
- Integration with HttpService

#### `./commands/repository.sh`
Creates repositories with:
- Interface in Domain Layer
- Implementation in Infrastructure Layer
- Auto-detection of Models and Services
- Auto-update of `app.config.ts`

#### `./commands/usecase.sh`
Creates use cases with:
- Auto-detection of Repositories
- Automatic dependency injection

#### `./commands/validate.sh`
Validates project structure:
- Counts files by type
- Lists available modules
- Shows components of each module

#### `./commands/inspect.sh`
Inspects a specific module:
- Lists all files
- Shows exports and classes
- Verifies configuration in app.config.ts

#### `./commands/help.sh`
Displays complete system documentation

## Workflows

### Create Complete Module (Recommended)

The automated workflow creates everything in the correct order:

```bash
./dev.sh
# Option 4: Create Complete Module
```

**Step 1:** Model Creation
- Directory: `auth`
- File: `auth`
- Request: `Yes`
- Response: `Yes`
- DTO: `Yes`
- Mapper: `Yes`

**Step 2:** Service Creation
- Uses same directory/file
- Auto-detects and uses created Mapper

**Step 3:** Repository Creation
- Uses same directory/file
- Auto-detects Models and Service
- Generates methods automatically
- Updates `app.config.ts`

### Create Individual Components

For more control, create in this order:

```bash
# 1. Models (module foundation)
./commands/model.sh

# 2. Service (HTTP logic)
./commands/service.sh

# 3. Repository (domain interface)
./commands/repository.sh

# 4. Use Cases (optional - specific use cases)
./commands/usecase.sh
```

## Conventions

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Directory | kebab-case | `auth`, `user-profile` |
| File | kebab-case | `auth`, `user-profile` |
| Model Class | PascalCase + Model | `AuthModel` |
| DTO Class | PascalCase + Dto | `AuthDto` |
| Service Class | PascalCase + Service | `AuthService` |
| Repository Class | PascalCase + Repository | `AuthRepository` |
| Use Case Class | PascalCase + UseCase | `LoginUseCase` |

### File Structure

#### Request/Response Pattern
```
domain/models/auth/
├── request/
│   └── auth-request.model.ts
└── response/
    └── auth-response.model.ts

infrastructure/dto/
├── request/
│   └── auth-request.dto.ts
└── response/
    └── auth-response.dto.ts

domain/mappers/auth/
└── auth.mapper.ts
```

#### Simple Pattern
```
domain/models/auth/
└── auth.model.ts

infrastructure/dto/
└── auth.dto.ts

domain/mappers/auth/
└── auth.mapper.ts
```

## Features

### Auto-detection
- Detects existing Mappers when creating Services
- Detects Models and Services when creating Repositories
- Detects Repositories when creating Use Cases
- Automatically generates methods based on Services

### Auto-configuration
- Automatically updates `app.config.ts`
- Adds necessary imports
- Registers providers in DI

### Validation
- Validates project structure
- Counts files by type
- Verifies module integrity

### Inspection
- Analyzes specific modules
- Shows exports and classes
- Detects orphaned files

## Examples

### Example 1: Authentication Module

```bash
./dev.sh
# Option 4 (Complete Module)
# Directory: auth
# File: auth
# Request: y
# Response: y
# DTO: y
# Mapper: y
```

**Created files:**
```
domain/models/auth/request/auth-request.model.ts
domain/models/auth/response/auth-response.model.ts
infrastructure/dto/request/auth-request.dto.ts
infrastructure/dto/response/auth-response.dto.ts
domain/mappers/auth/auth.mapper.ts
infrastructure/services/auth/auth.service.ts
domain/repositories/auth/auth.repository.ts
infrastructure/repositories/auth/auth.implementation.repository.ts
app.config.ts (updated)
```

### Example 2: Login Use Case

```bash
./dev.sh
# Option 5 (Create Use Case)
# Directory: auth
# Use case: login
```

**Result:**
```typescript
// application/use-cases/auth/login.use-case.ts
@Injectable({ providedIn: 'root' })
export class LoginUseCase {
  constructor(private authRepository: AuthRepository) {}

  async execute(params?: any): Promise<any> {
    // TODO: Implement logic
  }
}
```

## Maintenance

### Validate Project
```bash
./commands/validate.sh
```

### Inspect Module
```bash
./commands/inspect.sh
# Module: auth
```

### Clean Module
```bash
./dev.sh
# Option 9 (Clean Module)
# Module: auth
```

## Environment Configuration

### Initial Setup

Before starting development, configure the environment files. You can use the automated setup script:

```bash
./setup-env.sh
```

Or manually copy the template:

```bash
cp src/environments/environment.example.ts src/environments/environment.ts
cp src/environments/environment.example.ts src/environments/environment.prod.ts
```

### Configuration Files

- `environment.example.ts` - Template with default values (version controlled)
- `environment.ts` - Development settings (excluded from repository)
- `environment.prod.ts` - Production settings (excluded from repository)

### Security

The actual environment files are excluded from version control via `.gitignore` to protect sensitive information such as:
- API endpoints
- Authentication tokens
- Service URLs
- Database credentials

Only the example template is committed to the repository.

## Resources

- View structure: Option 6 in main menu
- Complete help: `./commands/help.sh` or option `?` in menu
- Validate structure: `./commands/validate.sh`
- Inspect module: `./commands/inspect.sh`

## Contributing

To add new generators:
1. Create script in `commands/`
2. Make executable: `chmod +x commands/new.sh`
3. Add to menu in `dev.sh`

## License

Internal use - SEO Bot AI Project

