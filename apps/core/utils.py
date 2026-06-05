from decimal import Decimal

from apps.services.models import PlatformConfig


def calculate_booking_price(service, vehicle, dirt_level, distance_km: float) -> dict:
    config = PlatformConfig.objects.first()

    service_price = Decimal(str(service.base_price)) if service else Decimal('0')
    vehicle_price = (
        Decimal(str(vehicle.vehicle_type.extra_price))
        if vehicle and vehicle.vehicle_type
        else Decimal('0')
    )
    dirt_price = Decimal(str(dirt_level.extra_price)) if dirt_level else Decimal('0')

    price_per_km = Decimal(str(config.distance_price_per_km)) if config else Decimal('3')
    distance_price = Decimal(str(distance_km)) * price_per_km

    engine_discount = Decimal('0')
    if vehicle and vehicle.engine_type:
        discount_pct = Decimal(str(vehicle.engine_type.discount_percent))
        subtotal_before = service_price + vehicle_price + dirt_price + distance_price
        engine_discount = (
            (subtotal_before * discount_pct / Decimal('100')).quantize(Decimal('0.01'))
        )

    platform_fee = Decimal(str(config.platform_fee_fixed)) if config else Decimal('10')

    total_amount = (
        service_price
        + vehicle_price
        + dirt_price
        + distance_price
        - engine_discount
        + platform_fee
    ).quantize(Decimal('0.01'))

    return {
        'service_price': service_price,
        'vehicle_price': vehicle_price,
        'dirt_price': dirt_price,
        'distance_price': distance_price.quantize(Decimal('0.01')),
        'engine_discount': engine_discount,
        'platform_fee': platform_fee,
        'total_amount': total_amount,
    }


def calculate_provider_earning(booking) -> dict:
    config = PlatformConfig.objects.first()
    commission_pct = Decimal(str(config.commission_percent)) if config else Decimal('15')

    gross_amount = Decimal(str(booking.total_amount))
    platform_fee = (gross_amount * commission_pct / Decimal('100')).quantize(Decimal('0.01'))
    net_amount = (gross_amount - platform_fee).quantize(Decimal('0.01'))

    return {
        'gross_amount': gross_amount,
        'platform_fee': platform_fee,
        'net_amount': net_amount,
    }
