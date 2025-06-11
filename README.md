# Jersey Homepage
Jersey Homepage 🇯🇪
An event discovery platform for Jersey, featuring event browsing, ticket purchasing via Stripe, and multi-role user management.
🚀 Quick Start
Prerequisites
* Docker and Docker Compose
* Git
Installation
1. Clone the repository:
git clone https://github.com/yourusername/jersey-homepage.git
cd jersey-homepage
1. Copy the environment file:
cp .env.example .env
1. Build and start the Docker containers:
docker-compose up --build
1. Run migrations:
docker-compose exec web python manage.py migrate
1. Create a superuser:
docker-compose exec web python manage.py createsuperuser
1. Visit http://localhost:8000 to see the homepage!
🏗️ Project Structure
jersey-homepage/
├── jersey_homepage/          # Django project settings
├── events/                   # Main application
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── media/                   # User-uploaded files
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
├── Dockerfile              # Docker image definition
└── README.md               # This file
🎯 Features (Planned)
* Event Discovery: Browse events by category, date, and price
* User Roles: Regular users, event organizers, and super admins
* Ticket System: QR code generation and PDF tickets
* Payment Integration: Stripe, Apple Pay, and Google Pay
* Email Notifications: Automated emails for bookings and updates
* Responsive Design: Mobile-first approach
🛠️ Tech Stack
* Backend: Django 5.0+, PostgreSQL
* Frontend: Django Templates, Bootstrap 5, HTMX
* Payments: Stripe
* Email: Django + SendGrid/AWS SES
* Deployment: Docker, Nginx, Gunicorn
📋 Development Milestones
* [x] Milestone 1: Project Setup & Basic Structure
* [ ] Milestone 2: User Authentication System
* [ ] Milestone 3: Event Model & Basic Display
* [ ] Milestone 4: Filtering & Search
* [ ] Milestone 5: Organizer Features
* [ ] Milestone 6: Payment Integration - Phase 1
* [ ] Milestone 7: Payment Integration - Phase 2
* [ ] Milestone 8: Ticket Management
* [ ] Milestone 9: Admin Dashboard
* [ ] Milestone 10: UI/UX Enhancement
* [ ] Milestone 11: Email System
* [ ] Milestone 12: Testing & Deployment
🧪 Running Tests
docker-compose exec web python manage.py test
📧 Contact
* Admin: admin@coderra.je
* Office: office@coderra.je
📄 License
This project is proprietary software for Jersey Homepage.

Built with ❤️ for Jersey
