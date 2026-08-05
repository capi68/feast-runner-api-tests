const express = require('express');
const bcrypt = require('bcryptjs');
const { query } = require('../utils/db');
const { generateToken, requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_CUISINES = ['italian', 'mexican', 'japanese', 'chinese', 'american', 'indian', 'thai', 'mediterranean'];
const VALID_STATUSES = ['active', 'suspended', 'closed'];

/**
 * @swagger
 * /restaurants:
 *   get:
 *     summary: List all active restaurants
 *     tags: [Restaurants]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of active restaurants ordered by name
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const result = await query(
      'SELECT id, name, cuisine_type, phone, email, opening_hours, min_order_amount, delivery_radius_km, status, created_at, updated_at FROM restaurants WHERE status != $1 ORDER BY name ASC',
      ['closed']
    );
    const rows = result.rows.map(r => ({
      ...r,
      min_order_amount: parseFloat(r.min_order_amount),
      delivery_radius_km: parseFloat(r.delivery_radius_km),
    }));
    res.json(rows);
  } catch (err) {
    console.error('Error listing restaurants:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /restaurants:
 *   post:
 *     summary: Register a new restaurant (no auth required)
 *     tags: [Restaurants]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [name, cuisine_type, phone, email, password, opening_hours, min_order_amount, delivery_radius_km]
 *             properties:
 *               name:
 *                 type: string
 *                 example: "Mario's Pizzeria"
 *               cuisine_type:
 *                 type: string
 *                 enum: [italian, mexican, japanese, chinese, american, indian, thai, mediterranean]
 *               phone:
 *                 type: string
 *                 example: "+1234567890"
 *               email:
 *                 type: string
 *                 example: "mario@pizza.com"
 *               password:
 *                 type: string
 *                 example: "SecurePass123!"
 *               opening_hours:
 *                 type: string
 *                 example: "09:00-23:00"
 *               min_order_amount:
 *                 type: number
 *                 example: 15.00
 *               delivery_radius_km:
 *                 type: number
 *                 example: 10
 *     responses:
 *       201:
 *         description: Restaurant created
 *       400:
 *         description: Validation error
 *       409:
 *         description: Email already exists
 */
router.post('/', async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['name', 'cuisine_type', 'phone', 'email', 'password', 'opening_hours', 'min_order_amount', 'delivery_radius_km'];
    const missing = required.filter(f => !data[f] && data[f] !== 0);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
      return res.status(400).json({ message: 'Invalid email format' });
    }

    if (!VALID_CUISINES.includes(data.cuisine_type)) {
      return res.status(400).json({ message: `Invalid cuisine_type. Must be one of: ${VALID_CUISINES.join(', ')}` });
    }

    const minOrder = parseFloat(data.min_order_amount);
    if (isNaN(minOrder) || minOrder < 1.00 || minOrder > 500.00) {
      return res.status(400).json({ message: 'min_order_amount must be between 1.00 and 500.00' });
    }

    const radius = parseFloat(data.delivery_radius_km);
    if (isNaN(radius) || radius < 1 || radius > 50) {
      return res.status(400).json({ message: 'delivery_radius_km must be between 1 and 50' });
    }

    if (!data.password || data.password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters' });
    }

    const passwordHash = await bcrypt.hash(data.password, 10);

    const result = await query(
      `INSERT INTO restaurants (name, cuisine_type, phone, email, password_hash, opening_hours, min_order_amount, delivery_radius_km)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING id, name, cuisine_type, phone, email, opening_hours, min_order_amount, delivery_radius_km, status, created_at, updated_at`,
      [data.name, data.cuisine_type, data.phone, data.email, passwordHash, data.opening_hours, minOrder, radius]
    );

    const restaurant = {
      ...result.rows[0],
      min_order_amount: parseFloat(result.rows[0].min_order_amount),
      delivery_radius_km: parseFloat(result.rows[0].delivery_radius_km),
    };
    res.status(201).json(restaurant);
  } catch (err) {
    if (err.code === '23505') {
      return res.status(409).json({ message: 'Email already exists' });
    }
    console.error('Error creating restaurant:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /restaurants/login:
 *   post:
 *     summary: Authenticate restaurant and receive JWT token
 *     tags: [Restaurants]
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
      'SELECT * FROM restaurants WHERE email = $1 AND status != $2',
      [email, 'closed']
    );
    const restaurant = result.rows[0];

    if (!restaurant || !(await bcrypt.compare(password, restaurant.password_hash))) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const token = generateToken({ id: restaurant.id, email: restaurant.email, role: 'restaurant' });
    res.json({ message: 'Login successful', token, restaurant_id: restaurant.id });
  } catch (err) {
    console.error('Error during login:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /restaurants/{id}:
 *   get:
 *     summary: Get restaurant by ID
 *     tags: [Restaurants]
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
 *         description: Restaurant found
 *       404:
 *         description: Restaurant not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query(
      'SELECT id, name, cuisine_type, phone, email, opening_hours, min_order_amount, delivery_radius_km, status, created_at, updated_at FROM restaurants WHERE id = $1',
      [id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Restaurant not found' });
    }
    const restaurant = {
      ...result.rows[0],
      min_order_amount: parseFloat(result.rows[0].min_order_amount),
      delivery_radius_km: parseFloat(result.rows[0].delivery_radius_km),
    };
    res.json(restaurant);
  } catch (err) {
    console.error('Error getting restaurant:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /restaurants/{id}:
 *   put:
 *     summary: Update restaurant fields
 *     tags: [Restaurants]
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
 *               name:
 *                 type: string
 *               phone:
 *                 type: string
 *               opening_hours:
 *                 type: string
 *               min_order_amount:
 *                 type: number
 *               delivery_radius_km:
 *                 type: number
 *               status:
 *                 type: string
 *                 enum: [active, suspended, closed]
 *     responses:
 *       200:
 *         description: Restaurant updated
 *       404:
 *         description: Restaurant not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    // Validate status transition
    if (data.status) {
      if (!VALID_STATUSES.includes(data.status)) {
        return res.status(400).json({ message: `Invalid status. Must be one of: ${VALID_STATUSES.join(', ')}` });
      }
      const current = await query('SELECT status FROM restaurants WHERE id = $1', [id]);
      if (current.rows.length === 0) {
        return res.status(404).json({ message: 'Restaurant not found' });
      }
      const currentStatus = current.rows[0].status;
      if (currentStatus === 'closed') {
        return res.status(400).json({ message: "Cannot transition from terminal status 'closed'" });
      }
    }

    if (data.cuisine_type && !VALID_CUISINES.includes(data.cuisine_type)) {
      return res.status(400).json({ message: `Invalid cuisine_type. Must be one of: ${VALID_CUISINES.join(', ')}` });
    }

    if (data.min_order_amount !== undefined) {
      const val = parseFloat(data.min_order_amount);
      if (isNaN(val) || val < 1.00 || val > 500.00) {
        return res.status(400).json({ message: 'min_order_amount must be between 1.00 and 500.00' });
      }
    }

    if (data.delivery_radius_km !== undefined) {
      const val = parseFloat(data.delivery_radius_km);
      if (isNaN(val) || val < 1 || val > 50) {
        return res.status(400).json({ message: 'delivery_radius_km must be between 1 and 50' });
      }
    }

    const allowed = ['name', 'phone', 'cuisine_type', 'opening_hours', 'min_order_amount', 'delivery_radius_km', 'status'];
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

    setClauses.push(`updated_at = NOW()`);
    values.push(id);

    const result = await query(
      `UPDATE restaurants SET ${setClauses.join(', ')} WHERE id = $${paramIndex}
       RETURNING id, name, cuisine_type, phone, email, opening_hours, min_order_amount, delivery_radius_km, status, created_at, updated_at`,
      values
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Restaurant not found' });
    }

    const restaurant = {
      ...result.rows[0],
      min_order_amount: parseFloat(result.rows[0].min_order_amount),
      delivery_radius_km: parseFloat(result.rows[0].delivery_radius_km),
    };
    res.json(restaurant);
  } catch (err) {
    console.error('Error updating restaurant:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /restaurants/{id}:
 *   delete:
 *     summary: Delete restaurant (fails if has active menus)
 *     tags: [Restaurants]
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
 *         description: Restaurant deleted
 *       404:
 *         description: Restaurant not found
 *       409:
 *         description: Has active menus
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM restaurants WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Restaurant not found' });
    }

    const activeMenus = await query(
      "SELECT COUNT(*) as count FROM menus WHERE restaurant_id = $1 AND status = 'active'",
      [id]
    );
    if (parseInt(activeMenus.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete restaurant with active menus' });
    }

    // Delete cascade: menu_items → menus → orders/deliveries/ratings → restaurant
    const menuIds = await query('SELECT id FROM menus WHERE restaurant_id = $1', [id]);
    for (const menu of menuIds.rows) {
      await query('DELETE FROM menu_items WHERE menu_id = $1', [menu.id]);
    }
    await query('DELETE FROM menus WHERE restaurant_id = $1', [id]);

    // Delete orders and related data
    const orderIds = await query('SELECT id FROM orders WHERE restaurant_id = $1', [id]);
    for (const order of orderIds.rows) {
      await query('DELETE FROM ratings WHERE order_id = $1', [order.id]);
      await query('DELETE FROM deliveries WHERE order_id = $1', [order.id]);
      await query('DELETE FROM order_items WHERE order_id = $1', [order.id]);
    }
    await query('DELETE FROM orders WHERE restaurant_id = $1', [id]);

    await query('DELETE FROM restaurants WHERE id = $1', [id]);
    res.json({ message: 'Restaurant deleted' });
  } catch (err) {
    console.error('Error deleting restaurant:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
