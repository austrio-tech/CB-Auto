# Ali Grandson Spare Parts — Knowledge Base Index

**Version:** 1.0  
**Created:** May 2026  
**Purpose:** Chatbot training data for the Ali Grandsons mobile app Support Center and any future AI-powered assistant.

This knowledge base is stored in the `KnowlegdeBase/` folder of the Ali Grandson Spare Parts Flutter project. It contains **12 documents** covering every aspect of the business that a support chatbot needs.

---

## Document List

| File | Topic |
|------|-------|
| `00_INDEX.md` (this file) | Master index and usage guide |
| `01_company_overview.md` | Company background, mission, contact info |
| `02_store_locations_warehouses.md` | 7 branch locations across Oman with addresses, phones, hours, and delivery coverage |
| `03_product_catalog.md` | 12 product categories, top products, brands, prices, and warranty summary |
| `04_ordering_and_delivery.md` | Step-by-step ordering guide, order statuses, delivery timeframes and policies |
| `05_payment_and_returns.md` | Payment methods, refund process, warranty claims |
| `06_customer_support_faqs.md` | Complete FAQ database organised by topic (Account, Products, Orders, Delivery, Payment, Returns, Technical, App Usage, Contact) |
| `07_vehicle_compatibility_guide.md` | Part recommendations per vehicle model, maintenance intervals for Oman climate |
| `08_promotions_and_loyalty.md` | Current promotions, Ali Points loyalty program, seasonal buying guide, corporate accounts |
| `09_app_user_guide.md` | Screen-by-screen walkthrough of the mobile app |
| `10_chatbot_responses_quick_reference.md` | Pre-written responses for all common intents |
| `11_oman_automotive_context.md` | Oman driving conditions, regional vehicle trends, climate impact on parts, public holidays |
| `12_database_schema.md` | Complete SQLite database schema — all 7 tables, columns, types, FK relationships, version history |

---

## How to Use This Knowledge Base for Chatbot Training

### Recommended Approach (RAG / Retrieval-Augmented Generation)

1. Index all `.md` files in a vector database (e.g. Pinecone, Chroma, Weaviate).
2. When a user asks a question, retrieve the top 3–5 most relevant chunks.
3. Pass the retrieved context + user question to the language model.
4. The model generates an answer grounded in the retrieved facts.

### Document Priority Order (for conflict resolution)

1. Document 10 (Quick Reference) — use as first-pass response templates
2. Document 06 (Full FAQs) — for detailed answers
3. Document 02 (Locations) — for address/contact queries
4. Document 04 (Ordering) — for process queries
5. Document 03 (Products) — for product/part queries
6. Document 05 (Payment/Returns) — for transaction queries
7. Document 07 (Vehicle Guide) — for compatibility queries
8. Document 08 (Promotions) — for pricing/offers queries
9. Document 11 (Context) — for regional/background queries
10. Document 01 (Company) — for general business queries

---

## Chatbot Personality Guidelines

- **Tone:** Friendly, professional, helpful, and knowledgeable.
- **Language:** English primarily; switch to Arabic if the user writes in Arabic.
- **Never guess.** If the answer is not in the knowledge base, direct the user to WhatsApp (+968 9576 0754) or email (aligrandsoncompany@gmail.com).
- Always offer a next action: *"Would you like help with anything else?"*
- For product compatibility: Always ask for vehicle make, model, and year if not provided.
- For orders: Always ask for the order number if discussing a specific order.
- For complaints: Express empathy first, then provide the escalation path.

---

## Escalation Rules

Escalate to a human agent when:

1. User expresses strong frustration or anger.
2. User asks about a complaint that has been ongoing for more than 1 day.
3. User asks for a refund above OMR 50.
4. User asks about a legal or regulatory matter.
5. User has been given the same answer twice and is still unsatisfied.

**Escalation contact:** WhatsApp +968 9576 0754

---

## Out-of-Scope Topics

The chatbot should politely decline:

- Medical advice
- Legal advice unrelated to our products
- Competitor product recommendations
- Political or religious topics
- Tyre sales (we do not sell tyres — refer to a tyre shop)

---

## Languages Supported

- **English** (primary)
- **Arabic** (العربية) — responses should mirror the formality of the Arabic question

---

## Data Freshness & Update Schedule

This knowledge base should be reviewed and updated:

- **Quarterly:** Product prices, stock highlights, promotions
- **Annually:** Branch hours, manager names, company details
- **As needed:** Whenever a new branch opens, a policy changes, or a major product line is added or discontinued

| | |
|---|---|
| Last reviewed | May 2026 |
| Next review due | August 2026 |
| Maintained by | Ali Grandson Spare Parts — IT / App Team |

---

## Static vs Dynamic Information

### Static (changes rarely — good for chatbot embedding)

- Company history and background
- Branch addresses and landmarks
- Vehicle compatibility information
- Maintenance intervals (climate-adjusted)
- Oman driving context
- Payment methods
- Return and warranty policy structure

### Dynamic (changes frequently — check live app/database)

- Product prices
- Stock levels (in stock / out of stock)
- Active promotional codes
- Delivery time estimates (may vary with demand)
- Branch phone numbers (rare changes)

For dynamic data, the chatbot should instruct users to:
> "Check the current price/stock in the Ali Grandsons app" OR  
> "Contact us on WhatsApp (+968 9576 0754) for the latest information."
