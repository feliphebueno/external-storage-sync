from django.contrib.auth import get_user_model, hashers

User = get_user_model()

User.objects.get_or_create(
    username="root",
    defaults={
        "first_name": "Root",
        "last_name": "User",
        "email": "feliphezion@gmail.com",
        "is_staff": True,
        "is_superuser": True,
        "password": hashers.make_password("admin"),
    },
)
