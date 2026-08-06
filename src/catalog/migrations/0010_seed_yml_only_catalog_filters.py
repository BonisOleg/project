from django.db import migrations


def seed_yml_filters(apps, schema_editor):
    from src.catalog.filters import siker_catalog_filter_definitions

    CatalogFilter = apps.get_model('catalog', 'CatalogFilter')
    CatalogFilter.objects.all().delete()
    for item in siker_catalog_filter_definitions():
        CatalogFilter.objects.create(
            name=item.name,
            filter_type=item.filter_type,
            attribute_name=item.attribute_name,
            fallback_values=item.fallback_values,
            sort_order=item.sort_order,
            is_active=item.is_active,
            open_by_default=item.open_by_default,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_seed_siker_catalog_filters'),
    ]

    operations = [
        migrations.RunPython(seed_yml_filters, noop),
    ]
