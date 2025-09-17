# PawPalace

Marketplace for dogs and accessories built with Django 4.2.

## Quick start

1. Create and activate a virtualenv (Python 3.9+)
2. Install dependencies:
   
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file at the repo root:

   ```env
   DEBUG=True
   SECRET_KEY=change-me
   ALLOWED_HOSTS=127.0.0.1,localhost
   CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
   STRIPE_PUBLIC_KEY=
   STRIPE_SECRET_KEY=
   ```

4. Apply migrations and run:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

Optional seed data:

```bash
python manage.py seed_dogs
python manage.py seed_accessories
```

## Environment & security

- Configuration is read from `.env`. Never commit real secrets.
- In production set `DEBUG=False`, provide strong `SECRET_KEY`, set `ALLOWED_HOSTS`, and use HTTPS. Security headers are enabled automatically when `DEBUG=False`.

## Payments (Stripe)

- Uses Stripe Checkout for accessories. Add your test keys to `.env`.
- For production, add a webhook endpoint to process `checkout.session.completed` and fulfill orders (not yet implemented).

## Apps

- `accounts`: custom user model, auth, profiles, dashboards
- `dogs`: dog listings, favorites, orders
- `messaging`: buyer-seller conversations per dog
- `accessories`: accessories catalog, favorites, cart, Stripe checkout

## Frontend

- Templates use Tailwind via CDN and Font Awesome.
- Favorite buttons use AJAX with CSRF token exposed in `base.html`.

## Next steps

- Add Stripe webhooks and accessory order models with inventory deduction.
- Add Terms/Privacy/FAQ pages and links.
- Expand tests for messaging scoping, cart limits, and orders.