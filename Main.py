import requests as e
import re
import json
import time

class TicketBooking:
    def __init__(self, user_data_file):
        self.s = e.Session()
        self.wait = 0
        self.load_user_data(user_data_file)
        self.possible_seat_locations = self.determine_seat_locations()
        self.teams = self.initialize_teams()
        self.found = False
        self.team_name = "2929292922"
        self.match_id = None
        self.category_id = None
        self.team_id = None
        self.match_team_zone_id = None
        self.price = None
    
    def load_user_data(self, user_data_file):
        with open(user_data_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
            self.username = lines[0]
            self.password = lines[1]
            self.search_word = lines[2]
            self.seats = lines[3]
            self.category = lines[4]
    
    def determine_seat_locations(self):
        if "درج" in self.category and "ول" in self.category:
            return ["Cat 1", "Cat1"]
        elif "درج" in self.category and "اني" in self.category:
            return ["Cat 2", "Cat2"]
        elif "تالت" in self.category and "ثالث" in self.category:
            return ["Cat 3", "Cat3"]
        elif "مقصو" in self.category:
            return ["VIP"]
        elif "علو" in self.category:
            return ["Upper"]
        elif "سفل" in self.category:
            return ["Lower"]
        else:
            return []
    
    def initialize_teams(self):
        return {
            'سماع': {'team_name': 'الاسماعيلى', 'eng_team': 'ISMAILY SC', 'categoryName': 'ISMAILY', 'teamid': '182'},
            'زمالك': {'team_name': 'الزمالك', 'eng_team': 'Zamalek SC', 'categoryName': 'Zamalek', 'teamid': '79'},
            'هل': {'team_name': 'الأهلى', 'eng_team': 'Al Ahly FC', 'categoryName': 'Al-Ahly', 'teamid': '77'},
            'مصر': {'team_name': 'النادي المصري للألعاب الرياضية', 'eng_team': 'Al-Masry SC', 'categoryName': 'Al-Masry'}
        }

    def find_team_info(self):
        for key in self.teams:
            if key in self.search_word:
                self.found = True
                team_info = self.teams[key]
                self.team_name = team_info['team_name']
                self.eng_team = team_info['eng_team']
                self.category_name = team_info['categoryName']
                self.team_id = team_info['teamid']
                return
        #print("Team not found in the search word.")

    def wait_for_registration(self):
        while True:
            try:
                h = self.get_headers()
                res = self.s.get('https://tazkarti.com/data/matches-list-json.json', headers=h).text
                if self.team_name in res:
                    return res
                else:
                    self.wait += 1
                    print(f'\rإنتظر حتى يفتح التسجيل ... لا تغلق البرنامج : {self.wait}', end='')
                    time.sleep(2)
            except Exception as e:
                print(e)

    def get_headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://tazkarti.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PPA-LX2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }

    def get_match_id(self, res):
        matches = json.loads(res)
        for match in matches:
            if match["teamName1"] == self.eng_team or match["teamName2"] == self.eng_team:
                if match.get('matchStatus') == 1:
                    self.match_id = match["matchId"]
                    return
        exit()

    def get_ticket_info(self):
        r1 = self.s.get(f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{self.match_id}.json', headers=self.get_headers()).text
        r1_data = json.loads(r1)

        for category in r1_data['data']:
            if category['categoryName'] == self.category_name:
                self.category_id = category['categoryId']
                self.team_id = category['teamId']
                self.match_team_zone_id = category['matchTeamzoneId']
                self.price = category['price']
                return
            else:
                for user_seat_location in self.possible_seat_locations:
                    if user_seat_location in category['categoryName'] and int(self.team_id) == category['teamId']:
                        self.category_id = category['categoryId']
                        self.team_id = category['teamId']
                        self.match_team_zone_id = category['matchTeamzoneId']
                        self.price = category['price']
                        return

    def login_and_book_tickets(self):
        headers = self.get_headers()
        headers.update({'Content-Type': 'application/json'})
        json_data = {
            'Username': self.username,
            'Password': self.password,
            'recaptchaResponse': '',
        }
        r = self.s.post('https://tazkarti.com/home/Login', headers=headers, json=json_data).text
        tok = r.split('access_token":"')[1].split('"')[0]
        self.book_seats(tok)

    def book_seats(self, token):
        h2 = self.get_headers()
        h2['Authorization'] = f'Bearer {token}'
        
        json_data2 = {
            'stadiumId': 1,
            'matchId': int(self.match_id),
            'teamId': int(self.team_id),
            'lockedSeatsList': [
                {
                    'categoryId': int(self.category_id),
                    'countSeats': int(self.seats),
                    'price': self.price,
                    'matchTeamZoneId': int(self.match_team_zone_id),
                },
            ],
        }
        
        r2 = self.s.post('https://tazkarti.com/booksprt/BookingTickets/addSeats', headers=h2, json=json_data2).text
        self.handle_ticket_response(r2, token)

    def handle_ticket_response(self, response, token):
        guid = response.split('seatGuid":"')[1].split('"')[0]
        id = response.split('id":')[1].split(',')[0]
        
        h3 = self.get_headers()
        h3['Authorization'] = f'Bearer {token}'
        
        json_data3 = {
            'matchId': int(self.match_id),
            'lockedSeatsList': [
                {
                    'id': int(id),
                    'seatGuid': str(guid),
                    'isDeleted': False,
                    'assignFanId': str(self.username),
                },
            ],
        }
        
        r3 = self.s.post('https://tazkarti.com/booksprt/BookingTickets/assignSeats', headers=h3, json=json_data3).text
        if 'assignFanId":"' in r3:
            #print(r3)
            print("تم التسجيل بنجاح 😍 ✅")
            print("يمكنك إغلاق البرنامج الآن ⚠️ ")
            time.sleep(10*1000)
        elif "This assignFanID assigned before or same category in seats=" in r3:
            print("تم تسجيل هذا المستخدم من قبل في هذه الفئة ✅ ")
        elif "no seats locked" in response:
            print("نأسف، لا توجد تذاكر كافية في هذه الفئة، إختار فئة أخرى ")


if __name__ == '__main__':
    booking = TicketBooking('data.txt')
    booking.find_team_info()
    response_text = booking.wait_for_registration()
    booking.get_match_id(response_text)
    booking.get_ticket_info()
    booking.login_and_book_tickets()
