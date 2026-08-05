const express = require('express');
const bcrypt = require('bcryptjs');
const { query } = require('../utils/db');
const { generateToken, requireAuth } = require('../middleware/auth');

const router = express.Router();

/**
 * @swagger
 * /customers:
 *   get:
 *     summary: List all active customers
 *     tags: [Customers]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of customers
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const result = await query(
      'SELECT id, first_name, last_name, email, phone, is_active, created_at, updated_at FROM customers WHERE is_active = TRUE ORDER BY last_name ASC'
    );
    res.json(result.rows);
  } catch (err) {
    console.error('Error listing customers:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /customers:
 *   post:
 *     summary: Register a new customer (no auth required)
 *     tags: [Customers]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [first_name, last_name, email, phone, password]
 *             properties:
 *               first_name:
 *                 type: string
 *                 example: "Ana"
 *               last_name:
 *                 type: string
 *                 example: "Lopez"
 *               email:
 *                 type: string
 *                 example: "ana@email.com"
 *               phone:
 *                 type: string
 *                 example: "+1234567890"
 *               password:
 *                 type: string
 *                 example: "Customer123!"
 *     responses:
 *       201:
 *         description: Customer created
 *       400:
 *         description: Validation error
 *       409:
 *         description: Email already exists
 */
router.post('/', async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['first_name', 'last_name', 'email', 'phone', 'password'];
    const missing = required.filter(f => !data[f]);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
      return res.status(400).json({ message: 'Invalid email format' });
    }

    if (data.password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters' });
    }

    const passwordHash = await bcrypt.hash(data.password, 10);

    const result = await query(
      `INSERT INTO customers (first_name, last_name, email, phone, password_hash)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, first_name, last_name, email, phone, is_active, created_at, updated_at`,
      [data.first_name, data.last_name, data.email, data.phone, passwordHash]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    if (err.code === '23505') {
      return res.status(409).json({ message: 'Email already exists' });
    }
    console.error('Error creating customer:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /customers/login:
 *   post:
 *     summary: Authenticate customer and receive JWT token
 *     tags: [Customers]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [email, password]
 *             properties:
 *               email:
 *                 type: string
 *               password:
 *                 type: string
 *     responses:
 *       200:
 *         description: Login successful
 *       401:
 *         description: Invalid credentials
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body || {};

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const result = await query(
      'SELECT * FROM customers WHERE email = $1 AND is_active = TRUE',
      [email]
    );
    const customer = result.rows[0];

    if (!customer || !(await bcrypt.compare(password, customer.password_hash))) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const token = generateToken({ id: customer.id, email: customer.email, role: 'customer' });
    res.json({ message: 'Login successful', token, customer_id: customer.id });
  } catch (err) {
    console.error('Error during customer login:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /customers/{id}:
 *   get:
 *     summary: Get customer by ID
 *     tags: [Customers]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *     responses:
 *       200:
 *         description: Customer found
 *       404:
 *         description: Customer not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query(
      'SELECT id, first_name, last_name, email, phone, is_active, created_at, updated_at FROM customers WHERE id = $1',
      [id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Customer not found' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error getting customer:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /customers/{id}:
 *   put:
 *     summary: Update customer
 *     tags: [Customers]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               first_name:
 *                 type: string
 *               last_name:
 *                 type: string
 *               phone:
 *                 type: string
 *     responses:
 *       200:
 *         description: Customer updated
 *       404:
 *         description: Customer not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    const allowed = ['first_name', 'last_name', 'phone'];
    const setClauses = [];
    const values = [];
    let paramIndex = 1;

    for (const key of allowed) {
      if (data[key] !== undefined) {
        setClauses.push(`${key} = $${paramIndex}`);
        values.push(data[key]);
        paramIndex++;
      }
    }

    if (setClauses.length === 0) {
      return res.status(400).json({ message: 'No valid fields to update' });
    }

    setClauses.push('updated_at = NOW()');
    values.push(id);

    const result = await query(
      `UPDATE customers SET ${setClauses.join(', ')} WHERE id = $${paramIndex} AND is_active = TRUE
       RETURNING id, first_name, last_name, email, phone, is_active, created_at, updated_at`,
      values
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Customer not found' });
    }

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating customer:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /customers/{id}:
 *   delete:
 *     summary: Delete customer (fails if has active orders)
 *     tags: [Customers]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *     responses:
 *       200:
 *         description: Customer deleted
 *       404:
 *         description: Customer not found
 *       409:
 *         description: Has active orders
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM customers WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Customer not found' });
    }

    const activeOrders = await query(
      "SELECT COUNT(*) as count FROM orders WHERE customer_id = $1 AND status IN ('placed', 'confirmed', 'preparing', 'ready', 'picked_up')",
      [id]
    );
    if (parseInt(activeOrders.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete customer with active orders' });
    }

    // Clean up completed/cancelled orders and related data
    const orderIds = await query('SELECT id FROM orders WHERE customer_id = $1', [id]);
    for (const order of orderIds.rows) {
      await query('DELETE FROM ratings WHERE order_id = $1', [order.id]);
      await query('DELETE FROM deliveries WHERE order_id = $1', [order.id]);
      await query('DELETE FROM order_items WHERE order_id = $1', [order.id]);
    }
    await query('DELETE FROM orders WHERE customer_id = $1', [id]);
    await query('DELETE FROM addresses WHERE customer_id = $1', [id]);
    await query('DELETE FROM customers WHERE id = $1', [id]);

    res.json({ message: 'Customer deleted' });
  } catch (err) {
    console.error('Error deleting customer:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
