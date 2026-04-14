from django.db import models


class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    db_connection_uri = models.CharField(max_length=255)
    session_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    base_url = models.URLField()
    session_db_path = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["created_at"]


class Completions(models.Model):
    chat_id = models.AutoField(primary_key=True)
    message_id = models.IntegerField(blank=True, null=True)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="messages"
    )
    session_name = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    question = models.TextField(blank=True, null=True)
    agent_output = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Completions"
