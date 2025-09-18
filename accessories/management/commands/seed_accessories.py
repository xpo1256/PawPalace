from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.conf import settings
from pathlib import Path
from decimal import Decimal
import requests

from accessories.models import Accessory, AccessoryCategory


class Command(BaseCommand):
    help = "Seed the database with mock accessories and categories."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=24, help='Number of accessories to create')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # Ensure a demo seller exists
        seller, created = User.objects.get_or_create(
            username='demo_seller',
            defaults={
                'email': 'seller@example.com',
                'role': 'seller',
            }
        )
        if created:
            seller.set_password('password123')
            seller.save()

        # Ensure base categories
        category_names = [
            ('Food & Treats', 'food', 'fas fa-bone'),
            ('Toys & Play', 'toys', 'fas fa-basketball-ball'),
            ('Health & Grooming', 'health', 'fas fa-syringe'),
            ('Safety & Training', 'safety', 'fas fa-shield-dog'),
            ('Bedding & Comfort', 'bedding', 'fas fa-bed'),
            ('Clothing & Accessories', 'clothing', 'fas fa-shirt'),
            ('Travel & Outdoor', 'travel', 'fas fa-car'),
            ('Other', 'other', 'fas fa-paw'),
        ]

        name_to_category = {}
        for label, code, icon in category_names:
            cat, _ = AccessoryCategory.objects.get_or_create(name=label, defaults={'description': label, 'icon': icon})
            name_to_category[code] = cat

        items = [
            {
                'name': 'Premium Dog Kibble', 'category': 'food', 'price': Decimal('29.99'),
                'brand': 'Pawfect', 'description': 'High-protein kibble for active dogs.',
                'image_url': 'https://images.unsplash.com/photo-1546443046-ed1ce6ffd1dc'
            },
            {
                'name': 'Rubber Chew Toy', 'category': 'toys', 'price': Decimal('12.50'),
                'brand': 'ChewMaster', 'description': 'Durable chew toy for aggressive chewers.',
                'image_url': 'https://images.unsplash.com/photo-1543466835-00a7907e9de1'
            },
            {
                'name': 'Grooming Brush', 'category': 'health', 'price': Decimal('15.00'),
                'brand': 'FurCare', 'description': 'Removes loose hair and reduces shedding.',
                'image_url': 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4'
            },
            {
                'name': 'Reflective Harness', 'category': 'safety', 'price': Decimal('24.99'),
                'brand': 'SafePaws', 'description': 'Comfortable harness with reflective straps.',
                'image_url': 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b'
            },
            {
                'name': 'Plush Dog Bed', 'category': 'bedding', 'price': Decimal('49.99'),
                'brand': 'CozyNest', 'description': 'Ultra-soft bed for restful sleep.',
                'image_url': 'https://images.unsplash.com/photo-1508672019048-805c876b67e2'
            },
            {
                'name': 'Raincoat', 'category': 'clothing', 'price': Decimal('19.99'),
                'brand': 'PuddlePup', 'description': 'Waterproof coat to keep your dog dry.',
                'image_url': 'https://images.unsplash.com/photo-1518717758536-85ae29035b6d'
            },
            {
                'name': 'Floral Dog Dress', 'category': 'clothing', 'price': Decimal('22.99'),
                'brand': 'PawCouture', 'description': 'Cute floral dress for special occasions.',
                'image_url': 'https://images.unsplash.com/photo-1525253086316-d0c936c814f8'
            },
            {
                'name': 'Tuxedo Outfit', 'category': 'clothing', 'price': Decimal('27.99'),
                'brand': 'PawCouture', 'description': 'Formal tuxedo outfit for dogs.',
                'image_url': 'https://images.unsplash.com/photo-1543466835-00a7907e9de1'
            },
            {
                'name': 'Winter Sweater', 'category': 'clothing', 'price': Decimal('18.99'),
                'brand': 'CozyTail', 'description': 'Warm knit sweater for chilly walks.',
                'image_url': 'https://images.unsplash.com/photo-1521302200778-33500795e128'
            },
            {
                'name': 'Travel Water Bottle', 'category': 'travel', 'price': Decimal('16.99'),
                'brand': 'HydraPaws', 'description': 'Portable bottle with built-in bowl.',
                'image_url': 'https://images.unsplash.com/photo-1541123603104-512919d6a96c'
            },
            {
                'name': 'Dental Chews', 'category': 'food', 'price': Decimal('9.99'),
                'brand': 'FreshBite', 'description': 'Helps reduce tartar and freshen breath.',
                'image_url': 'https://images.unsplash.com/photo-1568640347023-a616a30bc3bd'
            },
            {
                'name': 'Squeaky Ball', 'category': 'toys', 'price': Decimal('8.99'),
                'brand': 'PlayMore', 'description': 'Brightly colored ball with squeaker.',
                'image_url': 'https://images.unsplash.com/photo-1525253013412-55c1a69a5738'
            },
            {
                'name': 'Nail Clippers', 'category': 'health', 'price': Decimal('11.99'),
                'brand': 'TrimPro', 'description': 'Sharp clippers with safety guard.',
                'image_url': 'https://images.unsplash.com/photo-1490718720478-364a07a997cd'
            },
            {
                'name': 'LED Collar', 'category': 'safety', 'price': Decimal('13.99'),
                'brand': 'GlowPaw', 'description': 'USB-rechargeable LED collar for night walks.',
                'image_url': 'https://images.unsplash.com/photo-1507149833265-60c372daea22'
            },
            {
                'name': 'Orthopedic Pillow', 'category': 'bedding', 'price': Decimal('34.99'),
                'brand': 'RestEase', 'description': 'Supports joints for senior dogs.',
                'image_url': 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1'
            },
        ]

        # Expand items up to count by cloning with suffix
        if options['count'] > len(items):
            base = list(items)
            i = 1
            while len(items) < options['count']:
                for it in base:
                    clone = dict(it)
                    clone['name'] = f"{it['name']} #{i}"
                    items.append(clone)
                    if len(items) >= options['count']:
                        break
                i += 1

        created_count = 0
        for data in items[: options['count']]:
            if Accessory.objects.filter(name=data['name'], seller=seller).exists():
                continue

            accessory = Accessory(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                category=data['category'],
                accessory_category=name_to_category.get(data['category']),
                brand=data.get('brand'),
                seller=seller,
                is_available=True,
                quantity=10,
            )

            # Prefer local media first
            local_media_dir = Path(settings.MEDIA_ROOT) / 'accessories'
            local_candidates = [
                f"{data['name'].lower().replace(' ', '_')}.jpg",
                f"{data['name'].lower().replace(' ', '')}.jpg",
            ]
            used_local = False
            for fname in local_candidates:
                fpath = local_media_dir / fname
                if fpath.exists() and fpath.stat().st_size > 0:
                    with open(fpath, 'rb') as fh:
                        accessory.image.save(fname, ContentFile(fh.read()), save=False)
                    used_local = True
                    break
            if not used_local:
                # Try to fetch image
                try:
                    resp = requests.get(data['image_url'] + '?auto=format&fit=crop&w=1200&q=80', timeout=15)
                    resp.raise_for_status()
                    file_name = f"{data['name'].lower().replace(' ', '_')}.jpg"
                    accessory.image.save(file_name, ContentFile(resp.content), save=False)
                except Exception:
                    # Use a local placeholder file if remote fetch fails
                    placeholder_path = Path(settings.MEDIA_ROOT) / 'accessories' / 'placeholder.jpg'
                    try:
                        with open(placeholder_path, 'rb') as ph:
                            accessory.image.save('placeholder.jpg', ContentFile(ph.read()), save=False)
                    except Exception:
                        accessory.image.save('placeholder.jpg', ContentFile(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'), save=False)

            accessory.save()
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} accessory(ies). Demo seller: demo_seller / password123"))


