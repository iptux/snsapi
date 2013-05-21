# -*- coding: utf-8 -*-
#
# snsdroid.py
# android ui interface for snsapi
#
# Author: Alex.wang
# Create: 2013-05-19 17:42


from ConfigParser import ConfigParser
import DroidUi as Ui
from snsapi.snspocket import SNSPocket
from snsapi.utils import utc2str


# supported platform
EMAIL = 'Email'
RSS = 'RSS'
RSS_RW = 'RSS2RW'
RENREN_SHARE = 'RenrenShare'
RENREN_STATUS = 'RenrenStatus'
SQLITE = 'SQLite'
SINA_WEIBO = 'SinaWeiboStatus'
TENCENT_WEIBO = 'TencentWeiboStatus'
TWITTER = 'TwitterStatus'


APP = 'SNSDroid'
CONFILES = (
	'conf/snsgui.ini',
	'SNSDroid/conf/snsgui.ini',
	'/sdcard/sl4a/scripts/SNSDroid/conf/snsgui.ini',
)


class SNSGuiConfig(ConfigParser):
	def __init__(self):
		ConfigParser.__init__(self)
		self.optionxform = str
		self.read(CONFILES)
		self.theme = self.get('snsgui', 'theme')

	def getcolor(self, option):
		return self.get(self.theme, option)

	def email(self):
		'''get supported email platforms'''
		return self.options('email')

	def getmail(self, option):
		'''get mail config dict'''
		d = {}
		for key, value in self.items(option):
			d[key] = value
		return d


class CommonView(Ui.DroidUi):
	'''common input view'''
	def __init__(self, title, icon = '@android:drawable/ic_menu_set_as', background = '@android:drawable/screen_background_dark'):
		Ui.DroidUi.__init__(self)
		self.result = None
		layout = Ui.LinearLayout(self,
			background = background,
			layout_height = Ui.FILL_PARENT,
			layout_width = Ui.FILL_PARENT,
		)
		header = Ui.LinearLayout(layout,
			background = '@android:drawable/title_bar',
			orientation = Ui.HORIZONTAL,
			layout_width = Ui.FILL_PARENT,
		)
		Ui.TextView(header,
			text = title,
			gravity = Ui.CENTER,
			layout_weight = 1,
			layout_height = Ui.MATCH_PARENT,
			layout_marginLeft = '30dp',
		)
		Ui.ImageView(header,
			src = icon,
			clickable = Ui.TRUE,
			command = self.ok,
		)
		self.body(layout)

	def quit(self, data = None):
		# if data not saved
		if self.result is None and self.validate():
			yes = Ui.askyesnocancel(APP, 'Save or not?')
			# if `cancelled'
			if yes is None: return
			# if `yes'
			if yes is True: self.apply()
			# if `no', do nothing
		return Ui.DroidUi.quit(self, data)

	def ok(self):
		if self.validate():
			self.apply()
			self.quit()
		else:
			Ui.info('input validate failed')

	def validate(self):
		'''check input, should be override'''
		return False

	def apply(self):
		'''save input to self.result, should be override'''
		pass

	def main(self):
		self.mainloop()
		return self.result


class NewChannel(CommonView):
	'''create a new channel'''
	def __init__(self, platform):
		self.platform = platform
		CommonView.__init__(self, 'Add %s Channel' % platform)

	def showHook(self):
		if self.platform == EMAIL:
			self.email.setlist(config.email())

	def textField(self, master, label, id, init = ''):
		row = Ui.TableRow(master)
		Ui.TextView(row, text = label)
		text = Ui.EditText(row,
			id = id,
			text = init,
			layout_weight = 1,
		)
		setattr(self, id, text)

	def body(self, master):
		table = Ui.TableLayout(
			Ui.ScrollView(master),
		)
		self.textField(table, 'Channel Name:', 'channel_name')

		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO, TWITTER):
			self.textField(table, 'App Key:', 'app_key')
			self.textField(table, 'App Secret:', 'app_secret')

		if self.platform == EMAIL:
			row = Ui.TableRow(table)
			Ui.TextView(row, text = 'Email:')
			self.email = Ui.Spinner(row,
				layout_weight = 1,
				layout_height = Ui.WRAP_CONTENT,
			)

		if self.platform in (EMAIL, RSS_RW, SQLITE):
			self.textField(table, 'User Name:', 'username')

		if self.platform in (EMAIL, ):
			self.textField(table, 'Password:', 'password')

		if self.platform in (TWITTER, ):
			self.textField(table, 'Access Key:', 'access_key')
			self.textField(table, 'Access Secret:', 'access_secret')

		if self.platform in (RSS, RSS_RW, SQLITE):
			self.textField(table, 'Url:', 'url')

		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO):
			self.textField(table, 'Callback Url:', 'callback_url')
			self.textField(table, 'Cmd Request Url:', 'cmd_request_url', '(default)')
			self.textField(table, 'Cmd Fetch Code:', 'cmd_fetch_code', '(default)')
			self.textField(table, 'Save Token File:', 'save_token_file', '(default)')

	def validate(self):
		if not self.channel_name.cget('text'):
			return False

		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO, TWITTER):
			if not self.app_key.cget('text') or not self.app_secret.cget('text'):
				return False

		if self.platform in (EMAIL, RSS_RW):
			if not self.username.cget('text'):
				return False

		if self.platform in (EMAIL, ):
			if not self.password.cget('text'):
				return False

		if self.platform in (TWITTER, ):
			if not self.access_key.cget('text') or not self.access_secret.cget('text'):
				return False

		if self.platform in (RSS, RSS_RW, SQLITE):
			if not self.url.cget('text'):
				return False

		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO):
			if not self.callback_url.cget('text') or not self.cmd_request_url.cget('text') or not self.cmd_fetch_code.cget('text') or not self.save_token_file.cget('text'):
				return False

		return True

	def apply(self):
		channel = sp.new_channel(self.platform)
		channel['channel_name'] = self.channel_name.cget('text')

		# app_key and app_secret
		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO, TWITTER):
			channel['app_key'] = self.app_key.cget('text')
			channel['app_secret'] = self.app_secret.cget('text')

		# username is optional for sqlite
		if self.platform == SQLITE and self.username.cget('text'):
			channel['username'] = self.username.cget('text')

		if self.platform == RSS_RW:
			channel['author'] = self.username.cget('text')

		if self.platform == EMAIL:
			channel['username'] = self.username.cget('text')
			mail = config.getmail(self.email.selected())
			channel['imap_host'] = mail['imap_host']
			channel['imap_port'] = int(mail['imap_port'])
			channel['smtp_host'] = mail['smtp_host']
			channel['smtp_port'] = int(mail['smtp_port'])
			channel['address'] = '%s@%s' % (self.username.cget('text'), mail['domain'])

		# password
		if self.platform in (EMAIL, ):
			channel['password'] = self.password.cget('text')

		# access_key and access_secret
		if self.platform in (TWITTER, ):
			channel['access_key'] = self.access_key.cget('text')
			channel['access_secret'] = self.access_secret.cget('text')

		# url
		if self.platform in (RSS, RSS_RW, SQLITE):
			channel['url'] = self.url.cget('text')

		# auth_info
		if self.platform in (RENREN_SHARE, RENREN_STATUS, SINA_WEIBO, TENCENT_WEIBO):
			channel['auth_info']['callback_url'] = self.callback_url.cget('text')
			channel['auth_info']['cmd_request_url'] = self.cmd_request_url.cget('text')
			channel['auth_info']['cmd_fetch_code'] = self.cmd_fetch_code.cget('text')
			channel['auth_info']['save_token_file'] = self.save_token_file.cget('text')

		self.result = channel


class PostText(CommonView):
	def __init__(self, title, init_text = ''):
		self.init_text = init_text
		CommonView.__init__(self, title)

	def body(self, master):
		self.text = Ui.EditText(master,
			text = self.init_text,
			layout_weight = 1,
			gravity = Ui.TOP,
		)

	def validate(self):
		return self.text.cget('text')

	def apply(self):
		self.result = self.text.cget('text')


class StatusList(Ui.LinearLayout):
	def __init__(self, master):
		self.all = []
		Ui.LinearLayout.__init__(self,
			master,
			layout_width = Ui.FILL_PARENT,
		)
		for s in sp.home_timeline():
			self.insert_status(s)

	def __insert_status(self, status):
		data = status.parsed
		try: text = data.title
		except: text = data.text
		Ui.TextView(self,
			text = '%s at %s' % (data.username, utc2str(data.time)),
			textColor = 'gray',
		)
		Ui.TextView(self,
			text = '   ' + text,
			clickable = Ui.TRUE,
			command = lambda s = status: self.clicked(s),
			layout_width = Ui.FILL_PARENT,
		)
		Ui.View(self,
			background = '@android:drawable/divider_horizontal_dark',
			layout_width = Ui.FILL_PARENT,
		)

	def insert_status(self, status):
		if status in self.all:
			return

		self.all.append(status)
		self.__insert_status(status)

	def refresh(self, data = None):
		for s in sp.home_timeline(2):
			self.insert_status(s)
		return True

	def clicked(self, status):
		menu = {
			'Forward': lambda s = status: self.droid.forward_status(s),
			'Reply': lambda s = status: self.droid.reply_status(s),
		}
		if status.parsed.has_key('link'):
			menu['Link'] = lambda url = status.parsed.link: Ui.Intent(Ui.ACTION_VIEW, url, categories = Ui.CATEGORY_BROWSABLE).start()
		act = Ui.pick('Status', menu.keys())
		if act:
			menu[act]()


class SNSDroid(Ui.DroidUi):
	PLATFORMS = {
		'email': EMAIL,
		'rss': RSS,
		'rss rw': RSS_RW,
		'renren share': RENREN_SHARE,
		'renren status': RENREN_STATUS,
		'sqlite': SQLITE,
		'sina weibo': SINA_WEIBO,
		'tencent weibo': TENCENT_WEIBO,
		'twitter': TWITTER,
	}
	def __init__(self):
		Ui.DroidUi.__init__(self)
		self.channel = None
		layout = Ui.LinearLayout(self,
			background = '@android:drawable/screen_background_dark',
			layout_height = Ui.FILL_PARENT,
			layout_width = Ui.FILL_PARENT,
		)
		header = Ui.LinearLayout(layout,
			background = '@android:drawable/title_bar',
			orientation = Ui.HORIZONTAL,
			layout_width = Ui.FILL_PARENT,
		)
		self.channelLabel = Ui.TextView(header,
			text = 'All',
			clickable = Ui.TRUE,
			command = self.switch_channel,
			gravity = Ui.CENTER,
			layout_weight = 1,
			layout_height = Ui.MATCH_PARENT,
			layout_marginLeft = '30dp',
		)
		Ui.ImageView(header,
			src = '@android:drawable/ic_menu_edit',
			clickable = Ui.TRUE,
			command = self.post_status,
		)
		sl = StatusList(Ui.ScrollView(layout))
		self.addOptionMenu('Add Channel', self.add_channel, icon = '@android:drawable/ic_menu_add')
		self.addOptionMenu('Refresh', sl.refresh, icon = '@android:drawable/stat_notify_sync')
		self.addOptionMenu('Help', self.show_help, icon = '@android:drawable/ic_menu_help')
		self.addOptionMenu('About', self.show_about, icon = '@android:drawable/ic_menu_info_details')

	def switch_channel(self, data = None):
		ch = list(sp.keys())
		ch.insert(0, 'All')
		channel = Ui.pick('Switch channel', ch)
		if not channel or channel == self.channel: return
		self.channel = channel != 'All' and channel or None
		self.channelLabel.config(text = channel)
		return True

	def add_channel(self, data = None):
		platform = Ui.pick('Add a channel', self.PLATFORMS.keys())
		if not platform: return
		channel = NewChannel(self.PLATFORMS[platform]).main()
		if not channel: return
		sp.add_channel(channel)
		sp.auth(channel['channel_name'])
		return True

	def get_post_text(self, title, init_text = ''):
		if not self.channel:
			Ui.message(APP, 'switch to a channel first')
			return
		if sp[self.channel].platform == RSS:
			Ui.message(APP, 'cannot post to RSS channel')
			return

		return PostText(title, init_text).main()

	def post_status(self):
		text = self.get_post_text('Post to channel %s' % self.channel)
		if text:
			sp[self.channel].update(text)

	def reply_status(self, status):
		text = self.get_post_text('Reply to This Status')
		if text:
			sp[status.ID.channel].reply(status.ID, text)

	def forward_status(self, status):
		text = self.get_post_text('Forward Status to %s' % self.channel, 'forward')
		if text:
			sp[self.channel].forward(status, text)

	def show_help(self, data = None):
		Ui.message('Help - ' + APP, '''Glossary:
Channel: where Status come from and post to.

Usage:
 * Click title bar to switch channel.
 * Click `Post' button on top-right to post new Status to current channel.
 * Press Menu button to see more.
''')

		return True
	def show_about(self, data = None):
		Ui.message('About - ' + APP, '''a android front end for snsapi

by Alex.wang(iptux7#gmail.com)''')
		return True


if __name__ == '__main__':
	import os
	os.chdir('scripts')
	try: os.chdir(APP)
	except: pass
	config = SNSGuiConfig()
	sp = SNSPocket()
	sp.load_config()
	sp.auth()
	SNSDroid().mainloop()
	sp.save_config()
