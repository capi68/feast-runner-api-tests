const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

/**
 * @swagger
 * /addresses:
 *   get:
 *     summary: List addresses (filterable by customer_id)
 *     tags: [Addresses]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: customer_id
 *         schema:
 *           type: integer
 *     responses:
 *       200:
 *         description: List of addresses
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    const { customer_id } = req.query;
    let sql = 'SELECT * FROM addresses';
    const params = [];

    if (customer_id) {
      sql += ' WHERE customer_id = $1';
      params.push(customer_id);
    }
    sql += ' ORDER BY is_default DESC, created_at DESC';

    const result = await query(sql, params);
    const rows = result.rows.map(r => ({
      ...r,
      latitude: r.latitude ? parseFloat(r.latitude) : null,
      longitude: r.longitude ? parseFloat(r.longitude) : null,
    }));
    res.json(rows);
  } catch (err) {
    console.error('Error listing addresses:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /addresses:
 *   post:
 *     summary: Create a new address for a customer
 *     tags: [Addresses]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [customer_id, label, street, city, state, zip_code]
 *             properties:
 *               customer_id:
 *                 type: integer
 *               label:
 *                 type: string
 *                 example: "Home"
 *               street:
 *                 type: string
 *                 example: "123 Main St"
 *               city:
 *                 type: string
 *                 example: "Springfield"
 *               state:
 *                 type: string
 *                 example: "IL"
 *               zip_code:
 *                 type: string
 *                 example: "62701"
 *               latitude:
 *                 type: number
 *                 example: 39.7817
 *               longitude:
 *                 type: number
 *                 example: -89.6501
 *               is_default:
 *                 type: boolean
 *                 example: true
 *     responses:
 *       201:
 *         description: Address created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Customer not found
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['customer_id', 'label', 'street', 'city', 'state', 'zip_code'];
    const missing = required.filter(f => !data[f] && data[f] !== 0);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    // Validate coordinates
    if (data.latitude !== undefined && data.latitude !== null) {
      const lat = parseFloat(data.latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        return res.status(400).json({ message: 'latitude must be between -90 and 90' });
      }
    }
    if (data.longitude !== undefined && data.longitude !== null) {
      const lon = parseFloat(data.longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        return res.status(400).json({ message: 'longitude must be between -180 and 180' });
      }
    }

    // Verify customer exists
    const customer = await query('SELECT id FROM customers WHERE id = $1 AND is_active = TRUE', [data.customer_id]);
    if (customer.rows.length === 0) {
      return res.status(404).json({ message: 'Customer not found or inactive' });
    }

    // Handle default flag — unset others if this is default
    if (data.is_default) {
      await query('UPDATE addresses SET is_default = FALSE WHERE customer_id = $1', [data.customer_id]);
    }

    const result = await query(
      `INSERT INTO addresses (customer_id, label, street, city, state, zip_code, latitude, longitude, is_default)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *`,
      [
        data.customer_id, data.label, data.street, data.city, data.state, data.zip_code,
        data.latitude || null, data.longitude || null, data.is_default || false,
      ]
    );

    const address = {
      ...result.rows[0],
      latitude: result.rows[0].latitude ? parseFloat(result.rows[0].latitude) : null,
      longitude: result.rows[0].longitude ? parseFloat(result.rows[0].longitude) : null,
    };
    res.status(201).json(address);
  } catch (err) {
    console.error('Error creating address:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /addresses/{id}:
 *   get:
 *     summary: Get address by ID
 *     tags: [Addresses]
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
 *         description: Address found
 *       404:
 *         description: Address not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM addresses WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Address not found' });
    }
    const address = {
      ...result.rows[0],
      latitude: result.rows[0].latitude ? parseFloat(result.rows[0].latitude) : null,
      longitude: result.rows[0].longitude ? parseFloat(result.rows[0].longitude) : null,
    };
    res.json(address);
  } catch (err) {
    console.error('Error getting address:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /addresses/{id}:
 *   put:
 *     summary: Update address
 *     tags: [Addresses]
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
 *               label:
 *                 type: string
 *               street:
 *                 type: string
 *               city:
 *                 type: string
 *               state:
 *                 type: string
 *               zip_code:
 *                 type: string
 *               latitude:
 *                 type: number
 *               longitude:
 *                 type: number
 *               is_default:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Address updated
 *       404:
 *         description: Address not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    if (data.latitude !== undefined && data.latitude !== null) {
      const lat = parseFloat(data.latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        return res.status(400).json({ message: 'latitude must be between -90 and 90' });
      }
    }
    if (data.longitude !== undefined && data.longitude !== null) {
      const lon = parseFloat(data.longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        return res.status(400).json({ message: 'longitude must be between -180 and 180' });
      }
    }

    // If setting as default, unset others for same customer
    if (data.is_default === true) {
      const current = await query('SELECT customer_id FROM addresses WHERE id = $1', [id]);
      if (current.rows.length === 0) {
        return res.status(404).json({ message: 'Address not found' });
      }
      await query('UPDATE addresses SET is_default = FALSE WHERE customer_id = $1', [current.rows[0].customer_id]);
    }

    const allowed = ['label', 'street', 'city', 'state', 'zip_code', 'latitude', 'longitude', 'is_default'];
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
      `UPDATE addresses SET ${setClauses.join(', ')} WHERE id = $${paramIndex} RETURNING *`,
      values
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Address not found' });
    }

    const address = {
      ...result.rows[0],
      latitude: result.rows[0].latitude ? parseFloat(result.rows[0].latitude) : null,
      longitude: result.rows[0].longitude ? parseFloat(result.rows[0].longitude) : null,
    };
    res.json(address);
  } catch (err) {
    console.error('Error updating address:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /addresses/{id}:
 *   delete:
 *     summary: Delete address (fails if referenced by pending orders)
 *     tags: [Addresses]
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
 *         description: Address deleted
 *       404:
 *         description: Address not found
 *       409:
 *         description: Referenced by pending orders
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const exists = await query('SELECT id FROM addresses WHERE id = $1', [id]);
    if (exists.rows.length === 0) {
      return res.status(404).json({ message: 'Address not found' });
    }

    const pending = await query(
      "SELECT COUNT(*) as count FROM orders WHERE address_id = $1 AND status IN ('placed', 'confirmed', 'preparing', 'ready', 'picked_up')",
      [id]
    );
    if (parseInt(pending.rows[0].count) > 0) {
      return res.status(409).json({ message: 'Cannot delete address referenced by pending orders' });
    }

    await query('DELETE FROM addresses WHERE id = $1', [id]);
    res.json({ message: 'Address deleted' });
  } catch (err) {
    console.error('Error deleting address:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
