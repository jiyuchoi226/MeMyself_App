from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import  Dict
from fastapi import HTTPException
from zoneinfo import ZoneInfo
import os
import json

class CalendarService:
    def __init__(self):
        self.calendar_service = None
        self.people_service = None
        
    #Google API 서비스
    def _initialize_services(self, token: str):
        try:
            credentials = Credentials(
                token,
                [
                    'https://www.googleapis.com/auth/calendar.readonly',  # 캘린더 일정
                    'https://www.googleapis.com/auth/userinfo.profile',   # 기본 프로필
                    'https://www.googleapis.com/auth/userinfo.email'      # 이메일
                ]
            )
            self.calendar_service = build('calendar', 'v3', credentials=credentials)
            self.people_service = build('people', 'v1', credentials=credentials)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    def get_user_info(self, token: str) -> Dict:
        self._initialize_services(token)
        try:
            profile = self.people_service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,genders,birthdays,photos'
            ).execute()
            user_info = {
                'name': profile.get('names', [{}])[0].get('displayName', ''),
                'email': profile.get('emailAddresses', [{}])[0].get('value', ''),
                'gender': profile.get('genders', [{}])[0].get('value', ''),
                'photo_url': profile.get('photos', [{}])[0].get('url', ''),
            }

            # 생일이 있는 경우 추가
            if 'birthdays' in profile:
                birthday = profile['birthdays'][0].get('date', {})
                if birthday:
                    user_info['birthday'] = f"{birthday.get('year', '')}-{birthday.get('month', '')}-{birthday.get('day', '')}"

            return user_info
        except Exception as e:
            print(f"사용자 정보 가져오기 실패: {str(e)}")
            return {}

    def get_events(self, token, time_range=None):
        try:
            self._initialize_services(token)
            user_info = self.get_user_info(token)
            user_id = user_info.get('email')
            print(f"캘린더 사용자 ID: {user_id}")  
            
            all_events = []     
            
            # 한국 시간 기준 
            now = datetime.now(ZoneInfo("Asia/Seoul"))
            past = datetime(now.year, 1, 1).isoformat() + '+09:00'
            future = datetime(now.year, 4, 30).isoformat() + '+09:00'
            
            print(f"일정 조회 기간: {past} ~ {future}")
            
            calendar_list = self.calendar_service.calendarList().list().execute()             
            for calendar_item in calendar_list['items']:
                calendar_id = calendar_item['id']   
                events_result = self.calendar_service.events().list(
                    calendarId=calendar_id,
                    timeMin=past,
                    timeMax=future,
                    maxResults=2500,
                    singleEvents=True,
                    orderBy='startTime',
                    fields='items(id,summary,description,location,start,end,attendees,hangoutLink,recurrence,reminders,status,created,updated,guestsCanSeeOtherGuests)'
                ).execute()
                
                for event in events_result.get('items', []):
                    event['calendar_info'] = {
                        'id': calendar_id,
                        'summary': calendar_item.get('summary', ''),
                        'description': calendar_item.get('description', '')
                    }
                    
                    # 날짜/시간 포맷 처리
                    if 'start' in event:
                        if 'dateTime' in event['start']:
                            event['start'] = event['start']['dateTime']
                        else:
                            event['start'] = event['start']['date']
                    if 'end' in event:
                        if 'dateTime' in event['end']:
                            event['end'] = event['end']['dateTime']
                        else:
                            event['end'] = event['end']['date']
                
                all_events.extend(events_result.get('items', []))
           
            print(f"총 {len(all_events)}개의 이벤트를 가져왔습니다.")
            return all_events
            
        except Exception as e:
            print(f"이벤트 가져오기 실패: {str(e)}")
            raise e 
        