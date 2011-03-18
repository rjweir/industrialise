from industrialise import browser

username = 'username'
password = 'password'

b = browser.Browser()
b.go("http://slashdot.org/")
b.follow("Log In")
form = b.forms[2]
form.fields['unickname'] = username
form.fields['upasswd'] = password
b.submit(form, extra_values={'userlogin': 'Log in'})
assert "~" + username in b.contents
