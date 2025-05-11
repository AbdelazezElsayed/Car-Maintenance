// MongoDB initialization script
// This script will be executed when the MongoDB container is first created

// Connect to the admin database
db = db.getSiblingDB('admin');

// Create a user for the CAR database
db.createUser({
  user: 'carcare',
  pwd: 'carcare_password',
  roles: [
    { role: 'readWrite', db: 'CAR' }
  ]
});

// Switch to the CAR database
db = db.getSiblingDB('CAR');

// Create collections
db.createCollection('USER');
db.createCollection('VEHICLE');
db.createCollection('MAINTENANCE');
db.createCollection('TIRE_ANALYSIS');

// Create indexes for better performance
db.USER.createIndex({ "email": 1 }, { unique: true });
db.VEHICLE.createIndex({ "owner_email": 1 });
db.MAINTENANCE.createIndex({ "vehicle_id": 1 });
db.TIRE_ANALYSIS.createIndex({ "vehicle_id": 1 });
db.TIRE_ANALYSIS.createIndex({ "created_at": 1 });

// Print success message
print('MongoDB initialization completed successfully');
