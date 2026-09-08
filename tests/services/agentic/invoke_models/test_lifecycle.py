def test_provider_registry_is_not_global()->None:
 from app.services.agentic.invoke_models.invoke_models import InvokeModelsService
 assert not hasattr(InvokeModelsService,"providers")
