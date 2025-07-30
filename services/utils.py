from uuid import uuid4
from pytils.translit import slugify


def unique_slugify(instance, slug, slug_field=None):
    model = instance.__class__

    if not slug_field:
        slug_field = slugify(slug)

    base_slug = slug_field

    while model.objects.filter(slug=slug_field).exclude(id=instance.id).exists():
        slug_field = f"{base_slug}-{uuid4().hex[:9]}"
    return slug_field
