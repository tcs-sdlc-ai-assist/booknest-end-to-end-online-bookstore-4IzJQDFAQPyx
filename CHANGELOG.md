# Changelog

All notable changes to the BookNest project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added

- **User Authentication**
  - User registration with email validation and secure password hashing
  - Login and logout with JWT-based access tokens
  - Role-based access control (admin, customer)
  - Password reset functionality
  - User profile management

- **Book Catalog**
  - Browse books with pagination and filtering
  - Search books by title, author, ISBN, and genre
  - Book detail pages with full descriptions and metadata
  - Category and genre-based navigation
  - Book cover image support

- **Reviews & Ratings**
  - Authenticated users can submit book reviews
  - Star rating system (1-5 stars)
  - View all reviews for a book
  - Edit and delete own reviews
  - Average rating calculation per book

- **Shopping Cart**
  - Add books to cart with quantity selection
  - Update item quantities in cart
  - Remove items from cart
  - Persistent cart tied to user account
  - Cart total calculation

- **Checkout & Orders**
  - Checkout flow with shipping address entry
  - Order creation from cart contents
  - Order confirmation with summary details
  - Payment processing integration

- **Order Tracking**
  - View order history with status updates
  - Order detail pages with itemized breakdown
  - Order status progression (pending, processing, shipped, delivered, cancelled)
  - Order filtering by status and date

- **Admin Dashboard**
  - Admin-only access to management interface
  - Book inventory management (CRUD operations)
  - Order management and status updates
  - User account management
  - Sales and activity overview

- **Seed Data**
  - Database seeding script with sample books across multiple genres
  - Sample user accounts for testing (admin and customer roles)
  - Sample reviews and ratings
  - Sample orders in various statuses