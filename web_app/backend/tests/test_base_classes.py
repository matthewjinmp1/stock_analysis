import pytest
from unittest.mock import MagicMock
from web_app.backend.services.base_service import BaseService
from web_app.backend.controllers.base_controller import BaseController

def test_base_service():
    mock_repo = MagicMock()
    service = BaseService(mock_repo)
    assert service.repository == mock_repo

def test_base_controller():
    mock_service = MagicMock()
    controller = BaseController(mock_service)
    assert controller.service == mock_service
