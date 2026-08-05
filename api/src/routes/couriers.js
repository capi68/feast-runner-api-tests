const express = require('express');
const bcrypt = require('bcryptjs');
const { query } = require('../utils/db');
const { generateToken, requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_VEHICLE_TYPES = ['bicycle', 'motorcycle', 'car', 'scooter'];

/**
 * @swagger
 * /couriers:
 *   get:
 *     summary: List all active couriers
 *     tags: [Couriers]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: available
 *         schema:
 *           type: boolean
 *         description: Filter by availability
 *     responses:
 *       200:
 *         description: List of couriers
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    let sql = 'SELECT id, first_name, last_name, email, phone, vehicle_type, license_plate, is_available, is_active, created_at, updated_at FROM couriers WHERE is_active = TRUE';
    const params = [];

    if (req.query.available !== undefined) {
      sql += ' AND is_available = $1';
      params.push(req.query.available === 'true');
    }
    sql += ' ORDER BY last_name ASC';

    const result = await query(sql, params);
    res.json(result.rows);
  } catch (err) {
    console.error('Error listing couriers:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /couriers:
 *   post:
 *     summary: Register a new courier (no auth required)
 *     tags: [Couriers]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [first_name, last_name, email, phone, password, vehicle_type]
 *             properties:
 *               first_name:
 *                 type: string
 *                 example: "Carlos"
 *               last_name:
 *                 type: string
 *                 example: "Ramirez"
 *               email:
 *                 type: string
 *                 example: "carlos@courier.com"
 *               phone:
 *                 type: string
 *                 example: "+1987654321"
 *               password:
 *                 type: string
 *                 example: "Courier123!"
 *               vehicle_type:
 *                 type: string
 *                 enum: [bicycle, motorcycle, car, scooter]
 *               license_plate:
 *                 type: string
 *                 example: "XYZ-789"
 *     responses:
 *       201:
 *         description: Courier created
 *       400:
 *         description: Validation error
 *       409:
 *         description: Email already exists
 */
router.post('/', async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['first_name', 'last_name', 'email', 'phone', 'password', 'vehicle_type'];
    const missing = required.filter(f => !data[f]);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
      return res.status(400).json({ message: 'Invalid email format' });
    }

    if (!VALID_VEHICLE_TYPES.includes(data.vehicle_type)) {
      return res.status(400).json({ message: `Invalid vehicle_type. Must be one of: ${VALID_VEHICLE_TYPES.join(', ')}` });
    }

    if (data.password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters' });
    }

    const passwordHash = await bcrypt.hash(data.password, 10);

    const result = await query(
      `INSERT INTO couriers (first_name, last_name, email, phone, password_hash, vehicle_type, license_plate)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING id, first_name, last_name, email, phone, vehicle_type, license_plate, is_available, is_active, created_at, updated_at`,
      [data.first_name, data.last_name, data.email, data.phone, passwordHash, data.vehicle_type, data.license_plate || null]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    if (err.code === '23505') {
      return res.status(409).json({ message: 'Email already exists' });
    }
    console.error('Error creating courier:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /couriers/login:
 *   post:
 *     summary: Authenticate courier and receive JWT token
 *     tags: [Couriers]
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
      'SELECT * FROM couriers WHERE email = $1 AND is_active = TRUE',
      [email]
    );
    const courier = result.rows[0];

    if (!courier || !(await bcrypt.compare(password, courier.password_hash))) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const token = generateToken({ id: courier.id, email: courier.email, role: 'courier' });
    res.json({ message: 'Login successful', token, courier_id: courier.id });
  } catch (err) {
    console.error('Error during courier login:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /couriers/{id}:
 *   get:
 *     summary: Get courier by ID
 *     tags: [Couriers]
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
 *         description: Courier found
 *       404:
 *         description: Courier not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query(
      'SELECT id, first_name, last_name, email, phone, vehicle_type, license_plate, is_available, is_active, created_at, updated_at FROM couriers WHERE id = $1',
      [id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Courier not found' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error getting courier:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /couriers/{id}:
 *   put:
 *     summary: Update courier
 *     tags: [Couriers]
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
 *               vehicle_type:
 *                 type: string
 *               license_plate:
 *                 type: string
 *               is_available:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Courier updated
 *       400:
 *         description: Cannot change availability with active delivery
 *       404:
 *         description: Courier not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    if (data.vehicle_type && !VALID_VEHICLE_TYPES.includes(data.vehicle_type)) {
      return res.status(400).json({ message: `Invalid vehicle_type. Must be one of: ${VALID_VEHICLE_TYPES.join(', ')}` });
    }

    // Can't set available to true if has active delivery
    if (data.is_available === true) {
      const activeDelivery = await query(
        "SELECT COUNT(*) as count FROM deliveries WHERE courier_id = $1 AND status IN ('assigned', 'picked_up', 'in_transit')",
        [id]
      );
      if (parseInt(activeDelivery.rows[0].count) > 0) {
        return res.status(400).json({ message: 'Cannot set available while having an active delivery' });
      }
    }

    const allowed = ['first_name', 'last_name', 'phone', 'vehicle_type', 'license_plate', 'is_available'];
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
      `UPDATE couriers SET ${setClauses.join(', ')} WHERE id = $${paramIndex} AND is_active = TRUE
       RETURNING id, first_name, last_name, email, phone, vehicle_type, license_plate, is_available, is_active, created_at, updated_at`,
      values
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Courier not found' });
    }

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating courier:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /couriers/{id}:
 *   delete:
 *     summary: Delete courier (fails if has active delivery)
 *     tags: [Couriers]
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
 *         description: Courier deleted
 *       404:
 *         description: Courier not found
 *       409:
 *         description: Has active delivery
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM couriers WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Courier not found' });
    }

    const activeDelivery = await query(
      "SELECT COUNT(*) as count FROM deliveries WHERE courier_id = $1 AND status IN ('assigned', 'picked_up', 'in_transit')",
      [id]
    );
    if (parseInt(activeDelivery.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete courier with active delivery' });
    }

    await query('DELETE FROM deliveries WHERE courier_id = $1', [id]);
    await query('DELETE FROM couriers WHERE id = $1', [id]);
    res.json({ message: 'Courier deleted' });
  } catch (err) {
    console.error('Error deleting courier:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
