# Project Refactor Documentation

## Overview

This document summarizes the major refactoring completed on the Spotify Playlist Optimizer project to improve code organization and separation of concerns.

## Objectives

1. **Database Organization**: Move all database-related scripts and `.db` files into a dedicated `db/` directory
2. **Test Organization**: Move all test scripts into a dedicated `tests/` directory
3. **Import Consistency**: Update all imports and references to match the new structure
4. **Functionality Preservation**: Ensure all tests and application functionality work after the refactor

## Changes Made

### Directory Structure

**Before:**

```
spotify-optimizer/
├── check_db.py
├── monitor_oauth.py
├── debug_oauth_flow.py
├── test_auth_flow.py
├── direct_oauth_test.py
├── spotify.db
├── spotify_optimizer.db
├── test_spotify_optimizer.db
└── backend/
    ├── tests/
    └── [other files]
```

**After:**

```
spotify-optimizer/
├── db/
│   ├── check_db.py
│   ├── monitor_oauth.py
│   ├── debug_oauth_flow.py
│   ├── spotify.db
│   ├── spotify_optimizer.db
│   └── test_spotify_optimizer.db
├── tests/
│   ├── test_auth_flow.py
│   └── direct_oauth_test.py
└── backend/
    ├── tests/
    └── [other files]
```

### File Migrations

**Database Files Moved to `db/`:**

- `check_db.py` → `db/check_db.py`
- `monitor_oauth.py` → `db/monitor_oauth.py`
- `debug_oauth_flow.py` → `db/debug_oauth_flow.py`
- `spotify.db` → `db/spotify.db`
- `spotify_optimizer.db` → `db/spotify_optimizer.db`
- `test_spotify_optimizer.db` → `db/test_spotify_optimizer.db`

**Test Files Moved to `tests/`:**

- `test_auth_flow.py` → `tests/test_auth_flow.py`
- `direct_oauth_test.py` → `tests/direct_oauth_test.py`

### Code Updates

#### Database Path Configuration

**Updated Files:**

- `backend/dependencies.py`: Updated to use `db/spotify.db` path
- `backend/create_db.py`: Updated to create database in `db/` directory
- `backend/tests/conftest.py`: Updated test database path to `db/test_spotify_optimizer.db`

#### Import Path Fixes

**Key Changes:**

- Added `sys.path` manipulation in `create_db.py` to ensure absolute imports work
- Changed all model imports to use absolute imports: `from backend.models import ...`
- Ensured consistent SQLAlchemy Base usage across all modules

#### Path References

**Updated References:**

- Database connection strings updated to use `db/` directory
- Test scripts updated to reference correct database locations
- Monitor scripts updated to use relative paths from their new location

## Technical Fixes

### SQLAlchemy Model Import Issue

**Problem:** `sqlite3.OperationalError: no such table: users` errors due to inconsistent model imports and Base definitions.

**Solution:**

1. Standardized all imports to use absolute paths: `from backend.models import Base, User, ...`
2. Added `sys.path.append(str(Path(__file__).resolve().parent.parent))` to scripts
3. Ensured single source of truth for SQLAlchemy Base metadata

### Database Path Consistency

**Problem:** Different modules using different database file paths.

**Solution:**

1. Created centralized path configuration using `pathlib.Path`
2. Used robust absolute path construction: `PROJECT_ROOT / "db" / "spotify.db"`
3. Updated all database connection references to use the unified path

## Verification Steps

1. ✅ Database initialization works correctly (`python backend/create_db.py`)
2. ✅ Backend tests pass (`pytest backend/tests/`)
3. ✅ Application tests pass (`pytest tests/`)
4. ✅ All database files consolidated in `db/` directory
5. ✅ All test files consolidated in `tests/` directory
6. ✅ No broken import references
7. ✅ Cleaned up debug prints and temporary code

## Benefits Achieved

1. **Better Organization**: Clear separation between database logic, tests, and application code
2. **Maintainability**: Easier to find and manage database-related scripts
3. **Consistency**: Unified database path handling across all modules
4. **Reliability**: Fixed import path issues that could cause runtime errors
5. **Cleaner Root**: Reduced clutter in project root directory

## Future Considerations

- Consider moving additional utility scripts to appropriate subdirectories
- Document the new project structure in README.md
- Consider adding a migration guide for developers working with existing clones
- Evaluate if additional separation (e.g., `scripts/`, `utils/`) would be beneficial

## Commit Message Template

```
refactor: reorganize project structure for better separation of concerns

- Move database scripts and .db files to db/ directory
- Move test scripts to tests/ directory
- Fix SQLAlchemy model import consistency
- Update all path references to new structure
- Ensure all tests and functionality work after refactor

BREAKING CHANGE: Database files and some test files moved to new directories
```
