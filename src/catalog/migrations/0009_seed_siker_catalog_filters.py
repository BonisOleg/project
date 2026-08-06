from django.db import migrations


def seed_siker_filters(apps, schema_editor):
    CatalogFilter = apps.get_model('catalog', 'CatalogFilter')
    from src.catalog.filters import siker_catalog_filter_definitions

    CatalogFilter.objects.all().delete()
    rows = []
    for item in siker_catalog_filter_definitions():
        rows.append(CatalogFilter(
            name=item.name,
            filter_type=item.filter_type,
            attribute_name=item.attribute_name,
            fallback_values=item.fallback_values,
            sort_order=item.sort_order,
            is_active=item.is_active,
            open_by_default=item.open_by_default,
        ))
    CatalogFilter.objects.bulk_create(rows)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_oyra_tz_features'),
    ]

    operations = [
        migrations.RunPython(seed_siker_filters, noop),
    ]
