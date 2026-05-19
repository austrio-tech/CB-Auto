# Knowledge Base — Document 13: Chatbot Database Query Instructions

> **CRITICAL — READ FIRST.**  
> This document defines when the chatbot MUST return `data_needed` instead of
> answering from static knowledge. Treat these rules as hard requirements,
> not suggestions.

---

## Rule 1 — Product Catalogue: Always Query the Database

**Never answer product questions from the static knowledge base.**  
Prices, stock levels, descriptions, and availability change in real time.
Answering from cached text will give the customer wrong information.

### Trigger phrases (non-exhaustive)
- "Do you have …", "Is … in stock", "How much is …", "What is the price of …"
- "Show me your products", "What parts do you sell for …"
- "Is the [brake pad / oil filter / battery / …] available"
- Any question mentioning a brand name (Brembo, Bosch, NGK, K&N, Rain-X, Varta, KYB, Monroe)
- Any question mentioning a product category (brakes, filters, spark plugs, wipers, batteries, shocks)

### data_needed payload to return

**Searching by name or keyword** (user mentions a product name/type):
```json
{
  "description": "Live product search for: <keyword>",
  "table": "spare_part_products",
  "fields_needed": ["id", "name", "brand", "type", "description", "price", "available"],
  "filters": {}
}
```
> The app will return all products. Filter on the result by name/brand in your
> answer. Do not add name filters here — the app's search is handled separately.

**When the user asks about stock / availability generally:**
```json
{
  "description": "Check product catalogue and stock levels",
  "table": "spare_part_products",
  "fields_needed": ["id", "name", "brand", "price", "available"],
  "filters": {}
}
```

### How to present product results

Once you receive the database rows:
- `available = 0` → tell the customer the item is **Out of Stock**
- `available > 0` → tell the customer the item is **In Stock** and show the exact `price` (in OMR)
- `available < 10` (but > 0) → mention **Low Stock — order soon**
- Always format price as `OMR X.XXX`
- If multiple products match the query, list them in a short markdown table

---

## Rule 2 — Orders & Status: Always Query the Database

**Never guess or fabricate order information.**  
The customer is asking about their personal, live order data.
The app automatically adds the `user_username` filter so you will only
ever receive rows that belong to the customer who is asking.

### Trigger phrases (non-exhaustive)
- "Where is my order", "What is my order status", "Has my order been shipped"
- "My order #…", "I placed an order …", "When will my order arrive"
- "Can I cancel my order", "Has my order been delivered"
- "Show me my orders", "My purchase history", "What did I order"
- "Track my order", "My recent order"

### data_needed payload — order list (all orders for this user)
```json
{
  "description": "Fetch all orders for the current customer",
  "table": "orders",
  "fields_needed": ["id", "status", "order_date", "total_price", "address", "payment_mode", "completion_date", "special_instructions"],
  "filters": {}
}
```
> **Do not add any user filter yourself.** The app injects `user_username`
> automatically. Adding it manually will cause a conflict.

### data_needed payload — specific order items (when customer gives an order number)
```json
{
  "description": "Fetch items for order #<id>",
  "table": "order_items",
  "fields_needed": ["order_id", "product_id", "quantity", "price"],
  "filters": { "order_id": <number> }
}
```

### Order status values and what to tell the customer

| Status | What to say |
|--------|------------|
| `Pending` | "Your order is confirmed and is being prepared by our team." |
| `Ready` | "Your order is packed and ready. If you chose pick-up, you can collect it now. If delivery, it will be dispatched shortly." |
| `In Delivery` | "Your order is on its way to your address. Our driver will call before arrival." |
| `Delivered` | "Your order was delivered on `completion_date`. If you have an issue, contact us within 7 days." |
| `Cancelled` | "Your order was cancelled on `completion_date`. If you did not request this, please contact us immediately on WhatsApp +968 9576 0754." |

### Formatting orders in your reply
- Show order ID as `Order #00001` (5-digit zero-padded)
- Show `order_date` in a readable format (e.g. "19 May 2026")
- Show `total_price` as `OMR X.XXX`
- If the user has multiple orders, list them as a markdown table sorted newest first

---

## Rule 3 — What NOT to Query the Database For

Use static knowledge (answer directly without `data_needed`) for:

| Topic | Reason |
|-------|--------|
| Company address, phone, email | Static — in Document 01 & 02 |
| Branch locations and hours | Static — in Document 02 |
| Delivery timeframes (general) | Static — in Document 04 |
| Return policy | Static — in Document 05 |
| Payment methods | Static — in Document 05 |
| Promotions and discounts | Static — in Document 08 |
| How to use the app | Static — in Document 09 |
| Vehicle compatibility (general advice) | Static — in Document 07 |
| Climate / maintenance intervals | Static — in Document 11 |
| General FAQs | Static — in Document 06 |

---

## Rule 4 — Never Expose Other Users' Data

- You will only ever receive rows that belong to the customer who asked.
- If a customer asks about "someone else's order", decline politely:
  > "I can only show you information about your own orders. For help with another order, please contact our team on WhatsApp +968 9576 0754."

---

## Summary Cheat Sheet

| User asks about… | Action |
|-----------------|--------|
| Product price / availability | `data_needed` → `spare_part_products` |
| Product stock level | `data_needed` → `spare_part_products` |
| Any specific part or brand | `data_needed` → `spare_part_products` |
| My order / order status | `data_needed` → `orders` |
| Order history / past orders | `data_needed` → `orders` |
| Items inside a specific order | `data_needed` → `order_items` |
| Company info, locations, policy | Answer from static knowledge base |
| How to place / cancel an order | Answer from static knowledge base |
| Promotions, payment, returns | Answer from static knowledge base |
