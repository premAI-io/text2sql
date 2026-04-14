from rest_framework import serializers


class AgentOutputSerializer(serializers.Serializer):
    session_name = serializers.CharField()
    question = serializers.CharField()
    # db_connection_uri removed - sensitive data, never exposed to clients
    route_taken = serializers.ChoiceField(
        choices=["plot", "analyse", "query", "followup"]
    )
    input_dataframe = serializers.DictField(allow_null=True)
    output_dataframe = serializers.DictField(allow_null=True)
    sql_string = serializers.CharField(allow_null=True)
    analysis = serializers.CharField(allow_null=True)
    reasoning = serializers.CharField(allow_null=True)
    plot_config = serializers.DictField(allow_null=True)
    image_to_plot = serializers.CharField(allow_null=True)
    followup_route = serializers.ChoiceField(
        choices=["plot", "analyse", "query", "followup"], allow_null=True
    )
    followup_suggestion = serializers.CharField(allow_null=True)
    error_from_pipeline = serializers.CharField(allow_null=True)


# Sessions
class SessionCreationRequestSerializer(serializers.Serializer):
    base_url = serializers.CharField()


class SessionCreationResponseSerializer(serializers.Serializer):
    status_code = serializers.ChoiceField(choices=[200, 401, 500])
    status = serializers.ChoiceField(choices=["success", "error"])

    session_id = serializers.IntegerField(allow_null=True)
    session_name = serializers.CharField(allow_null=True)
    # db_connection_uri and session_db_path removed - sensitive, never exposed
    created_at = serializers.DateTimeField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)


class SessionSummarySerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    session_name = serializers.CharField(max_length=255)
    created_at = serializers.DateTimeField()
    base_url = serializers.CharField()
    # db_connection_uri and session_db_path removed - sensitive, never exposed


class SessionListResponseSerializer(serializers.Serializer):
    status_code = serializers.ChoiceField(choices=[200, 401, 404, 500])
    status = serializers.ChoiceField(choices=["success", "error"])
    sessions = SessionSummarySerializer(many=True, allow_null=True)
    total_count = serializers.IntegerField(allow_null=True)
    page = serializers.IntegerField(allow_null=True)
    page_size = serializers.IntegerField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)


class SessionDeletionResponse(serializers.Serializer):
    session_name = serializers.CharField(max_length=255)
    status_code = serializers.ChoiceField(choices=[200, 401, 404, 500])
    status = serializers.ChoiceField(choices=["success", "error"])
    error_message = serializers.CharField(allow_null=True)


# Chats (Completions)
class CompletionCreationRequestSerializer(serializers.Serializer):
    session_name = serializers.CharField()
    question = serializers.CharField()


class CompletionCreationResponseSerializer(serializers.Serializer):
    status_code = serializers.ChoiceField(choices=[200, 401, 404, 500])
    status = serializers.ChoiceField(choices=["success", "error"])
    message_id = serializers.IntegerField(allow_null=True)
    session_name = serializers.CharField(allow_null=True)
    message = AgentOutputSerializer(allow_null=True)
    created_at = serializers.DateTimeField(allow_null=True)
    question = serializers.CharField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)


class CompletionSummarySerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    session_name = serializers.CharField()
    # base_url removed - not needed in chat history, already known from session
    created_at = serializers.DateTimeField()
    question = serializers.CharField(allow_null=True)
    message = AgentOutputSerializer(allow_null=True)


class CompletionListResponseSerializer(serializers.Serializer):
    status_code = serializers.ChoiceField(choices=[200, 401, 404, 500])
    status = serializers.ChoiceField(choices=["success", "error"])
    completions = CompletionSummarySerializer(many=True, allow_null=True)
    total_count = serializers.IntegerField(allow_null=True)
    page = serializers.IntegerField(allow_null=True)
    page_size = serializers.IntegerField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)


# Utility function for creating model serializers
def create_model_serializer(model_class):
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_class
            fields = "__all__"

    return ModelSerializer
