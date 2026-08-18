# Seed Data API Documentation

## Overview
The Seed Data API populates your carwash booking system database with initial data including vehicle types, engine types, services/packages, dirt levels, and platform configuration.

The seed data follows the booking flow logic:
- **Vehicle Types**: Sedan, SUV, Truck, Bike
- **Engine Types**: Electric (with 5% discount), Petrol/Diesel (standard rates)
- **Services**:
  - **Petrol Services**: Express Wash, Premium Wash, VIP Wash (€39 each)
  - **Electric Services**: Express Charge, Comfort Load, Premium Charge (€35.50 each)
- **Dirt Levels**: Light (clean), Medium (week-old), Heavy (caked mud)
- **Platform Config**: Default fees and commission settings

---

## API Endpoint

### Seed Database
**Endpoint**: `GET /api/services/seed-data/`  
**Alternative**: `POST /api/services/seed-data/`  
**Permission**: AllowAny (Public)  
**Method**: GET or POST

#### Request
```bash
curl http://localhost:8000/api/services/seed-data/
```

#### Response
```json
{
  "success": true,
  "message": "Seed data populated successfully",
  "data": {
    "status": "success",
    "message": "Database seeded successfully",
    "created": {
      "vehicle_types": 4,
      "engine_types": 2,
      "dirt_levels": 3,
      "services": 6,
      "platform_config": 1
    },
    "total_created": 16,
    "details": {
      "vehicle_types": {
        "created": 4,
        "total": 4,
        "message": "Vehicle types: 4 created"
      },
      "engine_types": {
        "created": 2,
        "total": 2,
        "message": "Engine types: 2 created"
      },
      "dirt_levels": {
        "created": 3,
        "total": 3,
        "message": "Dirt levels: 3 created"
      },
      "services": {
        "created": 6,
        "total": 6,
        "message": "Services: 6 created (Petrol: 3, Electric: 3)"
      },
      "platform_config": {
        "created": 1,
        "total": 1,
        "message": "Platform config: created"
      }
    }
  }
}
```

---

## Management Command

You can also seed data using Django's management command:

```bash
python manage.py seed_database
```

Output:
```
🚀 Starting database seeding...

✅ Vehicle types: X created
✅ Engine types: X created
✅ Dirt levels: X created
✅ Services: X created (Petrol: 3, Electric: 3)
✅ Platform config: created

🎉 Database seeding completed! 16 total records created.
```

---

## Data Structure

### Vehicle Types
| Name | Extra Price | Order |
|------|------------|-------|
| Sedan | €0.00 | 1 |
| SUV | €39.00 | 2 |
| Truck | €39.00 | 3 |
| Bike | €39.00 | 4 |

### Engine Types
| Type | Discount | Description |
|------|----------|-------------|
| Electric | 5% | Benefit from 5% discount on all packages |
| Petrol/Diesel | 0% | Standard rates |

### Services (Petrol/Diesel)
| Name | Price | Description |
|------|-------|-------------|
| Express Wash | €39.00 | Complete Exterior - Quick wash |
| Premium Wash | €39.00 | Complete Exterior - Premium care |
| VIP Wash | €39.00 | Complete Exterior - VIP treatment |

### Services (Electric Vehicles)
| Name | Price | Features |
|------|-------|----------|
| Express Charge | €35.50 | Bodywork, Windows/Glass, Rims/Wheels, Drying |
| Comfort Load | €35.50 | Bodywork, Windows/Glass, Rims/Wheels, Drying |
| Premium Charge | €35.50 | Bodywork, Windows/Glass, Rims/Wheels, Drying |

### Dirt Levels
| Level | Description | Extra Price |
|-------|-------------|-------------|
| Light | Surface dust, recent wash | €0.00 |
| Medium | Mud splashes, week-old dirt | €0.00 |
| Heavy | Caked mud, off-road level | €0.00 |

### Platform Config
- Platform Fee (Fixed): €10.00
- Commission: 15%
- Distance Price per KM: €3.00

---

## Booking Flow with Seed Data

The seed data supports the complete booking flow:

### Step 1: Vehicle Type Selection
User selects from: Sedan, SUV, Truck, Bike
- Extra pricing adjusts based on vehicle type

### Step 2: Engine Type Selection
User selects: Electric Vehicle or Petrol/Diesel
- Electric vehicles get 5% discount on all packages

### Step 3: Service Selection
Available services depend on engine type:
- **Petrol**: Express/Premium/VIP Wash
- **Electric**: Express/Comfort/Premium Charge
- Base price already includes engine type discount

### Step 4: Dirt Level Assessment
User selects: Light, Medium, or Heavy
- Describes current vehicle cleanliness
- May affect service duration/availability

### Step 5: Quote Calculation
```
Total = Base Service Price 
        + Vehicle Type Extra Price
        - Engine Type Discount (if electric)
        + Dirt Level Extra Price
        + Distance Surcharge (if applicable)
        + Platform Fee
        + Commission
```

---

## Usage Examples

### Postman/Curl
```bash
# Seed the database
curl -X GET http://localhost:8000/api/services/seed-data/

# Alternative POST method
curl -X POST http://localhost:8000/api/services/seed-data/
```

### Django Shell
```python
from apps.services.seed_data import seed_all_data

result = seed_all_data()
print(result)
# Output: {'vehicle_types': {...}, 'engine_types': {...}, ...}
```

### Get Services by Engine Type
After seeding, retrieve services:
```bash
# Get all petrol services
curl http://localhost:8000/api/services/?engine_type=1

# Get all electric services
curl http://localhost:8000/api/services/?engine_type=2

# Get vehicle types
curl http://localhost:8000/api/services/vehicle-types/

# Get engine types
curl http://localhost:8000/api/services/engine-types/

# Get dirt levels
curl http://localhost:8000/api/services/dirt-levels/
```

---

## Idempotency

The seed data operation is **idempotent** - it can be run multiple times safely:
- Uses `get_or_create()` for all models
- Only creates records that don't exist
- Existing records are not modified
- Safe to run in development, staging, and production

---

## Notes

- Seed data is designed for the booking flow shown in the UI screenshots
- Pricing follows EUR (€) currency
- Electric vehicle discount applies to the service base price
- All created records are marked as `is_active=True`
- Platform config is singleton (pk=1) - only one record exists

---

## Files Created

1. **`apps/services/seed_data.py`** - Core seeding logic
2. **`apps/services/management/commands/seed_database.py`** - Django management command
3. **`apps/services/views.py`** - Updated with `SeedDataView`
4. **`apps/services/urls.py`** - Updated with seed endpoint

---

## Troubleshooting

### Command not found
```bash
# Make sure management/commands/__init__.py exists
# Verify the file structure:
# apps/services/management/__init__.py
# apps/services/management/commands/__init__.py
# apps/services/management/commands/seed_database.py
```

### API returns 404
```bash
# Verify URL is registered in apps/services/urls.py
# Check main urls.py includes the services app URLs
# Ensure format: path('api/services/', include('apps.services.urls'))
```

### Import errors
```bash
# Verify all models are properly imported in seed_data.py
# Run: python manage.py shell
# Then: from apps.services.seed_data import seed_all_data
```

---

## Support

For issues or questions about the seed data API, check:
1. Django logs for error messages
2. Database constraints (ensure models exist)
3. File permissions for management commands
