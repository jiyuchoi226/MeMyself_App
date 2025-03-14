import time
import os
import requests
from datetime import datetime
from typing import Dict, List
import json
import glob

SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 3600)) 
API_URL = "http://backend:8000/sync-calendar"

def get_registered_users() -> List[str]:
    try:
        active_users_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_users.json')
        if not os.path.exists(active_users_path):
            return []
            
        with open(active_users_path, 'r') as f:
            active_users = json.load(f)
            return [user['user_id'] for user in active_users]
            
    except Exception as e:
        print(f"등록된 사용자 목록 조회 실패: {str(e)}")
        return []

def load_active_users() -> List[Dict]:
    """활성 사용자 정보 로드"""
    try:
        active_users_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_users.json')
        if os.path.exists(active_users_path):
            with open(active_users_path, 'r') as f:
                active_users = json.load(f)
                return {user['user_id']: user['token'] for user in active_users}
    except Exception as e:
        print(f"활성 사용자 로드 실패: {str(e)}")
    return {}

def sync_calendars():
    """모든 등록된 사용자의 캘린더 동기화 시도"""
    print(f"\n[{datetime.now()}] 캘린더 동기화 시작")
    
    registered_users = get_registered_users()
    active_tokens = load_active_users()
    
    for user_id in registered_users:
        try:
            token = active_tokens.get(user_id)
            if token:
                print(f"사용자 {user_id} 동기화 시도 (활성 토큰 사용)")
                response = requests.post(API_URL, json={
                    "user_id": user_id,
                    "token": token
                })
                print(f"사용자 {user_id} 동기화 결과: {response.status_code}")
            else:
                print(f"사용자 {user_id}의 토큰 없음 - 동기화 스킵")
                
        except Exception as e:
            print(f"사용자 {user_id} 동기화 실패: {str(e)}")

def main():
    print("스케줄러 시작: 1시간 간격으로 FAISS 업데이트")
    while True:
        sync_calendars()
        time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    main() 