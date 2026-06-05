from django.db import models

class Journal(models.Model):
    username = models.CharField(max_length=100)
    date = models.DateField()
    content = models.TextField()

    class Meta:
        unique_together = ('username', 'date')

    def __str__(self):
        return f"{self.username} - {self.date}"
