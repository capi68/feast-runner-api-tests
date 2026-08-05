const express = require('express');
const cors = require('cors');
const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');
const { initDb } = require('./utils/db');
const { seedData } = require('./utils/seed');

const restaurantRoutes = require('./routes/restaurants');
const menuRoutes = require('./routes/menus');
const menuItemRoutes = require('./routes/menu-items');
const customerRoutes = require('./routes/customers');
const addressRoutes = require('./routes/addresses');
const courierRoutes = require('./routes/couriers');
const orderRoutes = require('./routes/orders');
const deliveryRoutes = require('./routes/deliveries');
const ratingRoutes = require('./routes/ratings');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Swagger config
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'FeastRunner API',
      version: '1.0.0',
      description: 'Food Delivery Platform — Training Project. All endpoints except registration and login require a valid JWT token in the Authorization header (Bearer <token>).',
    },
    servers: [{ url: `http://localhost:${PORT}` }],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
    security: [{ bearerAuth: [] }],
  },
  apis: ['./src/routes/*.js'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Redirect root to docs
app.get('/', (req, res) => {
  res.redirect('/api-docs');
});

// Routes
app.use('/restaurants', restaurantRoutes);
app.use('/menus', menuRoutes);
app.use('/menu-items', menuItemRoutes);
app.use('/customers', customerRoutes);
app.use('/addresses', addressRoutes);
app.use('/couriers', courierRoutes);
app.use('/orders', orderRoutes);
app.use('/deliveries', deliveryRoutes);
app.use('/ratings', ratingRoutes);

// Global error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ message: 'Internal server error' });
});

// Initialize DB and start server
async function start() {
  try {
    await initDb();
    await seedData();
    app.listen(PORT, () => {
      console.log(`FeastRunner API running on port ${PORT}`);
      console.log(`Swagger docs: http://localhost:${PORT}/api-docs`);
    });
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

start();
