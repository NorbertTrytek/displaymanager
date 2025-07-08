# TV Links Management System

## Overview

This is a Flask-based web application for managing TV links with an admin panel interface. The system allows administrators to configure and update URLs for different TV channels through a modern, responsive web interface. The application uses file-based storage for configuration and includes web scraping capabilities using Selenium.

## System Architecture

### Frontend Architecture
- **Framework**: Bootstrap 5 with dark theme
- **Styling**: Custom CSS with CSS variables for theming
- **JavaScript**: Vanilla JavaScript for form validation and UI interactions
- **Templates**: Jinja2 templating with template inheritance
- **Responsive Design**: Mobile-first approach using Bootstrap grid system

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Session Management**: Flask sessions with configurable secret key
- **File Storage**: JSON-based configuration storage
- **Web Scraping**: Selenium WebDriver integration for screenshot capabilities
- **Error Handling**: Flash messages for user feedback

### Data Storage
- **Configuration**: JSON file (`tv_links.json`) for storing TV channel URLs
- **Snapshots**: Local directory (`snapshots/`) for storing screenshot files
- **Session Data**: Flask session management for temporary data

## Key Components

### 1. Admin Panel (`admin.html`)
- **Purpose**: Main interface for managing TV links
- **Features**: 
  - Form-based URL editing with validation
  - Monitor name management (rename, add, delete)
  - Flash message system for feedback
  - Stats cards showing system metrics
  - Reset and refresh functionality
  - Modal dialogs for confirmations and monitor operations
  - Dropdown menus for monitor actions

### 2. Base Template (`base.html`)
- **Purpose**: Common layout and styling foundation
- **Features**:
  - Dark theme Bootstrap integration
  - Navigation bar with branding
  - Font Awesome icons
  - Responsive container layout

### 3. Flask Application (`app.py`)
- **Purpose**: Main application logic and routing
- **Features**:
  - URL validation and sanitization
  - JSON file management for TV links configuration
  - Session handling and flash messages
  - Route definitions for admin operations
  - API endpoints for monitor management (add, rename, delete)
  - Selenium WebDriver integration for screenshots
  - Background worker for automatic snapshots

### 4. Static Assets
- **CSS**: Custom styling with CSS variables for theming
- **JavaScript**: Form validation and UI enhancement
- **External Dependencies**: Bootstrap, Font Awesome via CDN

## Data Flow

1. **Initial Setup**: Application creates default configuration files if they don't exist
2. **Admin Access**: User accesses the admin panel through the root route
3. **Link Management**: Admin can update TV channel URLs through the web form
4. **Validation**: Client-side and server-side URL validation
5. **Storage**: Configuration changes are persisted to JSON file
6. **Feedback**: Flash messages provide user feedback on operations

## External Dependencies

### CDN Resources
- **Bootstrap 5**: UI framework and dark theme
- **Font Awesome 6**: Icon library
- **Bootstrap JavaScript**: Interactive components

### Python Packages
- **Flask**: Web framework
- **Selenium**: Web scraping and screenshot capabilities
- **Standard Library**: `os`, `json`, `threading`, `time`

### Browser Requirements
- **Chrome/Chromium**: Required for Selenium WebDriver functionality
- **Modern Browser**: For Bootstrap 5 and ES6 JavaScript features

## Deployment Strategy

### Environment Configuration
- **Session Secret**: Configurable via `SESSION_SECRET` environment variable
- **File Permissions**: Application manages local file creation and modification
- **Directory Structure**: Automatic creation of required directories

### Storage Requirements
- **Configuration File**: `tv_links.json` in application root
- **Snapshot Directory**: `snapshots/` for storing screenshots
- **Static Assets**: CSS/JS files served by Flask

### Scalability Considerations
- **File-based Storage**: Suitable for small to medium deployments
- **Single Instance**: Current design is single-instance focused
- **Threading**: Basic threading support for concurrent operations

## Changelog
- July 08, 2025: Initial setup with basic TV link management
- July 08, 2025: Added monitor management features (rename, add, delete)

## User Preferences

Preferred communication style: Simple, everyday language.