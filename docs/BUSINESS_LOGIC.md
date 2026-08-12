# 📋 Business Logic — FeastRunner API

##  Authentication

- Three entity types can authenticate: Restaurant, Customer, Courier
- JWT tokens are valid for 24 hours
- All endpoints **except** registration (`POST /restaurants`, `POST /customers`, `POST /couriers`) and login endpoints require auth
- Send token as: `Authorization: Bearer <token>`
- Expired/invalid tokens return `401`

---

##  Restaurants

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/restaurants` | GET | ✅ | List non-closed restaurants (ordered by name ASC) |
| `/restaurants` | POST | ❌ | Register new restaurant |
| `/restaurants/:id` | GET | ✅ | Get restaurant by ID |
| `/restaurants/:id` | PUT | ✅ | Update restaurant fields |
| `/restaurants/:id` | DELETE | ✅ | Delete restaurant (fails if has active menus) |
| `/restaurants/login` | POST | ❌ | Authenticate |

### Rules
- Required fields: name, cuisine_type, phone, email, password, opening_hours, min_order_amount, delivery_radius_km
- Cuisine types: `italian`, `mexican`, `japanese`, `chinese`, `american`, `indian`, `thai`, `mediterranean`
- min_order_amount: 1.00 – 500.00
- delivery_radius_km: 1 – 50
- Email: valid format, unique (409 on duplicate)
- Password: min 8 characters, hashed with bcrypt
- Password never appears in any response
- DELETE returns 409 if restaurant has active menus

### Status Machine
```
active → suspended ✅
active → closed ✅
suspended → active ✅
suspended → closed ✅
closed → (nothing) ❌ terminal
```

---

##  Menus

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/menus` | GET | ✅ | List menus (filterable by `?restaurant_id=`) |
| `/menus` | POST | ✅ | Create new menu (starts in 'draft') |
| `/menus/:id` | GET | ✅ | Get menu by ID |
| `/menus/:id` | PUT | ✅ | Update menu fields/status |
| `/menus/:id` | DELETE | ✅ | Delete menu (fails if items in pending orders) |

### Rules
- Required fields: restaurant_id, name
- restaurant_id must reference an existing **active** restaurant (404 otherwise)
- New menus always start in `draft` status
- **Only ONE active menu per restaurant** (409 if attempting to activate a second)
- DELETE returns 409 if menu has items referenced in pending orders

### Status Machine
```
draft → active ✅
draft → archived ✅
active → draft ✅
active → archived ✅
archived → (nothing) ❌ terminal
```

---

##  Menu Items

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/menu-items` | GET | ✅ | List items (filterable by `?menu_id=`) |
| `/menu-items` | POST | ✅ | Create new item |
| `/menu-items/:id` | GET | ✅ | Get item by ID |
| `/menu-items/:id` | PUT | ✅ | Update item fields |
| `/menu-items/:id` | DELETE | ✅ | Delete item (fails if in pending orders) |

### Rules
- Required fields: menu_id, name, price, category, preparation_time_minutes
- menu_id must reference an existing menu (404 otherwise)
- Price: 0.01 – 999.99
- Categories: `appetizer`, `main`, `side`, `dessert`, `beverage`, `combo`
- preparation_time_minutes: 5 – 120
- is_available: boolean (default true)
- DELETE returns 409 if referenced in pending orders (placed, confirmed, preparing)

---

##  Customers

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/customers` | GET | ✅ | List active customers (ordered by last_name ASC) |
| `/customers` | POST | ❌ | Register new customer |
| `/customers/:id` | GET | ✅ | Get customer by ID |
| `/customers/:id` | PUT | ✅ | Update customer fields |
| `/customers/:id` | DELETE | ✅ | Delete customer (fails if has active orders) |
| `/customers/login` | POST | ❌ | Authenticate |

### Rules
- Required fields: first_name, last_name, email, phone, password
- Email: valid format, unique (409 on duplicate)
- Password: min 8 characters
- DELETE returns 409 if customer has active orders (placed through picked_up)

---

##  Addresses

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/addresses` | GET | ✅ | List addresses (filterable by `?customer_id=`) |
| `/addresses` | POST | ✅ | Create address for a customer |
| `/addresses/:id` | GET | ✅ | Get address by ID |
| `/addresses/:id` | PUT | ✅ | Update address fields |
| `/addresses/:id` | DELETE | ✅ | Delete address (fails if in pending orders) |

### Rules
- Required fields: customer_id, label, street, city, state, zip_code
- customer_id must reference an existing active customer (404 otherwise)
- latitude: -90 to 90 (optional)
- longitude: -180 to 180 (optional)
- is_default: boolean (default false)
- **Setting is_default=true unsets all other defaults for that customer**
- DELETE returns 409 if referenced by pending orders

---

##  Couriers

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/couriers` | GET | ✅ | List active couriers (filterable by `?available=true`) |
| `/couriers` | POST | ❌ | Register new courier |
| `/couriers/:id` | GET | ✅ | Get courier by ID |
| `/couriers/:id` | PUT | ✅ | Update courier fields |
| `/couriers/:id` | DELETE | ✅ | Delete courier (fails if has active delivery) |
| `/couriers/login` | POST | ❌ | Authenticate |

### Rules
- Required fields: first_name, last_name, email, phone, password, vehicle_type
- Vehicle types: `bicycle`, `motorcycle`, `car`, `scooter`
- Email: valid format, unique (409 on duplicate)
- Password: min 8 characters
- is_available: boolean (default true)
- **Cannot set is_available=true while having an active delivery** (400)
- DELETE returns 409 if courier has active delivery (assigned, picked_up, in_transit)

---

##  Orders

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/orders` | GET | ✅ | List orders (filterable by `?customer_id=`, `?restaurant_id=`, `?status=`) |
| `/orders` | POST | ✅ | Create order with items |
| `/orders/:id` | GET | ✅ | Get order by ID (includes items) |
| `/orders/:id` | PUT | ✅ | Update order status/notes |
| `/orders/:id` | DELETE | ✅ | Cancel order (only placed/confirmed) |
| `/orders/:id/items` | GET | ✅ | Get items for an order |

### Rules
- Required fields: customer_id, restaurant_id, address_id, items (array)
- customer_id must reference an existing active customer (404)
- restaurant_id must reference an existing **active** restaurant (404)
- address_id must belong to the specified customer (400)
- items array must have at least 1 item
- Each item needs: menu_item_id, quantity (1-99)
- All menu items must belong to the same restaurant (400)
- All menu items must be available (400)
- **Order total must meet restaurant's min_order_amount** (400)
- estimated_delivery_minutes = max preparation time + 20
- total_amount = sum of (unit_price × quantity) for all items
- unit_price is captured at order time (price snapshot)
- DELETE sets status to 'cancelled' (only from placed/confirmed)

### Status Machine
```
placed → confirmed ✅
placed → cancelled ✅
confirmed → preparing ✅
confirmed → cancelled ✅
preparing → ready ✅
ready → picked_up ✅
picked_up → delivered ✅
delivered → (nothing) ❌ terminal
cancelled → (nothing) ❌ terminal
```
**Note:** Can only cancel from `placed` or `confirmed`. Once `preparing`, no cancellation.

---

##  Deliveries

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/deliveries` | GET | ✅ | List deliveries (filterable by `?courier_id=`, `?status=`) |
| `/deliveries` | POST | ✅ | Assign courier to order |
| `/deliveries/:id` | GET | ✅ | Get delivery by ID |
| `/deliveries/:id` | PUT | ✅ | Update delivery status |

### Rules
- Required fields: order_id, courier_id
- order_id must reference an order with status `ready` (400 otherwise)
- **One delivery per order** (409 if delivery already exists)
- courier_id must reference an active, available courier (404/409)
- **Courier can only have ONE active delivery** (409)
- distance_km: 0.1 – 100 (optional)
- Creating delivery automatically:
  - Sets courier's is_available to FALSE
  - Sets order status to `picked_up`

### Status Machine
```
assigned → picked_up ✅ (sets picked_up_at timestamp)
assigned → failed ✅
picked_up → in_transit ✅
picked_up → failed ✅
in_transit → delivered ✅ (sets delivered_at, courier available, order delivered)
in_transit → failed ✅
delivered → (nothing) ❌ terminal
failed → (nothing) ❌ terminal
```

### Side Effects
| Transition | Side Effect |
|---|---|
| → delivered | Sets `delivered_at`, courier `is_available = true`, order `status = delivered` |
| → failed | Courier `is_available = true` |
| → picked_up | Sets `picked_up_at` |

---

##  Ratings

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/ratings` | GET | ✅ | List ratings (filterable by `?order_id=`) |
| `/ratings` | POST | ✅ | Rate a delivered order |
| `/ratings/:id` | GET | ✅ | Get rating by ID |

### Rules
- Required fields: order_id, food_score, delivery_score
- order_id must reference an order with status `delivered` (400 otherwise)
- **One rating per order** (409 if rating already exists)
- food_score: 1 – 5 (integer)
- delivery_score: 1 – 5 (integer)
- comment: max 500 characters (optional)

---

## 🔗 Relationships & Cascade

```
Restaurant (1) ──► (N) Menu (1) ──► (N) Menu Item
                                              │
Customer (1) ──► (N) Address                  │
     │                    │                   ▼
     └────────────────────┴──────► Order (1) ──► (N) Order Item
                                       │
                                       ├──► (1) Delivery ◄── Courier
                                       │
                                       └──► (1) Rating
```

### Delete Cascade Rules
- **Restaurant**: Fails if has active menus. If no active menus, cascades: menus → menu_items → orders → order_items/deliveries/ratings
- **Menu**: Fails if items referenced in pending orders. Otherwise cascades items.
- **Menu Item**: Fails if in pending orders.
- **Customer**: Fails if has active orders. Otherwise cascades: addresses, orders → items/deliveries/ratings
- **Address**: Fails if referenced by pending orders.
- **Courier**: Fails if has active delivery. Otherwise cascades deliveries.
