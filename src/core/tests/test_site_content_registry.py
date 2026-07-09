from django.test import SimpleTestCase

from src.core.site_content_registry import CONTENT_SECTIONS, all_registry_block_keys, iter_section_blocks


class SiteContentRegistryTests(SimpleTestCase):
    def test_block_keys_are_unique_per_page(self):
        keys = all_registry_block_keys()
        pages: dict[str, set[str]] = {}
        for page, key in keys:
            pages.setdefault(page, set()).add(key)
        for page, page_keys in pages.items():
            section_keys = [key for p, key in keys if p == page]
            self.assertEqual(len(section_keys), len(page_keys), f'Duplicate keys on page {page!r}')

    def test_each_section_has_visibility_key(self):
        for section in CONTENT_SECTIONS:
            self.assertTrue(section.visibility_key, section.slug)
            visibility_in_blocks = any(
                key == section.visibility_key
                for _page, key in iter_section_blocks(section)
            )
            self.assertTrue(visibility_in_blocks, section.slug)

    def test_admin_model_names_are_unique(self):
        names = [section.admin_model_name for section in CONTENT_SECTIONS]
        self.assertEqual(len(names), len(set(names)))
