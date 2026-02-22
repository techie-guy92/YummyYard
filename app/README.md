# Yummy Yard

[Yummy Yard](https://github.com/techie-guy92/YummyYard) is a versatile e-commerce backend built with **Django Rest Framework (DRF)**. This application provides seamless management of users, products, categories, and transactional processes, enhanced with **Docker support** for easy deployment. The backend also utilizes **JWT-based authentication**, **Celery** for background tasks, **signals** for efficient event handling, and comprehensive unit tests using `APITestCase`.

---

## Features

### **Users App**

- **Email Verification**: Verifies users' email addresses using unique tokens.
- **Password Reset**: Enables users to reset their passwords via secure email links.
- **User Profile Management**: Allows users to create and update their profiles.
- **Authentication**: Secure login using **JWT-based authentication**.
- **Fetch User Data**: Admins can retrieve detailed user records, including usernames, emails, and profiles.

### **Main App**

- **Product Management**: View and organize product data with sorting, filtering, and pagination options.
- **Category Management**: Manage a hierarchical structure of product categories.
- **Wishlist**: Save and organize products in personal wishlists.
- **Shopping Cart**: Users can add products to a cart and calculate totals.
- **Delivery Scheduling**: Enables delivery scheduling for shopping cart items with validated time slots and associated costs.
- **Admin Panel Integration**: Both apps integrate with Django's admin panel for efficient management of users, products, categories, and delivery schedules.
- **AJAX in Admin Panel**: JavaScript is used in the admin panel to dynamically fetch and display information using **AJAX**, enhancing responsiveness and interactivity.

---

## Installation and Setup

### Docker Installation

Yummy Yard is Dockerized for quick and hassle-free deployment. Ensure **Docker** and **Docker Compose** are installed on your system.

### Run the Application

1. **Build and Start Containers**:
   ```bash
   docker-compose up --build
   ```
2. **Stop Containers**:
   ```bash
   docker-compose down
   ```

The application will be available locally at:

```bash
http://127.0.0.1:8000/
```

---

## Admin Panel

The **admin panel** provides a user-friendly interface for managing the application. It includes:

- **AJAX Integration**: Dynamically fetches and displays specific details (e.g., product stats, user information) for better efficiency and responsiveness.
- **Modules**:
  - **User Management**: View profiles, verify accounts, and manage passwords.
  - **Product Management**: Organize and filter product data.
  - **Category Management**: Hierarchical control over product categories.
  - **Transaction Logs and Order Review**: Monitor activities in the store.

Access the admin panel at:

```bash
http://127.0.0.1:8000/admin/
```

---

## Celery Integration

Yummy Yard uses **Celery**, **Redis**, and **RabbitMQ** for asynchronous operations. This setup efficiently handles tasks like sending emails and cleaning expired data.

### Start Celery

1. **Start the worker**:

   ```bash
   on Windows: celery -A config.celery_config worker --pool=solo --loglevel=info
   on Linux:   celery -A config.celery_config worker --loglevel=info
   ```

2. **Run the beat scheduler**:
   ```bash
   celery -A config.celery_config beat --loglevel=info
   ```

---

## Testing

### Overview

Both apps (users and main) are thoroughly tested using **Django's `APITestCase`** framework to ensure robust functionality and reliability.

- **Test Organization**:
  - **`constants.py`**: Defines reusable test data such as user profiles, credentials, and invalid inputs.
  - **`utilities.py`**: Contains helper functions for generating mock data, creating test users, and simulating API requests.

### Running Tests

Execute all tests using:

```bash
python manage.py test
```

---

## API Endpoints

### Users App

- **Register**: `POST /users/sign-up/`  
  Registers a user and sends a verification email.
- **Login**: `POST /users/login/`  
  Authenticates a user and returns a JWT token.
- **Resend Verification Email**: `POST /users/resend-verification-email/`  
  Sends a new email verification link.
- **Verify Email**: `GET /users/verify-email/?token=<jwt>`  
  Confirms user email via token.
- **Reset Password**: `POST /users/reset-password/`  
  Initiates a password reset email.
- **Set New Password**: `POST /users/set-new-password/`  
  Updates user password with a valid token.
- **Fetch Users (Admin-only)**: `GET /users/<username>/`  
  Retrieves detailed user records.

### Main App

- **Fetch Products**: `GET /products/`  
  Retrieves a list of all products with pagination and filtering options.
- **Fetch Categories**: `GET /categories/`  
  Displays all categories, including parent-child relationships.
- **Manage Wishlist**: `POST /wishlist/`, `DELETE /wishlist/delete_by_product/<product_id>/`  
  Add or remove products from the user's wishlist.
- **Create Cart**: `POST /add_products/`  
  Adds products to the shopping cart.
- **Schedule Delivery**: `POST /add_schedule/`  
  Schedules delivery for items in the shopping cart.

---

## Authentication

Yummy Yard uses **JWT (JSON Web Tokens)** for authentication. After logging in, include the `Authorization` header in requests:

```http
Authorization: Bearer <token>
```

---

## Contributing

Contributions are always welcome! Fork this repository, create a branch, and submit your pull request. For larger changes, open an issue to discuss your ideas.
