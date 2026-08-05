const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DATABASE_HOST || 'localhost',
  port: parseInt(process.env.DATABASE_PORT || '5432'),
  user: process.env.DATABASE_USER || 'feastadmin',
  password: process.env.DATABASE_PASSWORD || 'feastpass123',
  database: process.env.DATABASE_NAME || 'feastrunner',
});

async function query(text, params) {
  const result = await pool.query(text, params);
  return result;
}

async function initDb() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS restaurants (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        cuisine_type VARCHAR(30) NOT NULL CHECK (cuisine_type IN ('italian','mexican','japanese','chinese','american','indian','thai','mediterranean')),
        phone VARCHAR(20) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        opening_hours VARCHAR(50) NOT NULL,
        min_order_amount NUMERIC(8,2) NOT NULL CHECK (min_order_amount BETWEEN 1.00 AND 500.00),
        delivery_radius_km NUMERIC(5,1) NOT NULL CHECK (delivery_radius_km BETWEEN 1 AND 50),
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','suspended','closed')),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS menus (
        id SERIAL PRIMARY KEY,
        restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
        name VARCHAR(100) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft','active','archived')),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_menu_per_restaurant
        ON menus (restaurant_id) WHERE status = 'active';

      CREATE TABLE IF NOT EXISTS menu_items (
        id SERIAL PRIMARY KEY,
        menu_id INTEGER NOT NULL REFERENCES menus(id),
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price NUMERIC(8,2) NOT NULL CHECK (price BETWEEN 0.01 AND 999.99),
        category VARCHAR(20) NOT NULL CHECK (category IN ('appetizer','main','side','dessert','beverage','combo')),
        preparation_time_minutes INTEGER NOT NULL CHECK (preparation_time_minutes BETWEEN 5 AND 120),
        is_available BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        phone VARCHAR(20) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS addresses (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        label VARCHAR(50) NOT NULL,
        street VARCHAR(200) NOT NULL,
        city VARCHAR(100) NOT NULL,
        state VARCHAR(50) NOT NULL,
        zip_code VARCHAR(20) NOT NULL,
        latitude NUMERIC(10,7) CHECK (latitude BETWEEN -90 AND 90),
        longitude NUMERIC(10,7) CHECK (longitude BETWEEN -180 AND 180),
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS couriers (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        phone VARCHAR(20) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        vehicle_type VARCHAR(20) NOT NULL CHECK (vehicle_type IN ('bicycle','motorcycle','car','scooter')),
        license_plate VARCHAR(20),
        is_available BOOLEAN DEFAULT TRUE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
        address_id INTEGER NOT NULL REFERENCES addresses(id),
        status VARCHAR(20) DEFAULT 'placed' CHECK (status IN ('placed','confirmed','preparing','ready','picked_up','delivered','cancelled')),
        notes TEXT,
        total_amount NUMERIC(10,2) DEFAULT 0,
        estimated_delivery_minutes INTEGER,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
        quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 99),
        unit_price NUMERIC(8,2) NOT NULL,
        special_instructions TEXT,
        created_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS deliveries (
        id SERIAL PRIMARY KEY,
        order_id INTEGER UNIQUE NOT NULL REFERENCES orders(id),
        courier_id INTEGER NOT NULL REFERENCES couriers(id),
        status VARCHAR(20) DEFAULT 'assigned' CHECK (status IN ('assigned','picked_up','in_transit','delivered','failed')),
        distance_km NUMERIC(6,1) CHECK (distance_km BETWEEN 0.1 AND 100),
        picked_up_at TIMESTAMP,
        delivered_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY,
        order_id INTEGER UNIQUE NOT NULL REFERENCES orders(id),
        food_score INTEGER NOT NULL CHECK (food_score BETWEEN 1 AND 5),
        delivery_score INTEGER NOT NULL CHECK (delivery_score BETWEEN 1 AND 5),
        comment VARCHAR(500),
        created_at TIMESTAMP DEFAULT NOW()
      );
    `);
    console.log('Database tables initialized');
  } finally {
    client.release();
  }
}

module.exports = { pool, query, initDb };
