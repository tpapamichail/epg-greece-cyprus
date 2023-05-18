from datetime import datetime, timedelta
import pytz
import requests
import xmlutil
import os

URL = 'https://www.cosmotetv.gr/portal/residential/program?p_p_id=dayprogram_WAR_OTETVportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_dayprogram_WAR_OTETVportlet_date={DATE}&_dayprogram_WAR_OTETVportlet_feedType=EPG&_dayprogram_WAR_OTETVportlet_start=0&_dayprogram_WAR_OTETVportlet_end=102&_dayprogram_WAR_OTETVportlet_platform=DTH&_dayprogram_WAR_OTETVportlet_categoryId=-1'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Sec-Fetch-Site': 'none',
    'Cookie': 'JSESSIONID=68ABD1B1DC250CF2BE665B921FA59838.prod-node-1dtCookie=v_4_srv_9_sn_C694414EC21012097CEB5BBFE88BCA85_perc_100000_ol_0_mul_,1_app-3Aea7c4b59f27d43eb_0_rcs-3Acss_0; COOKIE_SUPPORT=true; GUEST_LANGUAGE_ID=el_GR',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Fetch-Mode': 'navigate',
    'Host': 'www.cosmotetv.gr',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Sec-Fetch-Dest': 'document',
    'Connection': 'keep-alive'
}

TIMEZONE = datetime.now(pytz.timezone('Europe/Athens')).strftime('%z')


def parse(channel, cosmote_cache):
    server_name = channel.get('serverName')
    epg_name = channel.get('epgName')
    print(f'{epg_name} start')

    channel_epg = []

    for date_diff in range(-1, 8):
        date_now = datetime.now(pytz.timezone("Europe/Athens")) + timedelta(days=date_diff)
        date_str = date_now.strftime('%d-%m-%Y')

        if date_str not in cosmote_cache:
            print(f'Cosmote: {date_str} not found, caching..')

            response = requests.get(URL.replace('{DATE}',date_str), headers=HEADERS, timeout=160)

            cosmote_cache[date_str] = response.json()

        json = cosmote_cache[date_str]

        day = json['currentDay']
        channel = list(filter(lambda x: x['ID'] == server_name, json['channels']))[0]
        programs = channel['shows']

        for program in programs:
            start_time_string = day + ' ' + program['startTime'] + ' ' + TIMEZONE
            start_time = datetime.strptime(start_time_string, '%d-%m-%Y %H:%M %z').timestamp()

            end_time_string = day + ' ' + program['endTime'] + ' ' + TIMEZONE
            end_time = datetime.strptime(end_time_string, '%d-%m-%Y %H:%M %z').timestamp()

            # If end time is less than start time, it means that the program ends on the next day
            if end_time < start_time:
                end_time = end_time + 86400

            program_object = {
                'channel': epg_name,
                'title': program['title'],
                'start_time': start_time,
                'end_time': end_time,
                'description': program['title']
            }

            channel_epg.append(program_object)

    icon = channel.get('icon')
    xmlutil.push(epg_name, channel_epg, icon)


