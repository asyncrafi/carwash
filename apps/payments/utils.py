import logging

from .models import ProviderEarning
from apps.core.utils import calculate_provider_earning

logger = logging.getLogger(__name__)


def create_provider_earning(booking):
    if not booking.provider:
        return
    if ProviderEarning.objects.filter(booking=booking).exists():
        return

    try:
        breakdown = calculate_provider_earning(booking)
        ProviderEarning.objects.create(
            provider=booking.provider,
            booking=booking,
            gross_amount=breakdown['gross_amount'],
            platform_fee=breakdown['platform_fee'],
            net_amount=breakdown['net_amount'],
        )
    except Exception as e:
        logger.error(
            f"Failed to create ProviderEarning for "
            f"Booking #{booking.id}: {e}"
        )
