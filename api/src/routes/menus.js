const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_STATUSES = ['draft', 'active', 'archived'];

/**
 * @swagger
 * /menus:
 *   get:
 *     summary: List all active menus (filterable by restaurant_id)
 *     tags: [Menus]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: restaurant_id
 *         schema:
 *           type: integer
 *         description: Filter by restaurant
 *     responses:
 *       200:
 *         description: List of menus
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const { restaurant_id } = req.query;
    let sql = 'SELECT * FROM menus';
    const params = [];

    if (restaurant_id) {
      sql += ' WHERE restaurant_id = $1';
      params.push(restaurant_id);
    }
    sql += ' ORDER BY created_at DESC';

    const result = await query(sql, params);
    res.json(result.rows);
  } catch (err) {
    console.error('Error listing menus:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menus:
 *   post:
 *     summary: Create a new menu
 *     tags: [Menus]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [restaurant_id, name]
 *             properties:
 *               restaurant_id:
 *                 type: integer
 *                 example: 1
 *               name:
 *                 type: string
 *                 example: "Lunch Menu"
 *               description:
 *                 type: string
 *                 example: "Available 11am-3pm"
 *     responses:
 *       201:
 *         description: Menu created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Restaurant not found
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['restaurant_id', 'name'];
    const missing = required.filter(f => !data[f] && data[f] !== 0);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    // Verify restaurant exists and is active
    const restaurant = await query(
      "SELECT id FROM restaurants WHERE id = $1 AND status = 'active'",
      [data.restaurant_id]
    );
    if (restaurant.rows.length === 0) {
      return res.status(404).json({ message: 'Restaurant not found or not active' });
    }

    const result = await query(
      `INSERT INTO menus (restaurant_id, name, description)
       VALUES ($1, $2, $3) RETURNING *`,
      [data.restaurant_id, data.name, data.description || null]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Error creating menu:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menus/{id}:
 *   get:
 *     summary: Get menu by ID
 *     tags: [Menus]
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
 *         description: Menu found
 *       404:
 *         description: Menu not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM menus WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Menu not found' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error getting menu:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menus/{id}:
 *   put:
 *     summary: Update menu (including status transitions)
 *     tags: [Menus]
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
 *               description:
 *                 type: string
 *               status:
 *                 type: string
 *                 enum: [draft, active, archived]
 *     responses:
 *       200:
 *         description: Menu updated
 *       400:
 *         description: Invalid transition or validation error
 *       404:
 *         description: Menu not found
 *       409:
 *         description: Another active menu exists for this restaurant
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    // Get current menu
    const current = await query('SELECT * FROM menus WHERE id = $1', [id]);
    if (current.rows.length === 0) {
      return res.status(404).json({ message: 'Menu not found' });
    }
    const menu = current.rows[0];

    // Validate status transition
    if (data.status) {
      if (!VALID_STATUSES.includes(data.status)) {
        return res.status(400).json({ message: `Invalid status. Must be one of: ${VALID_STATUSES.join(', ')}` });
      }

      const validTransitions = {
        draft: ['active', 'archived'],
        active: ['draft', 'archived'],
        archived: [],
      };

      if (!validTransitions[menu.status].includes(data.status)) {
        return res.status(400).json({
          message: `Cannot transition from '${menu.status}' to '${data.status}'. Allowed: ${validTransitions[menu.status].join(', ') || 'none (terminal state)'}`,
        });
      }

      // Only one active menu per restaurant
      if (data.status === 'active') {
        const existing = await query(
          "SELECT id FROM menus WHERE restaurant_id = $1 AND status = 'active' AND id != $2",
          [menu.restaurant_id, id]
        );
        if (existing.rows.length > 0) {
          return res.status(409).json({ message: 'Restaurant already has an active menu. Deactivate it first.' });
        }
      }
    }

    const allowed = ['name', 'description', 'status'];
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
      `UPDATE menus SET ${setClauses.join(', ')} WHERE id = $${paramIndex} RETURNING *`,
      values
    );

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating menu:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menus/{id}:
 *   delete:
 *     summary: Delete menu (fails if has items referenced in pending orders)
 *     tags: [Menus]
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
 *         description: Menu deleted
 *       404:
 *         description: Menu not found
 *       409:
 *         description: Menu has items in pending orders
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM menus WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Menu not found' });
    }

    // Check if any menu items are in pending orders
    const pendingOrders = await query(
      `SELECT COUNT(*) as count FROM order_items oi
       JOIN menu_items mi ON oi.menu_item_id = mi.id
       JOIN orders o ON oi.order_id = o.id
       WHERE mi.menu_id = $1 AND o.status IN ('placed', 'confirmed', 'preparing')`,
      [id]
    );
    if (parseInt(pendingOrders.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete menu with items referenced in pending orders' });
    }

    await query('DELETE FROM menu_items WHERE menu_id = $1', [id]);
    await query('DELETE FROM menus WHERE id = $1', [id]);
    res.json({ message: 'Menu deleted' });
  } catch (err) {
    console.error('Error deleting menu:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
