from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from dogs.models import Dog
import requests


class Command(BaseCommand):
    help = "Seed the database with mock dogs and a demo seller."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=8, help='Number of dogs to create')

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

        dog_data = [
            {
                'name': 'Buddy', 'breed': 'Labrador Retriever', 'age': 18, 'gender': 'male', 'price': '850.00',
                'description': 'Friendly and energetic, loves to play fetch.', 'location': 'New York',
                'is_vaccinated': True, 'is_neutered': False, 'image_url': 'https://images.unsplash.com/photo-1517849845537-4d257902454a'
            },
            {
                'name': 'Bella', 'breed': 'German Shepherd', 'age': 24, 'gender': 'female', 'price': '1200.00',
                'description': 'Loyal and intelligent, well-trained.', 'location': 'Los Angeles',
                'is_vaccinated': True, 'is_neutered': True, 'image_url': 'https://images.unsplash.com/photo-1543466835-00a7907e9de1'
            },
            {
                'name': 'Max', 'breed': 'Golden Retriever', 'age': 20, 'gender': 'male', 'price': '1100.00',
                'description': 'Gentle and affectionate family dog.', 'location': 'Chicago',
                'is_vaccinated': True, 'is_neutered': False, 'image_url': 'https://images.unsplash.com/photo-1558944351-c6c180df6781'
            },
            {
                'name': 'Luna', 'breed': 'French Bulldog', 'age': 14, 'gender': 'female', 'price': '1500.00',
                'description': 'Playful and charming companion.', 'location': 'Houston',
                'is_vaccinated': True, 'is_neutered': True, 'image_url': 'https://images.unsplash.com/photo-1552053831-71594a27632d'
            },
            {
                'name': 'Charlie', 'breed': 'Pomeranian', 'age': 10, 'gender': 'male', 'price': '900.00',
                'description': 'Small, fluffy, and full of personality.', 'location': 'Phoenix',
                'is_vaccinated': True, 'is_neutered': False, 'image_url': 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b'
            },
            {
                'name': 'Lucy', 'breed': 'Beagle', 'age': 16, 'gender': 'female', 'price': '700.00',
                'description': 'Curious and friendly scent hound.', 'location': 'Philadelphia',
                'is_vaccinated': True, 'is_neutered': True, 'image_url': 'https://images.unsplash.com/photo-1507146426996-ef05306b995a'
            },
            {
                'name': 'Cooper', 'breed': 'Siberian Husky', 'age': 22, 'gender': 'male', 'price': '1300.00',
                'description': 'Active and vocal, needs regular exercise.', 'location': 'San Antonio',
                'is_vaccinated': True, 'is_neutered': False, 'image_url': 'https://images.unsplash.com/photo-1543466835-8b7b3b2a1c5a'
            },
            {
                'name': 'Daisy', 'breed': 'Labrador Retriever', 'age': 12, 'gender': 'female', 'price': '950.00',
                'description': 'Sweet-tempered and eager to please.', 'location': 'San Diego',
                'is_vaccinated': True, 'is_neutered': True, 'image_url': 'https://images.unsplash.com/photo-1518020382113-a7e8fc38eac9'
            },
        ]

        created_count = 0
        for data in dog_data[: options['count']]:
            if Dog.objects.filter(name=data['name'], seller=seller).exists():
                continue

            dog = Dog(
                name=data['name'],
                breed=data['breed'],
                age=data['age'],
                gender=data['gender'],
                price=data['price'],
                description=data['description'],
                location=data['location'],
                is_vaccinated=data['is_vaccinated'],
                is_neutered=data['is_neutered'],
                seller=seller,
                status='available',
                is_featured=False,
            )

            # Download image and attach to ImageField
            try:
                resp = requests.get(data['image_url'] + '?auto=format&fit=crop&w=1200&q=80', timeout=15)
                resp.raise_for_status()
                file_name = f"{data['name'].lower().replace(' ', '_')}.jpg"
                dog.image.save(file_name, ContentFile(resp.content), save=False)
            except Exception:
                # Skip image if download fails; model requires it, so fallback to a tiny blank pixel
                dog.image.save('placeholder.jpg', ContentFile(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'), save=False)

            dog.save()
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} dog(s). Demo seller: demo_seller / password123"))


