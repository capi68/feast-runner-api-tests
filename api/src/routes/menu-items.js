const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_CATEGORIES = ['appetizer', 'main', 'side', 'dessert', 'beverage', 'combo'];

/**
 * @swagger
 * /menu-items:
 *   get:
 *     summary: List menu items (filterable by menu_id)
 *     tags: [Menu Items]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: menu_id
 *         schema:
 *           type: integer
 *         description: Filter by menu
 *     responses:
 *       200:
 *         description: List of menu items
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const { menu_id } = req.query;
    let sql = 'SELECT * FROM menu_items';
    const params = [];

    if (menu_id) {
      sql += ' WHERE menu_id = $1';
      params.push(menu_id);
    }
    sql += ' ORDER BY category, name ASC';

    const result = await query(sql, params);
    const rows = result.rows.map(r => ({ ...r, price: parseFloat(r.price) }));
    res.json(rows);
  } catch (err) {
    console.error('Error listing menu items:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menu-items:
 *   post:
 *     summary: Create a new menu item
 *     tags: [Menu Items]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [menu_id, name, price, category, preparation_time_minutes]
 *             properties:
 *               menu_id:
 *                 type: integer
 *               name:
 *                 type: string
 *                 example: "Margherita Pizza"
 *               description:
 *                 type: string
 *               price:
 *                 type: number
 *                 example: 12.99
 *               category:
 *                 type: string
 *                 enum: [appetizer, main, side, dessert, beverage, combo]
 *               preparation_time_minutes:
 *                 type: integer
 *                 example: 25
 *     responses:
 *       201:
 *         description: Menu item created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Menu not found
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['menu_id', 'name', 'price', 'category', 'preparation_time_minutes'];
    const missing = required.filter(f => data[f] === undefined || data[f] === null || data[f] === '');
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    if (!VALID_CATEGORIES.includes(data.category)) {
      return res.status(400).json({ message: `Invalid category. Must be one of: ${VALID_CATEGORIES.join(', ')}` });
    }

    const price = parseFloat(data.price);
    if (isNaN(price) || price < 0.01 || price > 999.99) {
      return res.status(400).json({ message: 'price must be between 0.01 and 999.99' });
    }

    const prepTime = parseInt(data.preparation_time_minutes);
    if (isNaN(prepTime) || prepTime < 5 || prepTime > 120) {
      return res.status(400).json({ message: 'preparation_time_minutes must be between 5 and 120' });
    }

    // Verify menu exists
    const menu = await query('SELECT id, restaurant_id FROM menus WHERE id = $1', [data.menu_id]);
    if (menu.rows.length === 0) {
      return res.status(404).json({ message: 'Menu not found' });
    }

    const result = await query(
      `INSERT INTO menu_items (menu_id, name, description, price, category, preparation_time_minutes)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [data.menu_id, data.name, data.description || null, price, data.category, prepTime]
    );

    const item = { ...result.rows[0], price: parseFloat(result.rows[0].price) };
    res.status(201).json(item);
  } catch (err) {
    console.error('Error creating menu item:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menu-items/{id}:
 *   get:
 *     summary: Get menu item by ID
 *     tags: [Menu Items]
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
 *         description: Menu item found
 *       404:
 *         description: Menu item not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM menu_items WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Menu item not found' });
    }
    const item = { ...result.rows[0], price: parseFloat(result.rows[0].price) };
    res.json(item);
  } catch (err) {
    console.error('Error getting menu item:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menu-items/{id}:
 *   put:
 *     summary: Update menu item
 *     tags: [Menu Items]
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
 *               price:
 *                 type: number
 *               category:
 *                 type: string
 *               preparation_time_minutes:
 *                 type: integer
 *               is_available:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Menu item updated
 *       404:
 *         description: Menu item not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    if (data.category && !VALID_CATEGORIES.includes(data.category)) {
      return res.status(400).json({ message: `Invalid category. Must be one of: ${VALID_CATEGORIES.join(', ')}` });
    }

    if (data.price !== undefined) {
      const price = parseFloat(data.price);
      if (isNaN(price) || price < 0.01 || price > 999.99) {
        return res.status(400).json({ message: 'price must be between 0.01 and 999.99' });
      }
    }

    if (data.preparation_time_minutes !== undefined) {
      const prepTime = parseInt(data.preparation_time_minutes);
      if (isNaN(prepTime) || prepTime < 5 || prepTime > 120) {
        return res.status(400).json({ message: 'preparation_time_minutes must be between 5 and 120' });
      }
    }

    const allowed = ['name', 'description', 'price', 'category', 'preparation_time_minutes', 'is_available'];
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
      `UPDATE menu_items SET ${setClauses.join(', ')} WHERE id = $${paramIndex} RETURNING *`,
      values
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Menu item not found' });
    }

    const item = { ...result.rows[0], price: parseFloat(result.rows[0].price) };
    res.json(item);
  } catch (err) {
    console.error('Error updating menu item:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /menu-items/{id}:
 *   delete:
 *     summary: Delete menu item (fails if in pending orders)
 *     tags: [Menu Items]
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
 *         description: Menu item deleted
 *       404:
 *         description: Menu item not found
 *       409:
 *         description: Referenced in pending orders
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM menu_items WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Menu item not found' });
    }

    // Check pending orders
    const pending = await query(
      `SELECT COUNT(*) as count FROM order_items oi
       JOIN orders o ON oi.order_id = o.id
       WHERE oi.menu_item_id = $1 AND o.status IN ('placed', 'confirmed', 'preparing')`,
      [id]
    );
    if (parseInt(pending.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete menu item referenced in pending orders' });
    }

    await query('DELETE FROM menu_items WHERE id = $1', [id]);
    res.json({ message: 'Menu item deleted' });
  } catch (err) {
    console.error('Error deleting menu item:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
