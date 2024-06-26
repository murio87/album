from django.db import models
from users.models import CustomUser
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

PUBLIC = 'public'
PRIVATE = 'private'
VISIBILITY_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]

class Album(models.Model):
    name = models.CharField(max_length=700, blank=False, null=False)
    age = models.CharField(max_length=20, blank=False, null=True)
    desc = models.CharField(max_length=700, blank=False, null=False)
    title = models.CharField(max_length=700, blank=False, null=False)
    location = models.CharField(max_length=700, blank=False, null=False)
    banner = models.ImageField(upload_to='album/banner')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=PUBLIC)
    

    def __str__(self):
        return self.name


class Images(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True)
    images = models.ImageField(upload_to='album/images')


@receiver(post_delete, sender=Album)
def delete_album_images(sender, instance, **kwargs):
    images = Images.objects.filter(album=instance)
    images.delete()


post_delete.connect(delete_album_images, sender=Album)

class Picha(models.Model):
    images = models.ImageField(upload_to='src/images')
