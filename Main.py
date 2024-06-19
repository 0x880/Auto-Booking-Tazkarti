import asyncio
import aiohttp
import re
import json
import time

class Tazkarti:
    def __init__(self, username, password, search_word, seats, price):
        self.username = username
        self.password = password
        self.search_word = search_word
        self.seats = seats
        self.price = price
        self.wait = 0
        self.matches = None
        self.team_info = self.get_team_info()

    def get_team_info(self):
        teams = {
            'سماع': {'team_name': 'الاسماعيلى', 'eng_team': 'ISMAILY SC', 'categoryName': 'ISMAILY'},
            'زمالك': {'team_name': 'الزمالك', 'eng_team': 'Zamalek SC', 'categoryName': 'Zamalek'},
            'هل': {'team_name': 'الأهلى', 'eng_team': 'Al Ahly FC', 'categoryName': 'Al-Ahly'},
            'مصر': {'team_name': 'النادي المصري للألعاب الرياضية', 'eng_team': 'Al-Masry SC', 'categoryName': 'Al-Masry'}
        }

        for key in teams:
            if key in self.search_word:
                return teams[key]
        raise ValueError("الفريق غير موجود في القائمة")

    async def find_match_details(self):
        headers = {
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
            'sec-ch-ua-platform': '"Android"'
        }

        async with aiohttp.ClientSession() as session:
            match_id = None
            team_id = None
            category_id = None
            match_team_zone_id = None

            async with session.get('https://tazkarti.com/data/matches-list-json.json', headers=headers) as response:
                self.matches = await response.json()

            for match in self.matches:
                if match["teamName1"] == self.team_info['eng_team'] or match["teamName2"] == self.team_info['eng_team']:
                    match_id = match["matchId"]
                    break

            if not match_id:
                print("لم يتم العثور على المباراة للفريق المحدد.")
                return

            async with session.get(f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{match_id}.json', headers=headers) as response:
                r1 = await response.json()

            for item in r1['data']:
                if item['categoryName'] == self.team_info['categoryName']:
                    category_id = item['categoryId']
                    team_id = item['teamId']
                    match_team_zone_id = item['matchTeamzoneId']
                    break

            if not (category_id and team_id and match_team_zone_id):
                print("لم يتم العثور على تفاصيل الفئة للحجز.")
                return

            self.match_id = match_id
            self.team_id = team_id
            self.category_id = category_id
            self.match_team_zone_id = match_team_zone_id

            await self.login_and_book_ticket(session)

    async def wait_for_registration(self):
        while True:
            try:
                headers = {
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
                    'sec-ch-ua-platform': '"Android"'
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get('https://tazkarti.com/data/matches-list-json.json', headers=headers) as response:
                        res = await response.text()
                        if self.team_info['eng_team'] in res:
                            self.matches = json.loads(res)
                            break
                        else:
                            self.wait += 1
                            print(f'\rفي انتظار فتح التسجيل ... من فضلك لا تغلق البرنامج: {self.wait}', end='')
                            await asyncio.sleep(1)
            except Exception as e:
                print(f"حدث استثناء: {e}")

    async def login_and_book_ticket(self, session):
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://tazkarti.com',
                'Referer': 'https://tazkarti.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PPA-LX2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"'
            }

            json_data = {
                'Username': self.username,
                'Password': self.password,
                'recaptchaResponse': ''
            }

            async with session.post('https://tazkarti.com/home/Login', headers=headers, json=json_data) as response:
                r = await response.text()
                tok = r.split('access_token":"')[1].split('"')[0]

            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': f'Bearer {tok}',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://tazkarti.com',
                'Pragma': 'no-cache',
                'Referer': 'https://tazkarti.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PPA-LX2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"'
            }

            json_data2 = {
                'stadiumId': 1,
                'matchId': int(self.match_id),
                'teamId': int(self.team_id),
                'lockedSeatsList': [
                    {
                        'categoryId': int(self.category_id),
                        'countSeats': int(self.seats),
                        'price': float(self.price),
                        'matchTeamZoneId': int(self.match_team_zone_id),
                    }
                ]
            }

            async with session.post('https://tazkarti.com/booksprt/BookingTickets/addSeats', headers=headers, json=json_data2) as response:
                r2 = await response.text()
                guid = r2.split('seatGuid":"')[1].split('"')[0]
                id = r2.split('id":')[1].split(',')[0]

            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': f'Bearer {tok}',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'https://tazkarti.com',
                'Pragma': 'no-cache',
                'Referer': 'https://tazkarti.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PPA-LX2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"'
            }

            json_data3 = {
                'matchId': int(self.match_id),
                'lockedSeatsList': [
                    {
                        'id': int(id),
                        'seatGuid': str(guid),
                        'isDeleted': False,
                        'assignFanId': str(self.username),
                    }
                ]
            }

            async with session.post('https://tazkarti.com/booksprt/BookingTickets/assignSeats', headers=headers, json=json_data3) as response:
                r3 = await response.text()
                if 'assignFanId":"' in r3:
                    print(r3)
                    print("تم الحجز بنجاح 😍 ✅")
                    print("يمكنك الآن إغلاق البرنامج ⚠️ ")
                    await asyncio.sleep(10 * 1000)
                elif "This assignFanID assigned before or same category in seats=" in r3:
                    print("تم تسجيل هذا المستخدم من قبل في هذه الفئة ✅ ")
                elif "no seats locked" in r2:
                    print("عذرًا، لا توجد تذاكر كافية متاحة في هذه الفئة. يرجى اختيار فئة أخرى.")
        except Exception as e:
            print(f"حدث استثناء أثناء الحجز: {e}")

async def main():
    inp = open('data.txt', encoding="utf-8").read()
    a = inp.splitlines()
    us = a[0]
    ps = a[1]
    search_word = a[2]
    seats = a[3]
    price = a[4]
    bot = Tazkarti(us, ps, search_word, seats, price)
    await bot.wait_for_registration()
    await bot.find_match_details()

if __name__ == "__main__":
    asyncio.run(main())