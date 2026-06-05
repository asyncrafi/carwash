from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class VehicleType(models.Model):
    name = models.CharField(max_length=50)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class EngineType(models.Model):
    ENGINE_ELECTRIC = 'electric'
    ENGINE_PETROL = 'petrol'
    ENGINE_CHOICES = [
        (ENGINE_ELECTRIC, 'Electric Vehicle'),
        (ENGINE_PETROL, 'Petrol / Diesel'),
    ]

    engine_type = models.CharField(
        max_length=10, choices=ENGINE_CHOICES, unique=True
    )
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.get_engine_type_display()


class DirtLevel(models.Model):
    LEVEL_LIGHT = 'light'
    LEVEL_MEDIUM = 'medium'
    LEVEL_HEAVY = 'heavy'
    LEVEL_CHOICES = [
        (LEVEL_LIGHT, 'Light'),
        (LEVEL_MEDIUM, 'Medium'),
        (LEVEL_HEAVY, 'Heavy'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, unique=True)
    description = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    image = models.ImageField(upload_to='dirt_levels/', null=True, blank=True)

    def __str__(self):
        return self.get_level_display()


class PlatformConfig(models.Model):
    platform_fee_fixed = models.DecimalField(
        max_digits=8, decimal_places=2, default=10
    )
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=15
    )
    distance_price_per_km = models.DecimalField(
        max_digits=6, decimal_places=2, default=3
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform Config'

    def __str__(self):
        return "Platform Config"
