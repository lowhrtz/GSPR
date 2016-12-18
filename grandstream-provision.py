import os
import re
import sqlite3
import MySQLdb as mysql
from urlparse import parse_qs

SQLITE_DB = os.path.join(os.path.dirname(__file__), 'gspr.db')

def get_style():
    style_string = '''\
<title>Grandstream Provision</title>
<style>
body {
  background: #234879;
  color: #fefefd;
}

.clear {
  clear: both;
}

div {
  text-align: center;
}

div.header {
  font-size: 40px;
  color: #66b4ce;
}

div.info {
  line-height: 300%;
}

div.bordered {
  border: 3px solid #66b4ce;
  border-radius: 25px;
  padding: 20px 0px;
}

#phone-list {
}

div.phone-list-item {
  border: 1px solid #fefefd;
  border-radius: 25px;
  margin: 10px auto;
  width: 30%;
}
</style>
'''
    return style_string

def is_config_request(path_info):
    m = r'^/cfg[0-9a-f]{12}\.xml$'
    return re.match(m, path_info)

def get_index(db):
    string_format = {
        'style':get_style(),
        'base_dir':BASE_URL_DIRECTORY,
    }
    html_string = '''\
<head>
{style}
</head>
<body>
<div class="header">Grandstream Provisioner</div>
<div class="info">
Enter admin password<br />
<form action="{base_dir}/admin" method="POST">
Password: <input type="password" id="pwd" name="pwd" autofocus required><br />
</form>
</div>
</body>
'''.format(**string_format)
    return html_string

def get_admin(db):
    c = db.execute('SELECT * FROM settings')
    settings = c.fetchone()
    html_string = '<head>{style}'.format(style=get_style())
    html_string += '''
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
<script type="text/javascript">
function list_phones() {
  $("#phone-list").empty();
  $("#phone-list").load("phone-list");
}

function delete_map_entry(ext) {
  ret = confirm("Are you sure you want to delete extension " + ext + "?");
  if(ret == true) {
    $("#phone-list-message-area").empty();
    $("#phone-list-message-area").load("delete-map-entry", {'extension':ext});
    list_phones();
  }
}

function select_radio(selected, sibling) {
  if(sibling.startsWith("#ext_")) {
    $("[id^='ext_']").prop("disabled", false);
  } else if (sibling.startsWith("#mac_")) {
    $("[id^='mac_']").prop("disabled", false);
  }
  $(sibling).prop("disabled", true);
}

$(document).ready(function(){
  list_phones();

  $("#add-phone").click(function (){
    $("#phone-add-message-area").empty();
    $("#phone-add-message-area").load("add-phone", {'extension':$("#extension").val(),'mac':$("#mac").val()});
    $("#extension").val("");
    $("#mac").val("");
    setTimeout(list_phones, 500);
  });

  $("input:radio").select(function (){
    alert('Fire!');
    $(this).siblings().prop("disabled", true);;
  });

  $("#save-set-change").click(function (){
    $("#edit-settings-message-area").empty();
    $("#edit-settings-message-area").load("edit-settings", 
    {
    'phone_server':$("#phone_server").val(),
    'phone_admin':$("#phone_admin").val(),
    'ntp_server':$("#ntp_server").val(),
    'phonebook_url':$("#phonebook_url").val(),
    'mysql_host':$("#mysql_host").val(),
    'mysql_user':$("#mysql_user").val(),
    'mysql_pass':$("#mysql_pass").val(),
    'mysql_db':$("#mysql_db").val(),
    'static_folder':$("#static_folder").val(),
    'wallpaper_server':$("#wallpaper_server").val(),
    'city_code':$("#city_code").val(),
    'time_zone':$("#time_zone").val(),
    });
  });

});
</script>
'''
    string_format = {
        'base_dir':BASE_URL_DIRECTORY,
        'phone_server':settings[2],
        'phone_admin':settings[3],
        'ntp_server':settings[4],
        'phonebook_url':settings[5],
        'mysql_host':settings[6],
        'mysql_user':settings[7],
        'mysql_pass':settings[8],
        'mysql_db':settings[9],
        'static_folder':settings[10],
        'wallpaper_server':settings[11],
        'city_code':settings[12],
        'time_zone':settings[13],
    }
    html_string += '''\
</head>
<div class="header">Administer Provisioning</div>
<div class="info">
Available Options<br />
<div class="bordered">
<div id="phone-add-message-area"></div>
Extension: <input id="extension" name="extension" required> &nbsp;&nbsp;MAC: <input id="mac" name="mac" required><br />
<input type="button" id="add-phone" value="Associate a Phone with Account">
</div><br />
<div class="bordered">
<div id="phone-list-message-area"></div>
<div id="phone-list"></div><div class="clear"><button>Switch Phones</button></div>
</div><br /><br />
<div class="bordered">
<div id="edit-settings-message-area"></div>
<div id="settings">
Phone Server: <input id="phone_server" name="phone_server" value="{phone_server}" required><br />
Phone Admin: <input id="phone_admin" name="phone_admin" value="{phone_admin}" required><br />
Phonebook URL: <input id="phonebook_url" name="phonebook_url" value="{phonebook_url}" required><br />
NTP Server: <input id="ntp_server" name="ntp_server" value="{ntp_server}" required><br />
MySQL Host: <input id="mysql_host" name="mysql_host" value="{mysql_host}" required><br />
MySQL User: <input id="mysql_user" name="mysql_user" value="{mysql_user}" required><br />
MySQL Pass: <input id="mysql_pass" name="mysql_pass" value="{mysql_pass}" required><br />
MySQL DB: <input id="mysql_db" name="mysql_db" value="{mysql_db}" required><br />
Static Folder: <input id="static_folder" name="static_folder" value="{static_folder}" required><br />
Wallpaper Server: <input id="wallpaper_server" name="wallpaper_server" value="{wallpaper_server}" required><br />
City Code: <input id="city_code" name="city_code" value="{city_code}" required><br />
Time Zone: <input id="time_zone" name="time_zone" value="{time_zone}" required><br />
<button id="save-set-change">Save Setting Changes</button>
</div></div>
<br /><a href="{base_dir}"><button>Logout</button></a>
</div>
'''.format(**string_format)
    return html_string

def get_config(path_info):
    mac = path_info[4:-4]
    settings = ()
    extension = None
    name = None
    secret = None
    try:
        db = sqlite3.connect(SQLITE_DB)
        c = db.execute('SELECT * FROM settings')
        settings = c.fetchone()
    except IOError:
        return 'Problem loading db file.'
    except sqlite3.OperationalError:
        return 'Database has not been set up yet. Run the setup from a web browser.'

    try:
        c = db.execute('SELECT extension FROM ext_mac_map WHERE mac=?', (mac,))
        extension = c.fetchone()[0]
    except IOError:
        return 'Problem loading db file.'
    except sqlite3.OperationalError:
        return 'ext_mac_map table missing. App Sqlite database is most likely corrupted.'
    except TypeError:
        return 'Phone has not been added to the db yet.'

    try:
        ast_db = mysql.connect(host=settings[6],
                       user=settings[7],
                       passwd=settings[8],
                       db=settings[9])

        db_cursor = ast_db.cursor()
        db_cursor.execute("SELECT data FROM sip WHERE id=%s AND keyword='secret'", (extension,))
        secret_rec = db_cursor.fetchone()
        secret = secret_rec[0]
        db_cursor.execute("SELECT name FROM users WHERE extension=%s", (extension,))
        name_rec = db_cursor.fetchone()
        name = name_rec[0]
    except IOError:
        return 'Problem connecting to the Freepbx Mysql DB.'
    string_format = {
        'mac':mac,
        'extension':extension,
        'name':name,
        'secret':secret,
        'server_address':settings[2],
        'phone_admin':settings[3],
        'ntp_server':settings[4],
        'phonebook_url':settings[5],
        'wallpaper_server':settings[11],
        'city_code':settings[12],
        'time_zone':settings[13],
    }
    config = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<gs_provision version="1">
<mac>{mac}</mac>
  <config version="1">
<!--####################################################################-->
<!--# Account Active. 0 - No, 1 - Yes. Default value is 0-->
<!--# Number: 0, 1-->
    <P271>1</P271>

<!--# Account Name-->
    <P270>{name}</P270>
    <P4180>{name}</P4180>

<!--# SIP Server-->
    <P47>{server_address}</P47>

<!--# SIP User ID-->
    <P35>{extension}</P35>
    <P4060>{extension}</P4060>

<!--# SIP Authenticate ID-->
    <P36>{extension}</P36>
    <P4090>{extension}</P4090>

<!--# SIP Authenticate Password-->
    <P34>{secret}</P34>
    <P4120>{secret}</P4120>

<!--# Admin password-->
    <P2>{phone_admin}</P2>

<!--# Name (Display Name, e.g., John Doe)-->
    <P3>{name}</P3>
    <P27020>{name}</P27020>

<!--# NTP Server-->
    <P30>{ntp_server}</P30>

<!--# Time Zone-->
    <P64>{time_zone}</P64>

<!--# Voice Mail UserID-->
    <P33>*97</P33>

<!--# Auto Answer. 0 - No, 1 - Yes-->
    <P90>0</P90>

<!--# Allow Auto Answer by Call-Info. 0 - No, 1 - Yes-->
    <P298>1</P298>

<!--# Enable Phonebook XML Download-->
    <P330>3</P330>

<!--# Phone Book XML Server Path-->
    <P331>{phonebook_url}</P331>

<!--# Phonebook Download Interval-->
    <P332>60</P332>

<!--# Remove Manually-edited entries on Download-->
    <P333>0</P333>

<!--# Phonebook Key Function-->
    <P1526>2</P1526>

<!--# Weather Update-->
<!--# Enable weather update. 0 - No, 1 - Yes. Default is 1-->
    <P1402>1</P1402>

<!--# City Code-->
<!--# 0 - Use Self-Defined City Code, 1 - Automatic. Default is 1-->
<!--# Number: 0, 1-->
    <P1405>0</P1405>

<!--# Self-Defined City Code-->
<!--# String-->
    <!--<P1377>USFL0479</P1377>-->
    <P1377>{city_code}</P1377>

<!--# Date Display Format-->
<!--# 0: yyyy-mm-dd  eg. 2011-10-31-->
<!--# 1: mm-dd-yyyy eg. 10-31-2011-->
<!--# 2: dd-mm-yyyy eg. 31-10-2011-->
<!--# 3: dddd, MMMM dd eg. Monday, October 31-->
<!--# 4: MMMM dd, dddd eg. October 31, Monday-->
    <P102>3</P102>

<!--# Virtual Multi-Purpose Keys-->
<!--# VPK Mode. 0 - Advanced, 1 - Traditional. Default is 0-->
    <P8369>0</P8369>

<!--# Show Label Background. 0 - No, 1 - Yes. Default is 0-->
    <P8345>0</P8345>

<!--# Use Long Label. 0 - No, 1 - Yes. Default is 0-->
    <P8346>1</P8346>

<!--# Wallpaper Settings-->
<!--# Wallpaper Source. O - Default, 1 - Download, 2 - USB, 3 - Uploaded-->
    <P2916>1</P2916>

<!--# Wallpaper Server Path-->
    <P2917>{wallpaper_server}</P2917>

<!--# Dial Plan. Default value is {{ x+ | \+x+ | *x+ | *xx*x+ }}-->
    <P290>{{ x+ | \\+x+ | *x+ | *xx*x+ | *1x }}</P290>

<!--####################################################################-->
  </config>
</gs_provision>
'''.format(**string_format)
    return config

def get_setup():
    string_format = {
        'style':get_style(),
        'base_dir':BASE_URL_DIRECTORY,
    }
    html_string = '''\
<html>
<head>
{style}
</head>
<body>
<div class="header">Intial Setup</div>
<div class="info">
This appears to be your first time running this application.<br />
Fill in the fields to get started.<br />
<form action="{base_dir}/submit-setup" method="post">
Admin Username: <input id="user" name="user" required><br />
Set Password: <input type="password" id="pw1" name="pw1" required><br />
Confirm Pwd: <input type="password" id="pw2" name="pw2" required><br />
Phone Server: <input id="phone_server" name="phone_server" required><br />
MySQL Host: <input id="mysql_host" name="mysql_host" value="localhost" required><br />
MySQL User: <input id="mysql_user" name="mysql_user" required><br />
MySQL Pass: <input id="mysql_pass" name="mysql_pass" required><br />
MySQL DB: <input id="mysql_db" name="mysql_db" value="asterisk" required><br />
Static Folder: <input id="static_folder" name="static_folder" value="/var/www/static_files" required><br />
<input type="submit" value="Submit"><br />
<form>
</div>
</body>
</html>
'''.format(**string_format)
    return html_string

def submit_setup(post_input, db):
    return_string = '<div class="header">{message}</div><div><a href="{base_dir}"><button>Back to Main Page</button></a></div>'
    message = 'Setup Successful!'

    user = post_input.get('user', [''])[0]
    pw1 = post_input.get('pw1', [''])[0]
    pw2 = post_input.get('pw2', [''])[0]
    phone_server = post_input.get('phone_server', [''])[0]
    mysql_host = post_input.get('mysql_host', [''])[0]
    mysql_user = post_input.get('mysql_user', [''])[0]
    mysql_pass = post_input.get('mysql_pass', [''])[0]
    mysql_db = post_input.get('mysql_db', [''])[0]
    static_folder = post_input.get('static_folder', [''])[0]
    if pw1 != pw2 or not user or not pw1 or not phone_server or not mysql_host or not mysql_user or not mysql_pass or not mysql_db:
        message = 'Problem Getting Submitted Data!'
    else:
        phone_admin = 'admin'
        ntp_server = phone_server
        phonebook_url = '{}/phonebook'.format(phone_server)
        wallpaper_server = 'https://{server}/gspr/'.format(server=phone_server)
        city_code = '32317'
        time_zone = 'EST5EDT'
        db.execute('CREATE TABLE settings (user TEXT, password TEXT, phone_server TEXT, phone_admin TEXT, ntp_server TEXT, phonebook_url TEXT, mysql_host TEXT, mysql_user TEXT, mysql_pass TEXT, mysql_db TEXT, static_folder TEXT, wallpaper_server TEXT, city_code TEXT, time_zone TEXT)')
        db.execute('CREATE TABLE ext_mac_map (extension TEXT, mac TEXT)')
        db.execute('INSERT INTO settings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (user, pw1, phone_server, phone_admin, ntp_server, phonebook_url, mysql_host, mysql_user, mysql_pass, mysql_db, static_folder, wallpaper_server, city_code, time_zone))
        db.execute('UPDATE settings set time_zone=?', (time_zone, ))
        db.commit()
        db.close()
    return return_string.format(base_dir=BASE_URL_DIRECTORY, message=message)

def add_phone(post_input):
    extension = post_input.get('extension', [''])[0]
    mac = post_input.get('mac', [''])[0]
    if not extension or not mac:
        return '<div class="header">Problem processing request!{a}</div>'.format(a=post_input.keys())
    try:
        db = sqlite3.connect(SQLITE_DB)
        extension_exists = False
        mac_exists = False
        for row in db.execute('SELECT extension, mac FROM ext_mac_map'):
            if extension in row:
                extension_exists = True
            if mac in row:
                mac_exists = True
        if extension_exists and not mac_exists:
            return '<div class="header">Extension Already Associated with a Phone!</div>'
        if mac_exists and not extension_exists:
            return '<div class="header">Phone Already Associated with an Extension!</div>'
        if extension_exists and mac_exists:
            return '<div class="header">Both Extension and Phone Already in DB!</div>'

        db.execute('INSERT INTO ext_mac_map VALUES (?,?)', (extension, mac))
        db.commit()
        db.close()
    except sqlite3.OperationalError:
        return '<div class="header">Problem adding phone to app db!</div>'

    return '<div class="header">Phone Added!</div>'

def phone_list():
    html_string = ''
    try:
        db = sqlite3.connect(SQLITE_DB)
        c = db.execute('SELECT * from ext_mac_map ORDER BY extension')
        for row in c:
            extension = row[0]
            mac = row[1]
            html_string += '''\
<div class="phone-list-item">
<input type="radio" name="switch_extension" id="ext_{extension}" onclick="select_radio('#ext_{extension}', '#mac_{mac}')" /><label for="ext_{extension}" onclick="select_radio('#ext_{extension}', '#mac_{mac}')">{extension}</label> &nbsp;&nbsp;&nbsp;
<input type="radio" name="switch_mac" id="mac_{mac}" onclick="select_radio('#mac_{mac}', '#ext_{extension}')" /><label for="mac_{mac}" onclick="select_radio('#mac_{mac}', '#ext_{extension}')">{mac}</label>
<button id="delete_ext_{extension}" onclick="delete_map_entry('{extension}')">Delete</button></div>
'''.format(extension=extension,mac=mac)
    except sqlite3.OperationalError:
        html_string = '<div class="header">Problem with the databse. May be corrupted!</div>'
    db.close()
    return html_string

def delete_map_entry(post_input):
    extension = post_input.get('extension', [''])[0]
    html_string = ''
    try:
        db = sqlite3.connect(SQLITE_DB)
        db.execute('DELETE FROM ext_mac_map WHERE extension=?', (extension,))
        db.commit()
        html_string = '<div class="header">Extension {extension} Deleted'.format(extension=extension)
    except sqlite3.OperationalError:
        html_string = '<div class="header">Problem with the database. May be corrupted!</div>'
    db.close()
    return html_string

def edit_settings(post_input):
    phone_server = post_input.get('phone_server', [''])[0]
    phone_admin = post_input.get('phone_admin', [''])[0]
    phonebook_url = post_input.get('phonebook_url', [''])[0]
    ntp_server = post_input.get('ntp_server', [''])[0]
    mysql_host = post_input.get('mysql_host', [''])[0]
    mysql_user = post_input.get('mysql_user', [''])[0]
    mysql_pass = post_input.get('mysql_pass', [''])[0]
    mysql_db = post_input.get('mysql_db', [''])[0]
    static_folder = post_input.get('static_folder', [''])[0]
    wallpaper_server = post_input.get('wallpaper_server', [''])[0]
    city_code = post_input.get('city_code', [''])[0]
    time_zone = post_input.get('time_zone', [''])[0]
    try:
        db = sqlite3.connect(SQLITE_DB)
        db.execute('UPDATE settings SET phone_server=?, phone_admin=?, phonebook_url=?, ntp_server=?, mysql_host=?, mysql_user=?, mysql_pass=?, mysql_db=?, static_folder=?, wallpaper_server=?, city_code=?, time_zone=?',
           (phone_server, phone_admin, phonebook_url, ntp_server, mysql_host, mysql_user, mysql_pass, mysql_db, static_folder, wallpaper_server, city_code, time_zone))
        db.commit()
        html_string = '<div class="header">Settings Updated!</div>'
    except sqlite3.OperationalError:
        html_string = '<div class="header">Problem with the database. May be corrupted!</div>'
    db.close()
    return html_string

def application(environ,start_response):
    status_OK = '200 OK'
    status_Forbidden = '403 Forbidden'
    status_Not_Found = '404 Not Found'
    status_REDIRECT = '302 Found'

    response_header = [('Content-type','text/html')]

    global BASE_URL_DIRECTORY
    BASE_URL_DIRECTORY = environ.get('SCRIPT_NAME','')
    path_info = environ.get('PATH_INFO', '')
    request_method = environ.get('REQUEST_METHOD', '')
    #query_string = environ.get('QUERY_STRING', '')
    #parsed_query = parse_qs(query_string, True)
    raw_post = environ.get('wsgi.input', '')
    post_input = parse_qs(raw_post.readline().decode(),True)

    status = status_OK
    html_string = ''

    #html_string = path_info
    if path_info == '' or path_info == '/':
        try:
           db = sqlite3.connect(SQLITE_DB)
           db.execute('SELECT * FROM settings')
           html_string = get_index(db)
           db.close()
        except IOError:
           db.close()
           html_string = 'Problem with database!'
        except sqlite3.OperationalError:
           #db.close()
           html_string = get_setup()

    elif path_info == "/admin":
        html_string = '<head>{style}</head>'.format(style=get_style())
        if request_method != 'POST':
            status = status_REDIRECT
            response_header = [('Location', BASE_URL_DIRECTORY)]
        else:
            try:
                db = sqlite3.connect(SQLITE_DB)
                c = db.execute('SELECT password FROM settings')
                password = c.fetchone()[0]
                pwd = post_input.get('pwd', [''])[0]
                if password != pwd:
                    status = status_Forbidden
                    html_string += '<div class="header">Wrong Password</div><div><a href="{base_dir}"><button>Back to Main Page</button></a></div>'.format(base_dir=BASE_URL_DIRECTORY)
                else:
                    html_string = get_admin(db)
                db.close()
            except IOError:
                db.close()
                html_string += '<div class="header">Problem with database!</div>'
            except sqlite3.OperationalError:
                html_string += submit_setup(post_input, db)
                db.close()

    elif path_info == "/add-phone":
        if request_method != 'POST':
            status = status_REDIRECT
            response_header = [('Location', BASE_URL_DIRECTORY)]
        else:
            html_string = add_phone(post_input)

    elif path_info == '/phone-list':
        html_string = phone_list()

    elif path_info == '/delete-map-entry':
        if request_method != 'POST':
            status = status_REDIRECT
            response_header = [('Location', BASE_URL_DIRECTORY)]
        else:
            html_string = delete_map_entry(post_input)

    elif path_info == '/edit-settings':
        html_string = '<head>{style}</head>'.format(style=get_style())
        if request_method != 'POST':
            status = status_REDIRECT
            response_header = [('Location', BASE_URL_DIRECTORY)]
        else: 
            html_string += edit_settings(post_input)

    elif path_info == "/submit-setup":
        html_string = '<head>{style}</head>'.format(style=get_style())
        if request_method != 'POST':
            status = status_REDIRECT
            response_header = [('Location', BASE_URL_DIRECTORY)]
        else: 
            try:
                db = sqlite3.connect(SQLITE_DB)
                db.execute('SELECT * FROM settings')
                db.close()
                html_string += '<div class="header">Database alread set up!</div>'
            except IOError:
                db.close()
                html_string += '<div class="header">Problem with database!</div>'
            except sqlite3.OperationalError:
                html_string += submit_setup(post_input, db)
                db.close()

    elif is_config_request(path_info):
        response_header = [('Content-type','text/xml')]
        html_string = get_config(path_info)

    elif path_info.endswith('.bin'):
        filename = path_info.replace('/', '')
        try:
            db = sqlite3.connect(SQLITE_DB)
            c = db.execute('SELECT static_folder FROM settings')
            static_folder = c.fetchone()[0]
            path = os.path.join(static_folder, filename)
            if os.path.exists(path):
                response_header = [('content-type', 'application/octet-stream')]
                f = open(path, 'rb')
                html_string = f.read()
                f.close()
            else:
                html_string = '404 Not Found'
                status = status_Not_Found
            db.close()
        except sqlite3.OperationalError:
            db.close()
            html_string = '404 Not Found'
            status = status_Not_Found

    elif path_info.endswith('.jpg'):
        filename = path_info.replace('/', '')
        try:
            db = sqlite3.connect(SQLITE_DB)
            c = db.execute('SELECT static_folder FROM settings')
            static_folder = c.fetchone()[0]
            path = os.path.join(static_folder, filename)
            if os.path.exists(path):
                response_header = [('content-type', 'image/jpeg')]
                f = open(path, 'rb')
                html_string = f.read()
                f.close()
            else:
                html_string = '404 Not Found'
                status = status_Not_Found
            db.close()
        except sqlite3.OperationalError:
            db.close()
            html_string = '404 Not Found'
            status = status_Not_Found

    else:
        html_string = '404 Not Found'
        status = status_Not_Found

    start_response(status, response_header)
    return [html_string]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()
