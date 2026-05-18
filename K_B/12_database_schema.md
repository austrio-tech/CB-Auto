================================================================
KNOWLEDGE BASE — DOCUMENT 12
TOPIC: App Database Schema (Technical Reference)
================================================================

Database File  : alis_grandson.db  (SQLite, stored on-device)
Schema Version : 10
ORM / Driver   : sqflite (Flutter package)

This document describes every table in the app's local database — what
each column stores, its type, and how tables relate to each other.
Useful for developers, chatbot training on technical queries, and
understanding what data the app captures.

================================================================
1. TABLE: users
   Purpose: Stores all registered customer accounts.
================================================================

| # | Column   | Type    | Constraints              | Description                          |
|---|----------|---------|--------------------------|--------------------------------------|
| 1 | username | TEXT    | PRIMARY KEY              | Unique login handle chosen at signup. Cannot be changed after registration. |
| 2 | name     | TEXT    | NOT NULL                 | Customer's full display name.        |
| 3 | email    | TEXT    | UNIQUE, NOT NULL         | Login credential and notification address. Must be unique across all accounts. |
| 4 | phone    | TEXT    | NOT NULL                 | Customer's mobile number (used on orders and for delivery contact). |
| 5 | password | TEXT    | NOT NULL                 | Plain-text password (stored locally on device only). |
| 6 | dob      | TEXT    | NOT NULL                 | Date of birth in ISO-8601 format (YYYY-MM-DD). |

Notes:
  - username is the primary key (text, not auto-incremented integer).
  - email has a UNIQUE constraint — one account per email address.
  - phone was added in schema migration v5.

================================================================
2. TABLE: admins
   Purpose: Stores admin login credentials.
================================================================

| # | Column   | Type    | Constraints              | Description                          |
|---|----------|---------|--------------------------|--------------------------------------|
| 1 | id       | INTEGER | PRIMARY KEY AUTOINCREMENT| Auto-assigned row ID.                |
| 2 | email    | TEXT    | NOT NULL                 | Admin login ID (default: "admin").   |
| 3 | password | TEXT    | NOT NULL                 | Admin password (default: "admin123"). |

Notes:
  - Seeded with one default admin row on first install: email = "admin", password = "admin123".
  - Change the default credentials after first login for security.

================================================================
3. TABLE: spare_part_products
   Purpose: The product catalogue — every item the store sells.
================================================================

| #  | Column      | Type    | Constraints              | Description                          |
|----|-------------|---------|--------------------------|--------------------------------------|
| 1  | id          | INTEGER | PRIMARY KEY AUTOINCREMENT| Unique product ID.                   |
| 2  | name        | TEXT    | NOT NULL                 | Product name (e.g. "Brembo Ceramic Brake Pad"). |
| 3  | description | TEXT    |                          | Long-form product description. Can be NULL. |
| 4  | image       | BLOB    |                          | Raw image bytes (Uint8List). Stored directly in DB — no file path needed. Loaded separately for performance. |
| 5  | type        | TEXT    |                          | Vehicle/part category (e.g. "Brakes", "Engine", "Ignition"). |
| 6  | brand       | TEXT    |                          | Manufacturer / brand name (e.g. "Brembo", "Bosch", "NGK"). |
| 7  | model       | TEXT    |                          | Compatible vehicle model or compatibility note. |
| 8  | price       | REAL    | NOT NULL                 | Selling price in Omani Rials (OMR). |
| 9  | available   | INTEGER | NOT NULL                 | Units currently in stock. 0 = Out of Stock. < 10 = Low Stock. |

Notes:
  - image BLOB is excluded from list queries (getProducts) for performance;
    fetched individually via getProductImage(id) only when needed.
  - Low stock threshold: available > 0 AND available < 10.
  - Stock is decremented atomically when an order is placed (inside a DB transaction).
  - Table name uses an underscore: spare_part_products.

================================================================
4. TABLE: cart
   Purpose: Holds items a customer has added to their cart but not yet ordered.
================================================================

| # | Column        | Type    | Constraints                           | Description                          |
|---|---------------|---------|---------------------------------------|--------------------------------------|
| 1 | id            | INTEGER | PRIMARY KEY AUTOINCREMENT             | Unique cart row ID.                  |
| 2 | user_username | TEXT    | NOT NULL, FK → users(username)        | Which customer owns this cart item.  |
| 3 | product_id    | INTEGER | NOT NULL, FK → spare_part_products(id)| Which product was added.             |
| 4 | quantity      | INTEGER | NOT NULL                              | How many units the customer wants.   |

Notes:
  - If a customer adds the same product twice, quantity is merged (increased) rather than inserting a duplicate row.
  - The entire cart for a user is deleted atomically when placeOrder() succeeds.
  - Added in schema migration v6.

================================================================
5. TABLE: orders
   Purpose: Confirmed purchase orders placed by customers.
================================================================

| #  | Column               | Type    | Constraints                    | Description                          |
|----|----------------------|---------|--------------------------------|--------------------------------------|
| 1  | id                   | INTEGER | PRIMARY KEY AUTOINCREMENT      | Unique order ID (shown as #00001 format in the app). |
| 2  | user_username        | TEXT    | NOT NULL, FK → users(username) | Which customer placed this order.    |
| 3  | address              | TEXT    | NOT NULL                       | Delivery address entered at checkout. |
| 4  | phone                | TEXT    | NOT NULL                       | Contact phone for delivery.          |
| 5  | special_instructions | TEXT    |                                | Optional delivery notes (e.g. "Ring doorbell"). Added in v8. |
| 6  | payment_mode         | TEXT    | NOT NULL                       | "Cash on Delivery" or "Card".        |
| 7  | total_price          | REAL    | NOT NULL                       | Grand total in OMR at time of order. |
| 8  | status               | TEXT    | NOT NULL                       | Current order state. See status values below. |
| 9  | order_date           | TEXT    | NOT NULL                       | ISO-8601 datetime string when order was placed. |
| 10 | completion_date      | TEXT    |                                | ISO-8601 datetime when Delivered or Cancelled. Added in v9. |

Order Status Values (lifecycle):
  Pending    → Order received, awaiting admin action.
  Ready      → Order packed and ready for dispatch / pick-up.
  In Delivery → Out for delivery to the customer.
  Delivered  → Successfully delivered. completion_date is set.
  Cancelled  → Cancelled by admin (with reason). completion_date is set.

Notes:
  - orders and order_items were added in schema migration v7.
  - Revenue analytics only counts rows where status = 'Delivered'.

================================================================
6. TABLE: order_items
   Purpose: Individual product lines inside each order (one row per product per order).
================================================================

| # | Column     | Type    | Constraints                           | Description                          |
|---|------------|---------|---------------------------------------|--------------------------------------|
| 1 | id         | INTEGER | PRIMARY KEY AUTOINCREMENT             | Unique row ID.                       |
| 2 | order_id   | INTEGER | NOT NULL, FK → orders(id)             | Which order this item belongs to.    |
| 3 | product_id | INTEGER | NOT NULL, FK → spare_part_products(id)| Which product was ordered.           |
| 4 | quantity   | INTEGER | NOT NULL                              | Number of units purchased.           |
| 5 | price      | REAL    | NOT NULL                              | Unit price at time of purchase (snapshot — does not change if product price changes later). |

Notes:
  - price is captured at checkout time so historical orders remain accurate even if the product price changes later.
  - Added in schema migration v7 alongside the orders table.

================================================================
7. TABLE: faqs
   Purpose: Question-and-answer pairs shown in the Help & Support screen.
================================================================

| # | Column   | Type    | Constraints              | Description                          |
|---|----------|---------|--------------------------|--------------------------------------|
| 1 | id       | INTEGER | PRIMARY KEY AUTOINCREMENT| Unique FAQ ID.                       |
| 2 | question | TEXT    | NOT NULL                 | The FAQ question text.               |
| 3 | answer   | TEXT    | NOT NULL                 | The answer shown to the customer.    |

Notes:
  - Seeded with 5 default FAQ rows on first install (or when the table is empty).
  - Admin can add, edit, and delete FAQ entries from the Manage FAQs screen.
  - Admin can restore defaults from Manage FAQs → "Restore Defaults" button.
  - Added in schema migration v10 (latest).

================================================================
ENTITY-RELATIONSHIP SUMMARY
================================================================

  users ──────────────┬──── cart ──────────────── spare_part_products
                      │        (user_username FK)      (product_id FK)
                      │
                      └──── orders ─────────────── order_items ──── spare_part_products
                               (user_username FK)   (order_id FK)    (product_id FK)

  admins   — standalone, no foreign keys
  faqs     — standalone, no foreign keys

================================================================
SCHEMA VERSION HISTORY
================================================================

  v1–v4  : Original tables (users without phone, products, no cart/orders).
  v5     : Added phone column to users table.
  v6     : Added cart table.
  v7     : Added orders and order_items tables.
  v8     : Added special_instructions column to orders.
  v9     : Added completion_date column to orders.
  v10    : Added faqs table (current version).

================================================================
END OF DOCUMENT 12
================================================================
