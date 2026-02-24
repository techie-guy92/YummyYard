# Yummy Yard (Django-DRF) - Stack E-Commerce Platform

[![Django](https://img.shields.io/badge/Django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15.2-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.4-blue.svg)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-green.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.2-red.svg)](https://redis.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-orange.svg)](https://www.rabbitmq.com/)
[![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)](https://www.docker.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-3.7+-orange.svg)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-latest-orange.svg)](https://grafana.com/)
[![Ansible](https://img.shields.io/badge/Ansible-2.16+-black.svg)](https://www.ansible.com/)

## Overview

**Yummy Yard** is a production-ready e-commerce backend platform built with Django Rest Framework (DRF). This project demonstrates a complete DevOps pipeline with containerized microservices, comprehensive monitoring, and infrastructure-as-code deployment.

The platform provides seamless management of users, products, categories, and transactional processes, enhanced with JWT authentication, Celery for background tasks, and full observability stack.

For complete App explanations, see the [Application README](./app/README.md).
And for detailed monitoring explanations, see the [Monitoring README](./monitoring/README.md).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Yummy Yard Platform                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────┐    ┌─────────────────┐                   │
│  │    Django App     │    │    PostgreSQL   │                   │
│  │      (Web)        │    │    (Database)   │                   │
│  └────────┬──────────┘    └────────┬────────┘                   │
│           │                        │                            │
│  ┌────────▼──────────┐    ┌────────▼────────┐                   │
│  │      Nginx        │    │      Redis      │                   │
│  │  (Reverse Proxy)  │    │     (Cache)     │                   │
│  └────────┬──────────┘    └────────┬────────┘                   │
│           │                        │                            │
│  ┌────────▼──────────┐    ┌────────▼────────┐                   │
│  │     RabbitMQ      │    │     Celery      │                   │
│  │  (Message Broker) │    │    (Workers)    │                   │
│  └────────┬──────────┘    └────────┬────────┘                   │
│           │                        │                            │
│  ┌────────▼──────────┐    ┌────────▼────────┐                   │
│  │      Flower       │    │   Celery Beat   │                   │
│  │(Celery Monitoring)│    │   (Scheduler)   │                   │
│  └───────────────────┘    └─────────────────┘                   │
│                                                                 │
├────────────────────────── MONITORING ───────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Prometheus  │  Grafana   │  Alertmanager │  Exporters    │  │
│  │  (Metrics)   │(Dashboards)│   (Alerts)    │ (7 Services)  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Core Services (8 containers)**
- **Web**: Django + Gunicorn application
- **Nginx**: Reverse proxy with SSL termination
- **PostgreSQL**: Primary database
- **Redis**: Caching layer
- **RabbitMQ**: Message broker for Celery
- **Celery**: Async task workers
- **Celery Beat**: Scheduled tasks
- **Flower**: Celery monitoring UI

### **Monitoring Stack (9 containers)**
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert handling and notifications
- **Exporters**: PostgreSQL, Redis, RabbitMQ, Celery, Nginx, Blackbox
- **Pre-configured dashboards** for all services

---

## Features

### **E-Commerce Functionality**
- **User Management**: Registration, email verification, password reset, JWT authentication
- **Product Management**: Browse, filter, sort, and paginate products
- **Category Management**: Hierarchical product categories
- **Shopping Cart**: Add/remove items, calculate totals
- **Wishlist**: Save favorite products
- **Delivery Scheduling**: Time-slot based delivery with cost calculation
- **Admin Panel**: Django admin with AJAX enhancements for dynamic data loading

### **DevOps & Infrastructure**
- **Docker Compose**: Complete containerized deployment
- **Ansible Automation**: Infrastructure-as-code for production deployments
- **SSL/TLS**: Self-signed certificates for development (Let's Encrypt ready)
- **Health Checks**: Comprehensive health monitoring for all services
- **Logging**: Centralized logging with rotation

### **Observability**
- **Metrics**: All services export Prometheus metrics
- **Dashboards**: 8+ pre-configured Grafana dashboards
- **Alerts**: Proactive alerting with Alertmanager
- **Tracing**: Request monitoring across services

---

## Documentation Structure

This project contains detailed documentation for each component:

| Directory | Documentation | Description |
|-----------|--------------|-------------|
| [`/app`](./app/README.md) | **Application README** | Detailed API endpoints, testing, Celery configuration, and Django app specifics |
| [`/monitoring`](./monitoring/README.md) | **Monitoring README** | Complete observability setup with Prometheus, Grafana, exporters, and alerting rules |
| [`/monitoring/runbooks`](./monitoring/runbooks/) | **Alert Runbooks** | Incident response procedures for each service alert |
| [`/ansible_automation`](./ansible_automation/) | **Ansible Playbooks** | Infrastructure automation for production deployment |

---

## Quick Start

### **Prerequisites**
- Docker and Docker Compose (v2.0+)
- Python 3.12+ (for local development)
- Ansible 2.16+ (for automated deployment)

### **Development Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/techie-guy92/YummyYard.git
   cd YummyYard
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   ```bash
   # Application
   http://localhost:8000
   https://yummyyard.local:8443 (with self-signed cert)

   # Admin Panel
   http://localhost:8000/admin

   # Monitoring
   http://localhost:3000  # Grafana (admin/admin)
   http://localhost:9090  # Prometheus
   http://localhost:5555  # Flower (Celery monitoring)
   ```

---

## Production Deployment

### **Ansible Automation**

The project includes complete Ansible playbooks for production deployment:

```bash
cd ansible_automation

# Deploy full stack
ansible-playbook -i inventory site.yml --ask-become-pass

# Deploy specific components
ansible-playbook -i inventory site.yml --tags app      # Core application only
ansible-playbook -i inventory site.yml --tags nginx    # Nginx + SSL only
ansible-playbook -i inventory site.yml --tags monitoring # Monitoring stack only
```

### **Deployment Features**
- Idempotent deployments
- Zero-downtime updates
- SSL certificate generation
- Persistent volumes for data
- Automated monitoring setup
- Grafana dashboards auto-provisioning

---

## API Endpoints

### **Users API**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/sign-up/` | POST | User registration with email verification |
| `/users/login/` | POST | JWT authentication |
| `/users/resend-verification-email/` | POST | Resend verification link |
| `/users/verify-email/` | GET | Verify email with token |
| `/users/reset-password/` | POST | Request password reset |
| `/users/set-new-password/` | POST | Set new password |
| `/users/<username>/` | GET | Fetch user details (admin) |

### **Products API**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/products/` | GET | List products with filtering |
| `/categories/` | GET | List categories |
| `/wishlist/` | POST/DELETE | Manage wishlist |
| `/add_products/` | POST | Add to cart |
| `/add_schedule/` | POST | Schedule delivery |

For complete API documentation, see the [Application README](./app/README.md).

---

## Monitoring Stack

### **Pre-configured Dashboards**

| Dashboard | Description | Source |
|-----------|-------------|--------|
| **Django Application** | Request rate, response times, errors | [17613_django.json](./monitoring/grafana/dashboards/17613_django.json.json) |
| **PostgreSQL** | Connections, queries, cache hit ratio | [9628_postgresql.json](./monitoring/grafana/dashboards/9628_postgresql.json) |
| **Redis** | Memory usage, commands, connected clients | [16056_redis.json](./monitoring/grafana/dashboards/16056_redis.json) |
| **RabbitMQ** | Queue sizes, message rates, connections | [10991_rabbitmq.json](./monitoring/grafana/dashboards/10991_rabbitmq.json) |
| **Celery** | Task rates, worker status, queue lengths | Built-in via celery-exporter |
| **Nginx** | Request rates, connections, status codes | [12708_nginx.json](./monitoring/grafana/dashboards/12708_nginx.json) |
| **Prometheus** | Target status, scrape performance | [3662_prometheus-v2.json](./monitoring/grafana/dashboards/3662_prometheus-v2.json) |
| **Blackbox** | External endpoint monitoring | [13659_blackbox.json](./monitoring/grafana/dashboards/13659_blackbox.json) |
| **Alertmanager** | Alert status and history | [9578-alertmanager.json](./monitoring/grafana/dashboards/9578-alertmanager.json) |

For detailed monitoring setup, see the [Monitoring README](./monitoring/README.md).

---

## Testing

The application includes comprehensive tests using Django's `APITestCase`:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users.tests
python manage.py test main.tests
```

Test utilities and constants are organized in:
- `users/tests/constants.py` - Reusable test data
- `users/tests/utilities.py` - Helper functions
- `main/tests/constants.py` - Product test data
- `main/tests/utilities.py` - Category test helpers

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first to discuss your ideas.

---

## Acknowledgments

- Built with [Django Rest Framework](https://www.django-rest-framework.org/)
- Container orchestration with [Docker](https://www.docker.com/)
- Monitoring stack powered by [Prometheus](https://prometheus.io/) & [Grafana](https://grafana.com/)
- Infrastructure automation with [Ansible](https://www.ansible.com/)

---

## Contact

**Project Maintainer**: [techie-guy92](https://github.com/techie-guy92)

**Email**: soheil.dalirii@gmail.com

**GitHub**: [https://github.com/techie-guy92/YummyYard](https://github.com/techie-guy92/YummyYard)
