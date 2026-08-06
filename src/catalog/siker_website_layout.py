"""
Канонічна ієрархія каталогу як на siker.ua (меню сайту), а не YML parentId.

YML partner-експорт кладе Крісла / Будівництво / дитячі / SUP під «Дім і сад».
На сайті siker.ua це окремі корені або інші гілки — цей модуль вирівнює дерево.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from slugify import slugify

from src.catalog.models import Category

# Синтетичні id (не з YML) — не деактивувати як stale.
OYRA_EXT_PREFIX = 'oyra:'

EXT_DIM = '23326795'
EXT_SPORT = '23326791'
EXT_VALIZY = '23326811'
EXT_KRISLA = '23326849'
EXT_BUDIV = '23326861'
EXT_ZOO = '23326935'
EXT_SALE = '23326939'

EXT_DYTYACHI_ROOT = f'{OYRA_EXT_PREFIX}dytyachi-tovary'

# Підкатегорії «Дім і сад», які мають стати окремими коренями.
PROMOTE_TO_ROOT = frozenset({EXT_KRISLA, EXT_BUDIV})

# external_id → батьківський external_id (після промоуту коренів).
REPARENT_TO: dict[str, str] = {
    # Дитячі товари
    '23326876': EXT_DYTYACHI_ROOT,  # Дитячі електромобілі
    '23326926': EXT_DYTYACHI_ROOT,  # Дитячі килимки
    '23326928': EXT_DYTYACHI_ROOT,  # Дитячі кухні
    '23326911': EXT_DYTYACHI_ROOT,  # Дитячі парти
    '23326951': EXT_DYTYACHI_ROOT,  # Дитячі спортивні комплекси
    '23326927': EXT_DYTYACHI_ROOT,  # Дитячі стільці
    # Спорт
    '23326949': EXT_SPORT,  # SUP-дошка для плавання
    '23326952': EXT_SPORT,  # Самокати
    # Будівництво
    '23326860': EXT_BUDIV,  # Візки
    '23326910': EXT_BUDIV,  # Складські рокли
}

# Перейменування підписів під меню siker.ua
RENAME_BY_EXT: dict[str, str] = {
    EXT_VALIZY: 'Дорожні валізи',
    '23326847': 'Садові гойдалки',
    '23326950': 'Садові павільйони, альтанки',
    '23326864': 'Металеві стелажі',
    '23326860': 'Складські візки',
    '23326949': 'Sup-дошки',
    '23326951': 'Дитячі ігрові комплекси та гойдалки',
}

# Порядок коренів у меню (як на siker.ua; трактори/СТО ховаються окремо).
ROOT_SORT: dict[str, int] = {
    EXT_DIM: 10,
    EXT_VALIZY: 20,
    EXT_KRISLA: 30,
    EXT_BUDIV: 40,
    EXT_DYTYACHI_ROOT: 50,
    EXT_SPORT: 60,
    EXT_ZOO: 80,
    EXT_SALE: 90,
}

# Featured sort усередині кореня (менші = вище в дропдауні, slice :4).
FEATURED_CHILD_SORT: dict[str, dict[str, int]] = {
    EXT_DIM: {
        'Складані меблі': 10,
        'Садові гойдалки': 20,
        'Садові павільйони, альтанки': 30,
        'Вуличні меблі': 40,
        'Шезлонги': 50,
        'Меблі для дому': 60,
        'Садові та пляжні парасольки': 70,
        'Теплиці': 80,
        'Агротканина': 90,
    },
    EXT_VALIZY: {
        'Комплекти валіз': 10,
        'Тканинні валізи': 20,
        'Пластикові валізи': 30,
    },
    EXT_KRISLA: {
        'Офісні крісла': 10,
        'Барні стільці хокери': 20,
        'Барні стільці': 20,
        'Геймерські крісла': 30,
        'Обідні крісла': 40,
        'Стільці для кухні': 40,
    },
    EXT_BUDIV: {
        'Металеві стелажі': 10,
        'Стелажі': 10,
        'Складські візки': 20,
        'Візки': 20,
        'Плитка керамогранітна': 30,
        'Вантажне обладнання': 40,
        'Складські рокли': 50,
    },
    EXT_DYTYACHI_ROOT: {
        'Дитячі електромобілі': 10,
        'Дитячі ігрові комплекси та гойдалки': 20,
        'Дитячі електроквадроцикли': 30,
        'Дитячі електромотоцикли': 40,
        'Дитячі стільці': 50,
        'Дитячі парти': 60,
        'Дитячі килимки': 70,
        'Дитячі кухні': 80,
    },
    EXT_SPORT: {
        'Батути': 10,
        'Бігові доріжки': 20,
        'Sup-дошки': 30,
        'SUP-дошка для плавання': 30,
        'Велотренажери та орбітреки': 40,
        'Самокати': 50,
    },
    EXT_SALE: {
        'Кухонні дошки': 10,
        'Складані меблі': 20,
        'Степери': 30,
        'Складські візки': 40,
    },
}

# Синтетичні підкатегорії для меню (якщо немає в YML).
SYNTHETIC_CHILDREN: dict[str, list[tuple[str, str, int]]] = {
    EXT_DIM: [
        (f'{OYRA_EXT_PREFIX}skladani-mebli', 'Складані меблі', 10),
        (f'{OYRA_EXT_PREFIX}vulychni-mebli', 'Вуличні меблі', 40),
    ],
    EXT_DYTYACHI_ROOT: [
        (f'{OYRA_EXT_PREFIX}elektrokvadrocycles', 'Дитячі електроквадроцикли', 30),
        (f'{OYRA_EXT_PREFIX}elektromotocycles', 'Дитячі електромотоцикли', 40),
    ],
    EXT_BUDIV: [
        (f'{OYRA_EXT_PREFIX}vantazhne', 'Вантажне обладнання', 40),
    ],
}


@dataclass
class LayoutStats:
    roots_ensured: int = 0
    reparented: int = 0
    renamed: int = 0
    sorted: int = 0
    synthetics: int = 0


def is_oyra_external_id(external_id: str) -> bool:
    return (external_id or '').startswith(OYRA_EXT_PREFIX)


def _unique_slug(base: str, exclude_pk: int | None = None) -> str:
    slug = (base or 'category')[:200]
    candidate = slug
    n = 1
    while True:
        qs = Category.objects.filter(slug=candidate)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return candidate
        n += 1
        suffix = f'-{n}'
        candidate = f'{slug[: 220 - len(suffix)]}{suffix}'


def _get_by_ext(external_id: str) -> Category | None:
    return Category.objects.filter(external_id=external_id).first()


def _ensure_root(
    *,
    external_id: str,
    name: str,
    slug_base: str,
    icon_key: str,
    color: str,
    sort_order: int,
) -> tuple[Category, bool]:
    cat = _get_by_ext(external_id)
    created = False
    if cat is None:
        cat = Category.objects.filter(name=name, parent__isnull=True).first()
    if cat is None:
        cat = Category(
            name=name,
            slug=_unique_slug(slugify(slug_base) or slug_base),
            external_id=external_id,
            parent=None,
            icon_key=icon_key,
            color=color,
            sort_order=sort_order,
            is_active=True,
        )
        created = True
    else:
        cat.name = name
        cat.external_id = external_id
        cat.parent = None
        cat.is_active = True
        cat.sort_order = sort_order
        if icon_key:
            cat.icon_key = icon_key
        if color:
            cat.color = color
    cat.save()
    return cat, created


def _ensure_child(
    *,
    external_id: str,
    name: str,
    parent: Category,
    sort_order: int,
    icon_key: str = 'grid',
) -> tuple[Category, bool]:
    cat = _get_by_ext(external_id)
    created = False
    if cat is None:
        # можливо є неактивний seed з тим самим ім'ям
        cat = Category.objects.filter(
            name=name, parent=parent, external_id='',
        ).first()
    if cat is None:
        cat = Category(
            name=name,
            slug=_unique_slug(f'{slugify(name)}-{external_id.split(":")[-1]}'),
            external_id=external_id,
            parent=parent,
            icon_key=icon_key,
            color=parent.color,
            sort_order=sort_order,
            is_active=True,
        )
        created = True
    else:
        cat.name = name
        cat.external_id = external_id
        cat.parent = parent
        cat.is_active = True
        cat.sort_order = sort_order
    cat.save()
    return cat, created


def _apply_renames() -> int:
    updated = 0
    for ext_id, new_name in RENAME_BY_EXT.items():
        cat = _get_by_ext(ext_id)
        if cat and cat.name != new_name:
            cat.name = new_name
            cat.save(update_fields=['name'])
            updated += 1
    return updated


def _apply_reparents(by_ext: dict[str, Category]) -> int:
    updated = 0
    for child_ext, parent_ext in REPARENT_TO.items():
        child = by_ext.get(child_ext) or _get_by_ext(child_ext)
        parent = by_ext.get(parent_ext) or _get_by_ext(parent_ext)
        if not child or not parent:
            continue
        if child.parent_id != parent.pk:
            child.parent = parent
            child.is_active = True
            child.save(update_fields=['parent', 'is_active'])
            updated += 1
            by_ext[child_ext] = child
    return updated


def _promote_roots(by_ext: dict[str, Category]) -> int:
    updated = 0
    for ext_id in PROMOTE_TO_ROOT:
        cat = by_ext.get(ext_id) or _get_by_ext(ext_id)
        if not cat:
            continue
        sort = ROOT_SORT.get(ext_id, cat.sort_order)
        fields: list[str] = []
        if cat.parent_id is not None:
            cat.parent = None
            fields.append('parent')
        if not cat.is_active:
            cat.is_active = True
            fields.append('is_active')
        if cat.sort_order != sort:
            cat.sort_order = sort
            fields.append('sort_order')
        if ext_id == EXT_KRISLA and cat.icon_key != 'chair':
            cat.icon_key = 'chair'
            fields.append('icon_key')
        if ext_id == EXT_BUDIV and cat.icon_key != 'tools':
            cat.icon_key = 'tools'
            fields.append('icon_key')
        if fields:
            cat.save(update_fields=fields)
            updated += 1
        by_ext[ext_id] = cat
    return updated


def _apply_featured_sort() -> int:
    updated = 0
    for parent_ext, name_to_sort in FEATURED_CHILD_SORT.items():
        parent = _get_by_ext(parent_ext)
        if not parent:
            continue
        for child in parent.children.all():
            target = name_to_sort.get(child.name)
            if target is None:
                # неfeatured — нижче featured-блоку
                if child.sort_order < 100:
                    child.sort_order = 100 + (child.pk % 50)
                    child.save(update_fields=['sort_order'])
                    updated += 1
                continue
            if child.sort_order != target:
                child.sort_order = target
                child.save(update_fields=['sort_order'])
                updated += 1
    return updated


def _deactivate_empty_named() -> int:
    return Category.objects.filter(name='', is_active=True).update(is_active=False)


def _move_name_prefix_to_dytyachi(dytyachi: Category) -> int:
    """Страховка: будь-які активні «Дитячі *» під Дім і сад → Дитячі товари."""
    dim = _get_by_ext(EXT_DIM)
    if not dim:
        return 0
    updated = 0
    qs = Category.objects.filter(
        parent=dim, is_active=True, name__istartswith='Дитяч',
    ).exclude(pk=dytyachi.pk)
    for cat in qs:
        cat.parent = dytyachi
        cat.save(update_fields=['parent'])
        updated += 1
    return updated


@transaction.atomic
def apply_siker_website_layout(
    by_ext: dict[str, Category] | None = None,
) -> LayoutStats:
    """Вирівнює дерево під меню siker.ua. Товари лишаються на leaf-категоріях."""
    stats = LayoutStats()
    by_ext = dict(by_ext or {})
    for cat in Category.objects.exclude(external_id=''):
        by_ext.setdefault(cat.external_id, cat)

    # 1) Синтетичний корінь «Дитячі товари»
    dytyachi, created = _ensure_root(
        external_id=EXT_DYTYACHI_ROOT,
        name='Дитячі товари',
        slug_base='dytyachi-tovary',
        icon_key='kids',
        color='#E8A838',
        sort_order=ROOT_SORT[EXT_DYTYACHI_ROOT],
    )
    by_ext[EXT_DYTYACHI_ROOT] = dytyachi
    if created:
        stats.roots_ensured += 1
        stats.synthetics += 1
    else:
        stats.roots_ensured += 1

    # 2) Промоут Крісла / Будівництво + сортування відомих коренів
    stats.reparented += _promote_roots(by_ext)
    for ext_id, sort in ROOT_SORT.items():
        cat = by_ext.get(ext_id) or _get_by_ext(ext_id)
        if not cat:
            continue
        changed = False
        if cat.sort_order != sort:
            cat.sort_order = sort
            changed = True
        if ext_id == EXT_VALIZY and cat.name != 'Дорожні валізи':
            cat.name = 'Дорожні валізи'
            changed = True
        if cat.parent_id is not None and ext_id in (
            EXT_DIM, EXT_VALIZY, EXT_SPORT, EXT_ZOO, EXT_SALE, EXT_DYTYACHI_ROOT,
        ):
            cat.parent = None
            changed = True
        if not cat.is_active:
            cat.is_active = True
            changed = True
        if changed:
            cat.save()
            stats.sorted += 1
        by_ext[ext_id] = cat

    # 3) Перейменування підписів
    stats.renamed += _apply_renames()

    # 4) Перепривʼязка підкатегорій
    stats.reparented += _apply_reparents(by_ext)
    stats.reparented += _move_name_prefix_to_dytyachi(dytyachi)

    # 5) Синтетичні підкатегорії для меню
    for parent_ext, children in SYNTHETIC_CHILDREN.items():
        parent = by_ext.get(parent_ext) or _get_by_ext(parent_ext)
        if not parent:
            continue
        for child_ext, child_name, child_sort in children:
            existing = _get_by_ext(child_ext)
            # якщо вже є категорія з такою назвою під цим батьком — не дублюємо
            named = parent.children.filter(name=child_name).exclude(
                external_id=child_ext,
            ).first()
            if named and not existing:
                named.external_id = child_ext
                named.sort_order = child_sort
                named.is_active = True
                named.save(update_fields=['external_id', 'sort_order', 'is_active'])
                stats.synthetics += 1
                continue
            _, created = _ensure_child(
                external_id=child_ext,
                name=child_name,
                parent=parent,
                sort_order=child_sort,
                icon_key=parent.icon_key or 'grid',
            )
            if created:
                stats.synthetics += 1

    # 6) Featured sort + порожні назви
    stats.sorted += _apply_featured_sort()
    _deactivate_empty_named()
    return stats
