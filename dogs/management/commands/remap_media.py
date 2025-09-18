from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

from dogs.models import Dog
from accessories.models import Accessory


class Command(BaseCommand):
    help = "Bulk remap existing Dog/Accessory images to local, subject-relevant files under MEDIA_ROOT."

    def handle(self, *args, **options):
        media = Path(settings.MEDIA_ROOT)

        dog_files = {p.stem.lower(): p for p in (media / 'dogs').glob('*.jpg')}
        acc_files = {p.stem.lower(): p for p in (media / 'accessories').glob('*.jpg')}

        def to_rel(p: Path) -> str:
            return str(p.relative_to(media)).replace('\\', '/')

        # Dogs mapping by first-name heuristic
        name_map = {
            'buddy': 'buddy', 'bella': 'bella', 'charlie': 'charlie', 'daisy': 'daisy',
            'lucy': 'lucy', 'luna': 'luna', 'max': 'buddy', 'cooper': 'luna'
        }

        fixed_d = 0
        for d in Dog.objects.all():
            key = (d.name or '').split(' ')[0].lower()
            stem = name_map.get(key, key)
            p = dog_files.get(stem)
            if not p:
                continue
            rel = to_rel(p)
            if not d.image or d.image.name != rel:
                d.image.name = rel
                d.save(update_fields=['image'])
                fixed_d += 1

        self.stdout.write(self.style.SUCCESS(f"Dogs remapped: {fixed_d}"))

        # Accessories mapping by keyword
        acc_keywords = [
            ('kibble', 'dental_chews'), ('chew toy', 'rubber_chew_toy'), ('grooming brush', 'grooming_brush'),
            ('harness', 'reflective_harness'), ('bed', 'plush_dog_bed'), ('raincoat', 'raincoat'),
            ('dress', 'floral_dog_dress'), ('tuxedo', 'tuxedo_outfit'), ('sweater', 'winter_sweater'),
            ('bottle', 'travel_water_bottle'), ('dental', 'dental_chews'), ('squeaky', 'squeaky_ball'),
            ('clippers', 'nail_clippers'), ('collar', 'led_collar'), ('pillow', 'orthopedic_pillow')
        ]

        fixed_a = 0
        for a in Accessory.objects.all():
            name = (a.name or '').lower()
            target = None
            for kw, stem in acc_keywords:
                if kw in name:
                    target = stem
                    break
            if not target:
                continue
            p = acc_files.get(target)
            if not p:
                continue
            rel = to_rel(p)
            if not a.image or a.image.name != rel:
                a.image.name = rel
                a.save(update_fields=['image'])
                fixed_a += 1

        self.stdout.write(self.style.SUCCESS(f"Accessories remapped: {fixed_a}"))


