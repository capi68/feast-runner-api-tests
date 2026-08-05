const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_STATUSES = ['assigned', 'picked_up', 'in_transit', 'delivered', 'failed'];
const TERMINAL_STATUSES = ['delivered', 'failed'];

const VALID_TRANSITIONS = {
  assigned: ['picked_up', 'failed'],
  picked_up: ['in_transit', 'failed'],
  in_transit: ['delivered', 'failed'],
  delivered: [],
  failed: [],
};

/**
 * @swagger
 * /deliveries:
 *   get:
 *     summary: List deliveries (filterable by courier_id, status)
 *     tags: [Deliveries]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: courier_id
 *         schema:
 *           type: integer
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: List of deliveries
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    let sql = 'SELECT * FROM deliveries WHERE 1=1';
    const params = [];
    let paramIndex = 1;

    if (req.query.courier_id) {
      sql += ` AND courier_id = $${paramIndex}`;
      params.push(req.query.courier_id);
      paramIndex++;
    }
    if (req.query.status) {
      sql += ` AND status = $${paramIndex}`;
      params.push(req.query.status);
      paramIndex++;
    }
    sql += ' ORDER BY created_at DESC';

    const result = await query(sql, params);
    const rows = result.rows.map(r => ({
      ...r,
      distance_km: r.distance_km ? parseFloat(r.distance_km) : null,
    }));
    res.json(rows);
  } catch (err) {
    console.error('Error listing deliveries:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /deliveries:
 *   post:
 *     summary: Create a delivery (assign courier to an order)
 *     tags: [Deliveries]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [order_id, courier_id]
 *             properties:
 *               order_id:
 *                 type: integer
 *               courier_id:
 *                 type: integer
 *               distance_km:
 *                 type: number
 *                 example: 5.2
 *     responses:
 *       201:
 *         description: Delivery created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Resource not found
 *       409:
 *         description: Duplicate delivery or courier unavailable
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['order_id', 'courier_id'];
    const missing = required.filter(f => !data[f] && data[f] !== 0);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    // Validate distance
    if (data.distance_km !== undefined && data.distance_km !== null) {
      const dist = parseFloat(data.distance_km);
      if (isNaN(dist) || dist < 0.1 || dist > 100) {
        return res.status(400).json({ message: 'distance_km must be between 0.1 and 100' });
      }
    }

    // Order must exist and be in 'ready' status
    const order = await query('SELECT * FROM orders WHERE id = $1', [data.order_id]);
    if (order.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }
    if (order.rows[0].status !== 'ready') {
      return res.status(400).json({ message: `Order must be in 'ready' status to assign delivery. Current: '${order.rows[0].status}'` });
    }

    // Check no duplicate delivery for this order
    const existingDelivery = await query('SELECT id FROM deliveries WHERE order_id = $1', [data.order_id]);
    if (existingDelivery.rows.length > 0) {
      return res.status(409).json({ message: 'Delivery already exists for this order' });
    }

    // Courier must exist, be active, and be available
    const courier = await query('SELECT * FROM couriers WHERE id = $1 AND is_active = TRUE', [data.courier_id]);
    if (courier.rows.length === 0) {
      return res.status(404).json({ message: 'Courier not found or inactive' });
    }
    if (!courier.rows[0].is_available) {
      return res.status(409).json({ message: 'Courier is not available' });
    }

    // Check courier doesn't have another active delivery
    const activeDelivery = await query(
      "SELECT COUNT(*) as count FROM deliveries WHERE courier_id = $1 AND status IN ('assigned', 'picked_up', 'in_transit')",
      [data.courier_id]
    );
    if (parseInt(activeDelivery.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Courier already has an active delivery' });
    }

    // Create delivery and set courier unavailable
    const result = await query(
      `INSERT INTO deliveries (order_id, courier_id, distance_km)
       VALUES ($1, $2, $3) RETURNING *`,
      [data.order_id, data.courier_id, data.distance_km || null]
    );

    // Set courier as unavailable
    await query('UPDATE couriers SET is_available = FALSE, updated_at = NOW() WHERE id = $1', [data.courier_id]);

    // Update order status to picked_up
    await query("UPDATE orders SET status = 'picked_up', updated_at = NOW() WHERE id = $1", [data.order_id]);

    const delivery = {
      ...result.rows[0],
      distance_km: result.rows[0].distance_km ? parseFloat(result.rows[0].distance_km) : null,
    };
    res.status(201).json(delivery);
  } catch (err) {
    console.error('Error creating delivery:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /deliveries/{id}:
 *   get:
 *     summary: Get delivery by ID
 *     tags: [Deliveries]
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
 *         description: Delivery found
 *       404:
 *         description: Delivery not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM deliveries WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Delivery not found' });
    }
    const delivery = {
      ...result.rows[0],
      distance_km: result.rows[0].distance_km ? parseFloat(result.rows[0].distance_km) : null,
    };
    res.json(delivery);
  } catch (err) {
    console.error('Error getting delivery:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /deliveries/{id}:
 *   put:
 *     summary: Update delivery status
 *     tags: [Deliveries]
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
 *               status:
 *                 type: string
 *                 enum: [assigned, picked_up, in_transit, delivered, failed]
 *     responses:
 *       200:
 *         description: Delivery updated
 *       400:
 *         description: Invalid status transition
 *       404:
 *         description: Delivery not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    const current = await query('SELECT * FROM deliveries WHERE id = $1', [id]);
    if (current.rows.length === 0) {
      return res.status(404).json({ message: 'Delivery not found' });
    }
    const delivery = current.rows[0];

    if (data.status) {
      if (!VALID_STATUSES.includes(data.status)) {
        return res.status(400).json({ message: `Invalid status. Must be one of: ${VALID_STATUSES.join(', ')}` });
      }

      const allowed = VALID_TRANSITIONS[delivery.status];
      if (!allowed.includes(data.status)) {
        return res.status(400).json({
          message: `Cannot transition from '${delivery.status}' to '${data.status}'. Allowed: ${allowed.join(', ') || 'none (terminal state)'}`,
        });
      }

      // Side effects on terminal statuses
      if (data.status === 'delivered') {
        // Set delivered timestamp
        await query('UPDATE deliveries SET delivered_at = NOW() WHERE id = $1', [id]);
        // Set courier available again
        await query('UPDATE couriers SET is_available = TRUE, updated_at = NOW() WHERE id = $1', [delivery.courier_id]);
        // Update order to delivered
        await query("UPDATE orders SET status = 'delivered', updated_at = NOW() WHERE id = $1", [delivery.order_id]);
      } else if (data.status === 'failed') {
        // Set courier available again
        await query('UPDATE couriers SET is_available = TRUE, updated_at = NOW() WHERE id = $1', [delivery.courier_id]);
      } else if (data.status === 'picked_up') {
        await query('UPDATE deliveries SET picked_up_at = NOW() WHERE id = $1', [id]);
      }
    }

    const setClauses = [];
    const values = [];
    let paramIndex = 1;

    if (data.status) {
      setClauses.push(`status = $${paramIndex}`);
      values.push(data.status);
      paramIndex++;
    }

    if (setClauses.length === 0) {
      return res.status(400).json({ message: 'No valid fields to update' });
    }

    setClauses.push('updated_at = NOW()');
    values.push(id);

    const result = await query(
      `UPDATE deliveries SET ${setClauses.join(', ')} WHERE id = $${paramIndex} RETURNING *`,
      values
    );

    const updated = {
      ...result.rows[0],
      distance_km: result.rows[0].distance_km ? parseFloat(result.rows[0].distance_km) : null,
    };
    res.json(updated);
  } catch (err) {
    console.error('Error updating delivery:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
