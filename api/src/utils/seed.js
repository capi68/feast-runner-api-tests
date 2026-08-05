const bcrypt = require('bcryptjs');
const { query } = require('./db');

async function seedData() {
  // Seed a default restaurant for auth testing
  const existing = await query('SELECT id FROM restaurants WHERE email = $1', ['admin@feastrunner.com']);
  if (existing.rows.length === 0) {
    const hash = await bcrypt.hash('Restaurant123!', 10);
    await query(
      `INSERT INTO restaurants (name, cuisine_type, phone, email, password_hash, opening_hours, min_order_amount, delivery_radius_km, status)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      ['FeastRunner Admin', 'italian', '+1000000000', 'admin@feastrunner.com', hash, '08:00-22:00', 10.00, 15, 'active']
    );
    console.log('Seeded admin restaurant');
  }

  // Seed a default customer for auth testing
  const existingCustomer = await query('SELECT id FROM customers WHERE email = $1', ['customer@feastrunner.com']);
  if (existingCustomer.rows.length === 0) {
    const hash = await bcrypt.hash('Customer123!', 10);
    await query(
      `INSERT INTO customers (first_name, last_name, email, phone, password_hash)
       VALUES ($1, $2, $3, $4, $5)`,
      ['Test', 'Customer', 'customer@feastrunner.com', '+1111111111', hash]
    );
    console.log('Seeded admin customer');
  }

  // Seed a default courier for auth testing
  const existingCourier = await query('SELECT id FROM couriers WHERE email = $1', ['courier@feastrunner.com']);
  if (existingCourier.rows.length === 0) {
    const hash = await bcrypt.hash('Courier123!', 10);
    await query(
      `INSERT INTO couriers (first_name, last_name, email, phone, password_hash, vehicle_type, license_plate)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      ['Test', 'Courier', 'courier@feastrunner.com', '+2222222222', hash, 'motorcycle', 'ABC-123']
    );
    console.log('Seeded admin courier');
  }
}

module.exports = { seedData };
