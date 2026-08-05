const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

/**
 * @swagger
 * /ratings:
 *   get:
 *     summary: List ratings (filterable by order_id)
 *     tags: [Ratings]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: order_id
 *         schema:
 *           type: integer
 *     responses:
 *       200:
 *         description: List of ratings
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const { order_id } = req.query;
    let sql = 'SELECT * FROM ratings';
    const params = [];

    if (order_id) {
      sql += ' WHERE order_id = $1';
      params.push(order_id);
    }
    sql += ' ORDER BY created_at DESC';

    const result = await query(sql, params);
    res.json(result.rows);
  } catch (err) {
    console.error('Error listing ratings:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /ratings:
 *   post:
 *     summary: Rate a delivered order
 *     tags: [Ratings]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [order_id, food_score, delivery_score]
 *             properties:
 *               order_id:
 *                 type: integer
 *               food_score:
 *                 type: integer
 *                 minimum: 1
 *                 maximum: 5
 *                 example: 4
 *               delivery_score:
 *                 type: integer
 *                 minimum: 1
 *                 maximum: 5
 *                 example: 5
 *               comment:
 *                 type: string
 *                 maxLength: 500
 *                 example: "Great food, fast delivery!"
 *     responses:
 *       201:
 *         description: Rating created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Order not found
 *       409:
 *         description: Rating already exists for this order
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['order_id', 'food_score', 'delivery_score'];
    const missing = required.filter(f => data[f] === undefined || data[f] === null || data[f] === '');
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    const foodScore = parseInt(data.food_score);
    if (isNaN(foodScore) || foodScore < 1 || foodScore > 5) {
      return res.status(400).json({ message: 'food_score must be between 1 and 5' });
    }

    const deliveryScore = parseInt(data.delivery_score);
    if (isNaN(deliveryScore) || deliveryScore < 1 || deliveryScore > 5) {
      return res.status(400).json({ message: 'delivery_score must be between 1 and 5' });
    }

    if (data.comment && data.comment.length > 500) {
      return res.status(400).json({ message: 'comment must be 500 characters or less' });
    }

    // Verify order exists and is delivered
    const order = await query('SELECT * FROM orders WHERE id = $1', [data.order_id]);
    if (order.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }
    if (order.rows[0].status !== 'delivered') {
      return res.status(400).json({ message: `Can only rate delivered orders. Current status: '${order.rows[0].status}'` });
    }

    // Check for duplicate rating
    const existing = await query('SELECT id FROM ratings WHERE order_id = $1', [data.order_id]);
    if (existing.rows.length > 0) {
      return res.status(409).json({ message: 'Rating already exists for this order' });
    }

    const result = await query(
      `INSERT INTO ratings (order_id, food_score, delivery_score, comment)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [data.order_id, foodScore, deliveryScore, data.comment || null]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Error creating rating:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /ratings/{id}:
 *   get:
 *     summary: Get rating by ID
 *     tags: [Ratings]
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
 *         description: Rating found
 *       404:
 *         description: Rating not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM ratings WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Rating not found' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error getting rating:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
