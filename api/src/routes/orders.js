const express = require('express');
const { query } = require('../utils/db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

const VALID_STATUSES = ['placed', 'confirmed', 'preparing', 'ready', 'picked_up', 'delivered', 'cancelled'];
const CANCELLABLE_STATUSES = ['placed', 'confirmed'];

const VALID_TRANSITIONS = {
  placed: ['confirmed', 'cancelled'],
  confirmed: ['preparing', 'cancelled'],
  preparing: ['ready'],
  ready: ['picked_up'],
  picked_up: ['delivered'],
  delivered: [],
  cancelled: [],
};

/**
 * @swagger
 * /orders:
 *   get:
 *     summary: List all orders (filterable by customer_id, restaurant_id, status)
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: customer_id
 *         schema:
 *           type: integer
 *       - in: query
 *         name: restaurant_id
 *         schema:
 *           type: integer
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: List of orders
 */
router.get('/', requireAuth, async (req, res) => {
  try {
    let sql = 'SELECT * FROM orders WHERE 1=1';
    const params = [];
    let paramIndex = 1;

    if (req.query.customer_id) {
      sql += ` AND customer_id = $${paramIndex}`;
      params.push(req.query.customer_id);
      paramIndex++;
    }
    if (req.query.restaurant_id) {
      sql += ` AND restaurant_id = $${paramIndex}`;
      params.push(req.query.restaurant_id);
      paramIndex++;
    }
    if (req.query.status) {
      sql += ` AND status = $${paramIndex}`;
      params.push(req.query.status);
      paramIndex++;
    }
    sql += ' ORDER BY created_at DESC';

    const result = await query(sql, params);
    const rows = result.rows.map(r => ({ ...r, total_amount: parseFloat(r.total_amount) }));
    res.json(rows);
  } catch (err) {
    console.error('Error listing orders:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /orders:
 *   post:
 *     summary: Create a new order with items
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [customer_id, restaurant_id, address_id, items]
 *             properties:
 *               customer_id:
 *                 type: integer
 *               restaurant_id:
 *                 type: integer
 *               address_id:
 *                 type: integer
 *               notes:
 *                 type: string
 *               items:
 *                 type: array
 *                 items:
 *                   type: object
 *                   required: [menu_item_id, quantity]
 *                   properties:
 *                     menu_item_id:
 *                       type: integer
 *                     quantity:
 *                       type: integer
 *                       example: 2
 *                     special_instructions:
 *                       type: string
 *     responses:
 *       201:
 *         description: Order created
 *       400:
 *         description: Validation error
 *       404:
 *         description: Resource not found
 */
router.post('/', requireAuth, async (req, res) => {
  try {
    const data = req.body || {};

    const required = ['customer_id', 'restaurant_id', 'address_id', 'items'];
    const missing = required.filter(f => !data[f] && data[f] !== 0);
    if (missing.length > 0) {
      return res.status(400).json({ message: `Missing required fields: ${missing.join(', ')}` });
    }

    if (!Array.isArray(data.items) || data.items.length === 0) {
      return res.status(400).json({ message: 'Order must have at least 1 item' });
    }

    // Validate customer exists
    const customer = await query('SELECT id FROM customers WHERE id = $1 AND is_active = TRUE', [data.customer_id]);
    if (customer.rows.length === 0) {
      return res.status(404).json({ message: 'Customer not found or inactive' });
    }

    // Validate restaurant exists and is active
    const restaurant = await query("SELECT * FROM restaurants WHERE id = $1 AND status = 'active'", [data.restaurant_id]);
    if (restaurant.rows.length === 0) {
      return res.status(404).json({ message: 'Restaurant not found or not active' });
    }

    // Validate address exists and belongs to customer
    const address = await query('SELECT * FROM addresses WHERE id = $1 AND customer_id = $2', [data.address_id, data.customer_id]);
    if (address.rows.length === 0) {
      return res.status(400).json({ message: 'Address not found or does not belong to this customer' });
    }

    // Validate all items
    let totalAmount = 0;
    let maxPrepTime = 0;
    const validatedItems = [];

    for (const item of data.items) {
      if (!item.menu_item_id || !item.quantity) {
        return res.status(400).json({ message: 'Each item must have menu_item_id and quantity' });
      }

      const qty = parseInt(item.quantity);
      if (isNaN(qty) || qty < 1 || qty > 99) {
        return res.status(400).json({ message: 'quantity must be between 1 and 99' });
      }

      // Verify menu item exists, is available, and belongs to the restaurant
      const menuItem = await query(
        `SELECT mi.*, m.restaurant_id FROM menu_items mi
         JOIN menus m ON mi.menu_id = m.id
         WHERE mi.id = $1`,
        [item.menu_item_id]
      );

      if (menuItem.rows.length === 0) {
        return res.status(404).json({ message: `Menu item ${item.menu_item_id} not found` });
      }

      const mi = menuItem.rows[0];

      if (!mi.is_available) {
        return res.status(400).json({ message: `Menu item '${mi.name}' is not available` });
      }

      if (mi.restaurant_id !== data.restaurant_id) {
        return res.status(400).json({ message: `Menu item '${mi.name}' does not belong to this restaurant` });
      }

      const unitPrice = parseFloat(mi.price);
      totalAmount += unitPrice * qty;
      maxPrepTime = Math.max(maxPrepTime, mi.preparation_time_minutes);

      validatedItems.push({
        menu_item_id: item.menu_item_id,
        quantity: qty,
        unit_price: unitPrice,
        special_instructions: item.special_instructions || null,
      });
    }

    // Check minimum order amount
    const minOrder = parseFloat(restaurant.rows[0].min_order_amount);
    if (totalAmount < minOrder) {
      return res.status(400).json({
        message: `Order total (${totalAmount.toFixed(2)}) is below restaurant minimum (${minOrder.toFixed(2)})`,
      });
    }

    // Estimate delivery time: max prep time + 20 min delivery buffer
    const estimatedDelivery = maxPrepTime + 20;

    // Create order
    const orderResult = await query(
      `INSERT INTO orders (customer_id, restaurant_id, address_id, notes, total_amount, estimated_delivery_minutes)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [data.customer_id, data.restaurant_id, data.address_id, data.notes || null, totalAmount, estimatedDelivery]
    );
    const order = orderResult.rows[0];

    // Create order items
    const orderItems = [];
    for (const item of validatedItems) {
      const itemResult = await query(
        `INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, special_instructions)
         VALUES ($1, $2, $3, $4, $5) RETURNING *`,
        [order.id, item.menu_item_id, item.quantity, item.unit_price, item.special_instructions]
      );
      orderItems.push({ ...itemResult.rows[0], unit_price: parseFloat(itemResult.rows[0].unit_price) });
    }

    res.status(201).json({
      ...order,
      total_amount: parseFloat(order.total_amount),
      items: orderItems,
    });
  } catch (err) {
    console.error('Error creating order:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /orders/{id}:
 *   get:
 *     summary: Get order by ID (includes items)
 *     tags: [Orders]
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
 *         description: Order found
 *       404:
 *         description: Order not found
 */
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const result = await query('SELECT * FROM orders WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }

    const items = await query('SELECT * FROM order_items WHERE order_id = $1', [id]);
    const order = {
      ...result.rows[0],
      total_amount: parseFloat(result.rows[0].total_amount),
      items: items.rows.map(i => ({ ...i, unit_price: parseFloat(i.unit_price) })),
    };
    res.json(order);
  } catch (err) {
    console.error('Error getting order:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /orders/{id}:
 *   put:
 *     summary: Update order status
 *     tags: [Orders]
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
 *                 enum: [placed, confirmed, preparing, ready, picked_up, delivered, cancelled]
 *               notes:
 *                 type: string
 *     responses:
 *       200:
 *         description: Order updated
 *       400:
 *         description: Invalid status transition
 *       404:
 *         description: Order not found
 */
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body || {};

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ message: 'No data provided' });
    }

    const current = await query('SELECT * FROM orders WHERE id = $1', [id]);
    if (current.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }
    const order = current.rows[0];

    if (data.status) {
      if (!VALID_STATUSES.includes(data.status)) {
        return res.status(400).json({ message: `Invalid status. Must be one of: ${VALID_STATUSES.join(', ')}` });
      }

      const allowed = VALID_TRANSITIONS[order.status];
      if (!allowed.includes(data.status)) {
        return res.status(400).json({
          message: `Cannot transition from '${order.status}' to '${data.status}'. Allowed: ${allowed.join(', ') || 'none (terminal state)'}`,
        });
      }
    }

    const allowedFields = ['status', 'notes'];
    const setClauses = [];
    const values = [];
    let paramIndex = 1;

    for (const key of allowedFields) {
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
      `UPDATE orders SET ${setClauses.join(', ')} WHERE id = $${paramIndex} RETURNING *`,
      values
    );

    const items = await query('SELECT * FROM order_items WHERE order_id = $1', [id]);
    res.json({
      ...result.rows[0],
      total_amount: parseFloat(result.rows[0].total_amount),
      items: items.rows.map(i => ({ ...i, unit_price: parseFloat(i.unit_price) })),
    });
  } catch (err) {
    console.error('Error updating order:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /orders/{id}:
 *   delete:
 *     summary: Cancel order (only if placed or confirmed)
 *     tags: [Orders]
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
 *         description: Order cancelled
 *       400:
 *         description: Cannot cancel at current status
 *       404:
 *         description: Order not found
 */
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const result = await query('SELECT * FROM orders WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }

    const order = result.rows[0];
    if (!CANCELLABLE_STATUSES.includes(order.status)) {
      return res.status(400).json({
        message: `Cannot cancel order with status '${order.status}'. Only 'placed' or 'confirmed' orders can be cancelled`,
      });
    }

    const updated = await query(
      "UPDATE orders SET status = 'cancelled', updated_at = NOW() WHERE id = $1 RETURNING *",
      [id]
    );

    res.json({ ...updated.rows[0], total_amount: parseFloat(updated.rows[0].total_amount) });
  } catch (err) {
    console.error('Error cancelling order:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

/**
 * @swagger
 * /orders/{id}/items:
 *   get:
 *     summary: Get items for a specific order
 *     tags: [Orders]
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
 *         description: List of order items
 *       404:
 *         description: Order not found
 */
router.get('/:id/items', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const order = await query('SELECT id FROM orders WHERE id = $1', [id]);
    if (order.rows.length === 0) {
      return res.status(404).json({ message: 'Order not found' });
    }

    const items = await query('SELECT * FROM order_items WHERE order_id = $1', [id]);
    res.json(items.rows.map(i => ({ ...i, unit_price: parseFloat(i.unit_price) })));
  } catch (err) {
    console.error('Error getting order items:', err);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
