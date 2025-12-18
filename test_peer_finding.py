#!/usr/bin/env python3
# Test peer finding directly
import sys
import os
sys.path.insert(0, 'web_app')

from services.peers_service import PeersService
from repositories.data_repository import DataRepository

# Create service instance
from repositories.peers_repository import PeersRepository
data_repo = DataRepository()
peers_repo = PeersRepository()
peers_service = PeersService(peers_repo, data_repo)

print('Testing direct peer finding for NVDA...')
try:
    result = peers_service.find_peers('NVDA')
    print(f'Result success: {result.get("success", False)}')
    print(f'Peers found: {len(result.get("peers", []))}')
    if not result.get('success', False):
        print(f'Error: {result.get("message", "Unknown error")}')
    else:
        print('SUCCESS: Peer finding worked')
        # Check if it was saved
        saved_result = peers_service.get_peers('NVDA')
        if saved_result.get('success'):
            print('SUCCESS: Results were cached')
        else:
            print('ERROR: Results were not cached properly')
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()