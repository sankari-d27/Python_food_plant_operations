🍱 Food Plant Operations Management System
Chennai Frozen Foods Pvt. Ltd.

A Python-based backend application developed to manage and monitor the daily operations of a frozen food manufacturing plant.

📌 Project Overview

The Food Plant Operations Management System is designed to replace manual registers, spreadsheets and disconnected operational records with a centralized digital management application.

The system provides REST APIs for managing production activities, products, suppliers, raw materials, machines, production lines, batches, quality inspections, approvals and user accounts.

It also includes JWT authentication, role-based authorization, historical data imports, validation reports and audit trail management.

🎯 Project Objectives
Centralize food plant operational records.
Manage production batches and production lines.
Monitor raw materials, suppliers and machines.
Maintain quality inspection records.
Implement secure user authentication.
Manage approval workflows.
Import and validate historical operational data.
Track important user activities through audit logs.
Improve data accuracy and operational efficiency.
🛠️ Technology Stack
Technology	Purpose
Python 3.11	Programming language
FastAPI	REST API development
SQLAlchemy	Database ORM
SQLite	Database storage
Pydantic	Data validation
Passlib	Password hashing
bcrypt	Password security
python-jose	JWT authentication
python-dotenv	Environment configuration
Pytest	Automated testing
Swagger UI	API documentation
📂 Project Modules
User Management
Authentication and Authorization
Product Management
Supplier Management
Raw Material Management
Machine Management
Production Line Management
Production Management
Batch Management
Quality Management
Approval Management
Historical Data Imports
Audit Trail Management
🏗️ Project Architecture

The application follows a layered architecture:

Router → Service → Repository → Database

Models: Define database tables using SQLAlchemy.
Schemas: Validate request and response data using Pydantic.
Routers: Handle HTTP requests and API endpoints.
Services: Implement business logic and validation.
Repositories: Handle database operations.
Strategies: Support different historical data import processes.
Imports: Manage historical data and validation reports.
Tests: Verify application functionality and business rules.
🔐 Authentication and Security

The application implements:

JWT-based authentication.
Password hashing.
Role-based authorization.
Protected API endpoints.
Active user validation.
Token expiration.
Audit logging.
Supported User Roles
Role	Responsibility
Admin	Administrative management
Production	Production operations
Quality	Quality inspections
Manager	Management and oversight
⚙️ Installation and Setup
1. Clone the Repository
bash
git clone YOUR_GITHUB_REPOSITORY_URL

2. Navigate to the Project Folder
bash
cd food-plant-operations-management-system

3. Create a Virtual Environment
bash
python -m venv venv

4. Activate the Virtual Environment

Windows PowerShell:

powershell
.\venv\Scripts\Activate.ps1

5. Install Dependencies
bash
pip install -r requirements.txt

6. Configure Environment Variables

Create a .env file and configure the required application settings, including a secure JWT secret key.

Do not upload your .env file to GitHub.

7. Run the Application
bash
uvicorn app.main:app --reload

📖 API Documentation

After starting the application, open:

Swagger UI:

http://127.0.0.1:8000/docs

OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

Swagger UI allows users to explore and test the available API endpoints.

🔄 HTTP Methods
Method	Operation
GET	Retrieve records
POST	Create records
PUT	Update records
PATCH	Partially update records
DELETE	Delete records
📥 Historical Data Import

The application includes historical data import functionality for:

Batch production records.
Raw material records.
Machine records.
Quality inspection records.

Import validation helps identify invalid or incomplete records and provides validation
