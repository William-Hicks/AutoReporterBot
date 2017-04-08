import praw
import time
import datetime
import re
import threading
import random
import os
import string
import random
from variables import sub_listing, responses, master_dict


class Modmail(object):

	def __init__(self, subreddit, subreddits, reddit):
		self.subreddit = subreddit
		self.subreddits = subreddits
		self.reddit = reddit
		self.report_at = subreddits[subreddit]['report']
		self.remove_at = subreddits[subreddit]['remove']
		self.verbose = subreddits[subreddit]['verbose']
		self.reports = self.get_reports()

	def save(self, sub_id):
		with open('saved.txt','a') as f:
			f.write(str(sub_id) + ' ')
			f.close()

	def check(self, sub_id):
		with open('saved.txt','r') as f:
			if str(sub_id) in f.read().split(' '):
				return True
			else:
				return False

	def modmailed(self, sub_id):
		with open('modmailed.txt','r') as f:
			if str(sub_id) in f.read().split(' '):
				return True
			else:
				return False

	def save_modmail(self, sub_id):
		with open('modmailed.txt','a') as f:
			f.write(str(sub_id) + ' ')
			f.close()

	def get_reports(self, limit=25):
		try:
			user_reports = {}
			queue = self.reddit.request('GET','r/{}/about/reports?limit={}'.format(self.subreddit, limit))['data']['children']
			for item in queue:
				if len(item['data']['user_reports']) < 1:
					pass
				else:
					user_reports[item['data']['id']] = item['data']['user_reports']
			return user_reports
		except:
			return {'id':'nothing'}

	def check_answered(self, sub_id):
		with open('answered.txt') as f:
			if f.read().split(' ').count(sub_id) > 0:
				return True
			else:
				return False
				
	def save_answered(self, sub_id):
		with open('answered.txt', 'a') as f:
			f.write(str(sub_id) + ' ')
			f.close()

	def check_reports(self):
		for report in self.reports:
			count = 0
			for item in self.reports[report]:
				count += int(item[-1])
			if count >= self.report_at:
				self.report_modmail(count=count, sub_id=report)

	def save_record(self, author):
		with open('records.txt') as f:
			f.write(author+'\n')
			f.close()

	def report_modmail(self, count, sub_id):
		try:
			print('Threshold met in /r/{}'.format(self.subreddit))
			submission = self.reddit.submission(sub_id)
			user = _reddit_.redditor(str(submission.author))
			created = time.strftime(('%Y %m %d'),time.localtime(user.created_utc)).split(' ')
			now = datetime.date.today()
			years = int(now.year) - int(created[0])
			months = int(now.month) - int(created[1])
			try:
				if months < 0:
					months = 12 + months
					years -= 1
				if years < 1:
					info = '[{} | {} | {} months](/u/{})'.format(user.link_karma, user.comment_karma, months)
				else:
					info = '[{} | {} | {} years {} months]'.format(user.link_karma, user.comment_karma, years, months)
			except:
				info = '[Unavailable]'
			u_reports = submission.user_reports
			reports = ''
			for report in u_reports:
				report = str(report)
				report = report.replace('[',''); report = report.replace(']','')
				reports += '*{}*\n\n'.format(report)
			if count >= self.remove_at and self.check(submission.id) is False:
				submission.mod.remove()
				try:
					print('Preparing to send modmail')
					self.reddit.subreddit(self.subreddit).message('Post Removal','[{}]({}) by /u/{} {} has been removed. [Image/video]({})\n\n[Report reasons:]({})\n\n{}\n\n---'.format(submission.title,submission.permalink, submission.author, info,submission.url,'https://www.reddit.com/r/{}/about/rules'.format(self.subreddit), reports))
					self.save(submission.id)
					print('Sent modmail to /r/{}'.format(self.subreddit))
				except:
					pass
			elif count >= self.report_at and count < self.remove_at and self.modmailed(submission.id) is False:
				print('Reporting')
				things = ''; count = 1
				try:
					rules = self.reddit.request('GET','r/{}/about/rules'.format(self.subreddit))
				except:
					rules = ['No personal attacks','Threatening or harassing','Spam']
				sub_rules = [rule['violation_reason'] for rule in rules['rules']]
				for rule in sub_rules:
					things += '^({}. {})\n\n'.format(count, rule)
					count+= 1
				try:
					title = re.sub('\(','',submission.title)
					title = re.sub('\)','',title)
				except Exception as e:
					print(e)
					title = 'Unable to retrieve title'
				try:
					author = str(submission.author)
				except:
					author = '[deleted]'
				if self.verbose is True:
					if submission.is_self == True:
						self.reddit.subreddit(self.subreddit).message('Reports','[{}]({}) by /u/{} {} has received {} reports.\n\nHere are the report reasons:\n\n{}\n\n---\n\nRemoval Reasons:\n\n{}\n\n---\n\nKEYS: !ap = approve + ignore | !rm = remove | !ban = ban'.format(title,submission.permalink, author, info, self.report_at, reports, things))
					else:
						if submission.is_self != True:
							self.reddit.subreddit(self.subreddit).message('Reports','[{}]({}) by /u/{} {} has received {} reports.\n\n[Image/video]({})\n\nHere are the report reasons:\n\n{}\n\n---\n\nRemoval Reasons:\n\n{}\n\n---\n\nKEYS: !ap = approve + ignore | !rm = remove | !ban = ban'.format(title,submission.permalink, submission.author, info, self.report_at, submission.url,reports, things))
				else:
					if submission.is_self == True:
						self.reddit.subreddit(self.subreddit).message('Reports','[{}]({}) by /u/{} {} has received {} reports.\n\n[Report reasons:]({})\n\n{}'.format(title,submission.permalink, submission.author, info, self.report_at, '/r/{}/about/rules'.format(submission.subreddit.display_name), reports))
					else:
						self.reddit.subreddit(self.subreddit).message('Reports','[{}]({}) by /u/{} {} has received {} reports.\n\n[Image/video]({})\n\n[Report reasons:]({})\n\n{}'.format(title,submission.permalink,submission.author, info, self.report_at, submission.url,'/r/{}/about/rules'.format(submission.subreddit.display_name),reports))
				self.save_modmail(submission.id)
				print('Report successful')
			else:
				print('Already modmailed')
		except Exception as e:
			print(e)

	def check_modmail(self):
		for message in self.reddit.subreddit(self.subreddit).mod.inbox(limit=2):
			if message.subject == "Post Removal" or message.subject == "Reports":
				try:
					permalink = message.body[re.search('\(',message.body).span()[1]:re.search('\)',message.body).span()[0]]
					submission = self.reddit.submission(url='https://www/reddit.com'+permalink)
					for reply in message.replies:
						if '!rm' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							print('About to remove')
							self.save_answered(submission.id)
							reply.reply('Submission removed! {}'.format(random.choice(responses)))
							removal_prefix = 'Hello, /u/{}, unfortunately your submission has been removed for breaking the following subreddit rules:\n\n'.format(submission.author)
							message_mods = '\n\n---\n\n*If you have any questions, please [message the mods](https://www.reddit.com/message/compose?to={})*'.format(submission.subreddit)
							rules = self.reddit.request('GET','r/{}/about/rules'.format(submission.subreddit))
							sub_rules = [rule['violation_reason'] for rule in rules['rules']]
							try:
								reason = int(reply.body[re.search('!rm',reply.body).span()[1]+1:re.search('\d+',reply.body).span()[1]])
							except:
								reason = None
							if reason == None:
								try:
									reason = reply.body[re.search('\<',reply.body).span()[1]:re.search('\>',reply.body).span()[0]]
								except:
									reason = None
							if reason == None:
								default_response = '*Hello, /u/{}, your submission has been removed because it violates our [subreddit rules]({}). If you have any questions or concerns, or feel that this was done in error, please [message the moderators]({}). Best of luck in the future!*\n\n---\n\n^(I am a bot, and this action was performed automatically. For more information on me, follow) [^this ^link](https://www.reddit.com/r/AutoReporterBot/wiki/index)'.format(submission.author,'/r/{}/about/rules'.format(submission.subreddit), "https://www.reddit.com/message/compose?to=%2Fr%2F{}&subject=Removal%20Appeal&message=After%20having%20read%20the%20rules%2C%20I%20still%20have%20a%20question%20regarding%20the%20removal%20of%20my%20submission%0A%0A{}".format(submission.subreddit,submission.permalink))
								try:
									submission.mod.remove()
									(submission.reply(default_response).mod.distinguish(sticky=True))
								except Exception as e:
									reply.reply('*The submission was removed but there was an error in leaving a comment. Thanks. I am a bot.*')
							else:
								try:
									comment = submission.reply('{}* **{}**{}'.format(removal_prefix,sub_rules[reason-1],message_mods))
								except:
									comment = submission.reply('{}* **{}**{}'.format(removal_prefix,reason,message_mods))
								comment.mod.distinguish(sticky=True)
								submission.mod.remove()
							print('Removed')
						elif '!ap' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							print('APPROVE')
							self.save_answered(submission.id)
							reply.reply('Submission approved! *{}*'.format(random.choice(responses)))
							submission.mod.approve()
							print('Approved')
							self.save_answered(submission.id)
						elif '!ban' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							self.save_answered(submission.id)
							reply.reply('/u/{} has been banned! Enjoy your power you cancer mods! {}'.format(submission.author, random.choice(responses)))
							try:
								days = reply.body[re.search('!ban',reply.body).span()[1]+1:re.search('\d+',reply.body).span()[0]]
							except:
								days = None
							print("Banning user")
							self.reddit.subreddit(self.subreddit).banned.add(submission.author, ban_reason=str(submission.permalink)+' '+str(reply.author), duration=days)
							submission.mod.remove()
						elif '!shadow' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							reply.reply('/u/{} has been shadowbanned. I am a bot'.format(submission.author))
							print('Banning')
							submission.mod.remove()
							wiki = self.reddit.request('GET','r/{}/wiki/config/automoderator'.format(self.subreddit))['data']['content_md']
							banned = 'type: any\nauthor: {}\naction: remove\naction_reason: shadowbanned user\n#Bot shadowbanned by /u/{}\n---'.format(submission.author, reply.author)
							self.reddit.subreddit(self.subreddit).wiki['config/automoderator'].edit(content=wiki + '\n\n' + banned, reason='Shadowbanned user')
							print('Banned')
							self.save_answered(submission.id)
						elif '!watch' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							submission.mod.remove()
							reply.reply('/u/{} has been watchlisted. I am a bot'.format(submission.author))
							wiki = self.reddit.request('GET','r/{}/wiki/config/automoderator'.format(self.subreddit))['data']['content_md']
							banned = 'type: any\nauthor: {}\naction: report\naction_reason: shadowbanned user\n#Bot shadowbanned by /u/{}'.format(submission.author, reply.author)
							self.reddit.subreddit(self.subreddit).wiki['config/automoderator'].edit(content=wiki + '\n\n' + banned, reason='Shadowbanned user')
							self.save_answered(submission.id)
						elif '!globalshadowban' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							submission.mod.remove()
							self.save_answered(submission.id)
							reply.reply('/u/{} has been global banned! Oh you cancerous bastard! I am a bot'.format(submission.author))
							banned = 'type: any\nauthor: {}\naction: report\naction_reason: shadowbanned user\n#Bot shadowbanned by /u/{}'.format(submission.author, reply.author)
							for subreddit in reddit.user.moderator_subreddits():
								try:
									wiki = self.reddit.request('GET','r/{}/wiki/config/automoderator'.format(subreddit))['data']['content_md']
									_reddit_.subreddit(subreddit).wiki['config/automoderator'].edit(content=wiki + '\n\n' + banned, reason='Shadowbanned user')
								except:
									pass
							print('Global banned')
						elif '!spam' in reply.body.split(' ') and self.check_answered(submission.id) is False:
							self.reply('Submission removed as spam! I am a bot')
							submission.mod.remove(spam=True)
							self.save_answered(submission.id)
						else:
							pass
				except:
					pass

class nukeCode(object):

	def __init__(self, subreddit):
		self.subreddit = subreddit
		self.alphanumeric = [letter for letter in string.printable if letter not in [i for i in "{|}~' \t\n\r\x0b\x0c"]]
		self.code = [random.randint(0,9) for x in range(10)]
		self.replace = random.randint(0,3)
		self.values = self.get_code()
		self.today_code = self.set_code()
		self.today = datetime.date.today().day
		self.old = self.is_new_day()
		self.submit()

	def get_code(self):
		settings = []
		for v in range(self.replace):
			settings.append(random.randint(0,9))
		return settings

	def set_code(self):
		for place in self.values:
			self.code[place] = random.choice(self.alphanumeric)
		code = ''.join([str(item) for item in self.code])
		return code
		
	def is_new_day(self):
		last_submission = r.subreddit(self.subreddit).new(limit=1)
		new_made = [submission.created_utc for submission in last_submission]
		made_day = time.strftime('%d',time.localtime(new_made[0]))
		if int(made_day) != (self.today):
			return True
		else:
			return False

	def submit(self):
		if self.old is True:
			try:
				submission = r.subreddit(self.subreddit).submit('{}'.format(time.strftime('%A, %B %d, %Y')), selftext=self.today_code)
				print('Submitted nukeCode')
				submission.reply('Pinging /u/just-a-traveler and /u/randoh12')
				print('Replied to nukeCode')
				return True
			except Exception as e:
				print(e)
				return False

	def current_code(self):
		try:
			submissions = r.subreddit('BotMasters').new(limit=1)
			for submission in submissions:
				code = submission.selftext
			return code
		except:
			print('nukeCode')

class botAdmin(object):

	def __init__(self, message, subreddits, reddit):
		self.message = message
		self.reddit = reddit
		self.subreddits = subreddits
		self.subject = message.subject
		self.author = message.author
		self.body = message.body
		self.approved_code = nukeCode('BotMasters').current_code()
		self.preview = '*A message concerning the AutoReporterBot, from Skynet*\n\n'

	def isApproved(self):
		if self.approved_code in self.subject:
			return True
		else:
			return False

	def isBroadcast(self):
		if '!broadcast' in self.subject:
			return True
		else:
			return False

	def announcement(self):
		print('Today\'s approved code: {}'.format(self.approved_code))
		listing = ''
		for subreddit in self.subreddits:
			listing += '\n\n* /r/{}'.format(subreddit)
		if self.isBroadcast() is True and self.isApproved() is True:
			for subreddit in self.subreddits:
				self.reddit.subreddit(subreddit).message('Official Bot Announcement',self.preview+self.body)
				print('Message sent to /r/{}'.format(subreddit))
			self.message.reply('*Thank you! Your message will be delivered momentarily to the following subreddits:*\n\n'+listing)
		else:
			pass

	def isInvite(self):
		if 'invitation to moderate' in self.subject:
			try:
				self.reddit.subreddit(self.message.subreddit.display_name).mod.accept_invite()
				print('Accepted invite to /r/{}'.format(self.message.subreddit))
			except Exception as e:
				pass

	def isQuery(self): 
		if self.isApproved() is True and '!query' in self.subject:
			pass


def announcement_thread(reddit):
	while True:
		for message in reddit.inbox.unread(limit=1):
			botAdmin(message, sub_listing, reddit).announcement()
			botAdmin(message, sub_listing, reddit).isInvite()
			if any(title in message.subject for title in ['!broadcast','invitation to moderate']):
				message.mark_read()

def thread_starter(sub, subreddits, reddit):
	while True:
		try:
			print('Parsing /r/{} [{}]'.format(sub,str(threading.activeCount())))
			Modmail(sub, subreddits, reddit).check_reports()
			Modmail(sub, subreddits, reddit).check_modmail()
		except:
			Modmail(sub, subreddits, reddit).check_reports()
			Modmail(sub, subreddits, reddit).check_modmail()

def main(subreddits,reddit):
	try:
		for subreddit in subreddits:
			threading.Thread(target=thread_starter, kwargs={'sub':subreddit,'subreddits':subreddits,'reddit':reddit}).start()
		threading.Thread(target=announcement_thread, kwargs={'reddit':reddit}).start()
	except:
		main()

if __name__ == '__main__':
	main()
