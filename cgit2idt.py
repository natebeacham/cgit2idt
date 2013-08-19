import re
import smtplib
import requests

from bs4 import BeautifulSoup as bs
from email.mime.text import MIMEText
from requests.auth import HTTPDigestAuth as auth

TOKEN = '##'
THRESHOLD = 1440

CGIT_URL = 'http://cgit.example.com'
CGIT_LOG_URL = '%s/repo/log/?h=%%s' % CGIT_URL
CGIT_PROTECTED = True
CGIT_CREDS = ('user', 'pass')

TEAM_ADDR = '[your team]@team.idonethis.com'

USER_MAP = {
	'natebeacham': 'nate@example.com',
}

BRANCHES = [
	'master',
	'newfeature',
]

HOURS_RE = re.compile('(?P<num>[0-9]+) hours')
MINS_RE = re.compile('(?P<num>[0-9]+) min')

def parse_delta(buffer):
	if ' hours' in buffer:
		return int(MINS_RE.match(buffer).groupdict()['num']) * 60
	elif ' min' in buffer:
		return int(MINS_RE.match(buffer).groupdict()['num'])

	return None

for branch in BRANCHES:
	kwargs = {}

	if CGIT_PROTECTED:
		kwargs['auth'] = auth(*CGIT_CREDS)

	response = requests.get(CGIT_LOG_URL % branch, **kwargs)

	soup = bs(response.content)

	for entry in soup.find_all('table')[-1].find_all('tr')[1:]:
		timestamp, message, author, fcount, lcount = entry.find_all('td')

		message = message.find_all('a')[0].text

		if TOKEN not in message:
			continue

		author = author.text
		timestamp = timestamp.find_all('span')[0].text
		href = '%s%s' % (CGIT_URL, entry.find_all('a')[0].attrs['href'])

		delta = parse_delta(timestamp)

		if not delta or delta > THRESHOLD:
			continue

		try:
			from_ = USER_MAP[author]
		except KeyError:
			continue

		message = MIMEText(message.replace('##', '') + '\n')
		message['Subject'] = "RE: What'd you get done"
		message['From'] = from_
		message['To'] = TEAM_ADDR

		s = smtplib.SMTP('localhost')
		s.sendmail(from_, [TEAM_ADDR], message.as_string())
		s.quit()

