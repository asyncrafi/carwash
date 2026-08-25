"""
Seed data utility for populating initial database with services, vehicle types, and engine types.
"""
from decimal import Decimal
from apps.services.models import VehicleType, EngineType, Service, DirtLevel, PlatformConfig


def seed_all_data():
    """
    Populate the database with initial seed data for the car wash booking system.
    Handles conditional data based on vehicle type and engine type.
    """
    result = {
        'vehicle_types': seed_vehicle_types(),
        'engine_types': seed_engine_types(),
        'dirt_levels': seed_dirt_levels(),
        'services': seed_services(),
        'platform_config': seed_platform_config(),
        'app_settings': seed_app_settings(),
    }
    return result


def seed_vehicle_types():
    """Seed vehicle types with appropriate pricing."""
    vehicle_types_data = [
        {'name': 'Sedan', 'extra_price': Decimal('0.00'), 'order': 1},
        {'name': 'SUV', 'extra_price': Decimal('39.00'), 'order': 2},
        {'name': 'Truck', 'extra_price': Decimal('39.00'), 'order': 3},
        {'name': 'Bike', 'extra_price': Decimal('39.00'), 'order': 4},
    ]

    created_count = 0
    for vt_data in vehicle_types_data:
        vt, created = VehicleType.objects.get_or_create(
            name=vt_data['name'],
            defaults={
                'extra_price': vt_data['extra_price'],
                'is_active': True
            }
        )
        if created:
            created_count += 1

    return {
        'created': created_count,
        'total': len(vehicle_types_data),
        'message': f'Vehicle types: {created_count} created'
    }


def seed_engine_types():
    """Seed engine types with discount percentages."""
    engine_types_data = [
        {
            'engine_type': EngineType.ENGINE_ELECTRIC,
            'discount_percent': Decimal('5.00'),
            'description': 'Electric vehicles benefit from a 5% discount on all formulas'
        },
        {
            'engine_type': EngineType.ENGINE_PETROL,
            'discount_percent': Decimal('0.00'),
            'description': 'Standard rates for petrol and diesel vehicles'
        }
    ]

    created_count = 0
    for et_data in engine_types_data:
        et, created = EngineType.objects.get_or_create(
            engine_type=et_data['engine_type'],
            defaults={
                'discount_percent': et_data['discount_percent'],
                'description': et_data['description']
            }
        )
        if created:
            created_count += 1

    return {
        'created': created_count,
        'total': len(engine_types_data),
        'message': f'Engine types: {created_count} created'
    }


def seed_dirt_levels():
    """Seed dirt/dirtiness levels with descriptions and pricing."""
    dirt_levels_data = [
        {
            'level': DirtLevel.LEVEL_LIGHT,
            'description': 'Surface dust, recent wash',
            'extra_price': Decimal('0.00'),
        },
        {
            'level': DirtLevel.LEVEL_MEDIUM,
            'description': 'Mud splashes, week-old dirt',
            'extra_price': Decimal('0.00'),
        },
        {
            'level': DirtLevel.LEVEL_HEAVY,
            'description': 'Caked mud, off-road level',
            'extra_price': Decimal('0.00'),
        }
    ]

    created_count = 0
    for dl_data in dirt_levels_data:
        dl, created = DirtLevel.objects.get_or_create(
            level=dl_data['level'],
            defaults={
                'description': dl_data['description'],
                'extra_price': dl_data['extra_price']
            }
        )
        if created:
            created_count += 1

    return {
        'created': created_count,
        'total': len(dirt_levels_data),
        'message': f'Dirt levels: {created_count} created'
    }


def seed_services():
    """
    Seed services based on engine type.
    
    Petrol/Diesel Services:
    - Express Wash (€39)
    - Premium Wash (€39)
    - VIP Wash (€39)
    
    Electric Vehicle Services:
    - Express Charge (€35.50, with 5% discount)
    - Comfort Load (€35.50, with 5% discount)
    - Premium Charge (€35.50, with 5% discount)
    """
    petrol_engine = EngineType.objects.get(engine_type=EngineType.ENGINE_PETROL)
    electric_engine = EngineType.objects.get(engine_type=EngineType.ENGINE_ELECTRIC)

    # Petrol/Diesel services
    petrol_services_data = [
        {
            'name': 'Express Wash',
            'description': 'Complete Exterior - Quick exterior wash with all essentials',
            'base_price': Decimal('39.00'),
            'engine_type': petrol_engine,
            'order': 1
        },
        {
            'name': 'Premium Wash',
            'description': 'Complete Exterior - Premium exterior wash with extra care',
            'base_price': Decimal('39.00'),
            'engine_type': petrol_engine,
            'order': 2
        },
        {
            'name': 'VIP Wash',
            'description': 'Complete Exterior - VIP treatment with premium products',
            'base_price': Decimal('39.00'),
            'engine_type': petrol_engine,
            'order': 3
        }
    ]

    # Electric vehicle services
    electric_services_data = [
        {
            'name': 'Express Charge',
            'description': 'Electric vehicle specialized wash - Bodywork, Windows or Glass, Rims or Wheels, Drying',
            'base_price': Decimal('35.50'),
            'engine_type': electric_engine,
            'order': 1
        },
        {
            'name': 'Comfort Load',
            'description': 'Comfortable electric vehicle wash - Bodywork, Windows or Glass, Rims or Wheels, Drying',
            'base_price': Decimal('35.50'),
            'engine_type': electric_engine,
            'order': 2
        },
        {
            'name': 'Premium Charge',
            'description': 'Premium electric vehicle wash - Bodywork, Windows or Glass, Rims or Wheels, Drying',
            'base_price': Decimal('35.50'),
            'engine_type': electric_engine,
            'order': 3
        }
    ]

    created_count = 0

    # Create petrol services
    for service_data in petrol_services_data:
        service, created = Service.objects.get_or_create(
            name=service_data['name'],
            engine_type=service_data['engine_type'],
            defaults={
                'description': service_data['description'],
                'base_price': service_data['base_price'],
                'order': service_data['order'],
                'is_active': True
            }
        )
        if created:
            created_count += 1

    # Create electric services
    for service_data in electric_services_data:
        service, created = Service.objects.get_or_create(
            name=service_data['name'],
            engine_type=service_data['engine_type'],
            defaults={
                'description': service_data['description'],
                'base_price': service_data['base_price'],
                'order': service_data['order'],
                'is_active': True
            }
        )
        if created:
            created_count += 1

    return {
        'created': created_count,
        'total': len(petrol_services_data) + len(electric_services_data),
        'message': f'Services: {created_count} created (Petrol: {len(petrol_services_data)}, Electric: {len(electric_services_data)})'
    }


def seed_platform_config():
    """Seed platform configuration with default values."""
    config_data = {
        'platform_fee_fixed': Decimal('10.00'),
        'commission_percent': Decimal('15.00'),
        'distance_price_per_km': Decimal('3.00'),
    }

    config, created = PlatformConfig.objects.get_or_create(
        pk=1,
        defaults=config_data
    )

    return {
        'created': 1 if created else 0,
        'total': 1,
        'message': f'Platform config: {"created" if created else "already exists"}'
    }


def seed_app_settings():
    """Seed default global app settings (Privacy Policy, Terms, About Us, FAQ)."""
    from apps.services.models import AppSetting

    settings_data = [
        {
            'settings_type': 'privacy',
            'content': """<h2>Privacy Policy</h2>
<p>At Rince Carwash, we are committed to protecting your privacy. This policy outlines how we collect, use, and safeguard your personal information when using our mobile application and website.</p>
<h3>1. Information We Collect</h3>
<p>We collect information such as your name, phone number, email address, vehicle details, location data, and payment information necessary to facilitate bookings.</p>
<h3>2. How We Use Information</h3>
<p>Your data is used solely to process car wash requests, dispatch providers, process secure payments, and provide customer support.</p>
<h3>3. Security</h3>
<p>We implement industry-standard encryption and security measures to protect your personal information.</p>""",
        },
        {
            'settings_type': 'terms',
            'content': """<h2>Terms & Conditions</h2>
<p>Welcome to Rince Carwash. By accessing or using our platform, you agree to be bound by these Terms and Conditions.</p>
<h3>1. Services</h3>
<p>Rince provides an on-demand mobile car wash booking platform connecting customers with professional service providers.</p>
<h3>2. Payments & Cancellations</h3>
<p>Payments are processed securely via Stripe. Cancellations made prior to provider dispatch are eligible for a full refund according to our cancellation policy.</p>
<h3>3. User Conduct</h3>
<p>Users must provide accurate vehicle location and ensure a safe working environment for service providers.</p>""",
        },
        {
            'settings_type': 'about_us',
            'content': """<h2>About Rince Carwash</h2>
<p>Rince is your premier on-demand car wash service, bringing professional detailing directly to your doorstep. We combine eco-friendly wash techniques with high-efficiency scheduling to keep your vehicle spotless anywhere, anytime.</p>""",
        },
        {
            'settings_type': 'faq',
            'content': """<h2>Frequently Asked Questions</h2>
<h3>How does on-demand car washing work?</h3>
<p>Simply select your vehicle type, choose a wash package, set your location, and request a wash. An available nearby provider will accept and arrive at your location.</p>
<h3>Do I need to be present during the wash?</h3>
<p>For exterior washes, you don't need to be present as long as the vehicle is accessible. For interior detailing, access to the vehicle is required.</p>
<h3>What payment methods are supported?</h3>
<p>We support all major credit/debit cards, Apple Pay, and Google Pay through Stripe secure checkout.</p>""",
        },
    ]

    created_count = 0
    for s_data in settings_data:
        setting, created = AppSetting.objects.get_or_create(
            user=None,
            settings_type=s_data['settings_type'],
            defaults={'content': s_data['content']}
        )
        if created:
            created_count += 1

    return {
        'created': created_count,
        'total': len(settings_data),
        'message': f'App settings: {created_count} created'
    }

