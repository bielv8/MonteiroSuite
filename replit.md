# Overview

This is a comprehensive management system for Monteiro Corretora de Seguros (Monteiro Insurance Brokerage). The system provides a complete CRM solution with integrated WhatsApp Business API communication, social media management capabilities, Kanban-based operations tracking, client and policy management, and multi-user administration. The platform centralizes all customer interactions and business processes in a unified interface designed specifically for insurance brokerage operations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 for responsive design with custom CSS styling
- **JavaScript Libraries**: 
  - SortableJS for drag-and-drop Kanban functionality
  - Native JavaScript for WhatsApp chat interface and real-time updates
- **Asset Management**: Static files served directly through Flask with organized CSS/JS structure

## Backend Architecture
- **Web Framework**: Flask with modular route organization
- **Database ORM**: SQLAlchemy with DeclarativeBase for database operations
- **Authentication**: Flask-Login for session management with role-based access control (admin, manager, user)
- **Form Handling**: WTForms with CSRF protection for secure form processing
- **Logging**: Python's logging module for application monitoring and debugging

## Data Storage Solutions
- **Primary Database**: SQLite (development) with PostgreSQL support via environment configuration
- **Connection Pooling**: SQLAlchemy engine with pool recycling and pre-ping health checks
- **Session Management**: Flask's built-in session handling with configurable secret keys

## Core Data Models
- **User Management**: Role-based user system with activity logging
- **Client Management**: Comprehensive client profiles with contact information, insurance preferences, and interaction history
- **Kanban Operations**: Flexible card-based workflow management with customizable columns
- **WhatsApp Integration**: Message storage and conversation threading
- **Policy Tracking**: Insurance policy management with expiration monitoring

## Authentication and Authorization
- **Login System**: Username/password authentication with "remember me" functionality
- **Role-Based Access**: Three-tier access control (admin, manager, user) with permission checking
- **Activity Logging**: Comprehensive audit trail of user actions and system interactions
- **Session Security**: Secure session management with configurable timeouts

## Business Logic Components
- **WhatsApp Service**: Dedicated service class for Meta Business API integration
- **Activity Tracking**: Centralized logging system for user actions and system events
- **Client Workflow**: Kanban-based client journey management from prospect to active customer
- **Communication History**: Unified interaction tracking across all communication channels

# External Dependencies

## WhatsApp Business API Integration
- **Meta Graph API**: Version 18.0 for WhatsApp Business messaging
- **Authentication**: Bearer token-based API access with configurable credentials
- **Features**: Send/receive messages, conversation management, business account integration
- **Webhook Support**: Ready for real-time message notifications and status updates

## Social Media APIs (Planned)
- **Instagram Business API**: For post scheduling and engagement monitoring
- **Facebook Graph API**: For page management and unified messaging
- **Integration Architecture**: Extensible service layer ready for social media platform connections

## Frontend Dependencies
- **Bootstrap 5**: CDN-delivered responsive framework
- **Font Awesome 6**: Icon library for consistent UI elements
- **SortableJS**: Drag-and-drop functionality for Kanban boards

## Database Connectivity
- **SQLite**: Default development database with file-based storage
- **PostgreSQL**: Production-ready via DATABASE_URL environment configuration
- **SQLAlchemy**: Database abstraction layer with migration support potential

## Security and Middleware
- **ProxyFix**: Werkzeug middleware for proper header handling behind reverse proxies
- **CSRF Protection**: WTForms integration for form security
- **Environment Configuration**: Secure credential management through environment variables

## Deployment Dependencies
- **Flask Development Server**: Built-in server for development
- **Production Ready**: WSGI-compatible for deployment with Gunicorn, uWSGI, or similar
- **Environment Variables**: DATABASE_URL, SESSION_SECRET, WHATSAPP_API_TOKEN configuration