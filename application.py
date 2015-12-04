import os
import sys

sys.path.insert(1, os.path.join(os.path.abspath('.'), 'venv/lib/python2.7/site-packages'))
sys.path.append('/usr/local/google_appengine')

from flask import Flask, request, session, url_for, render_template, redirect, send_from_directory, flash
from werkzeug import secure_filename
from dropbox import session as dropbox_session, client
from config import *
from imgurpython import ImgurClient
from google.appengine.api import images
#from PIL import Image

dropbox_sess = dropbox_session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
imgurClient = ImgurClient(IMGUR_KEY, IMGUR_SECRET)

application = Flask(__name__)
#application.debug = True
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
application.secret_key = "SaltySalt"


# Landing Page
@application.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@application.route('/FAQ')
def faq():
    return render_template('faq.html')


@application.route('/About')
def about():
    return render_template('about.html')

@application.route('/custom/<text>')
def custom(text):
    return render_template('custom.html', text = text)

@application.route('/login')
def login():
    return  redirect(url_for('authorize_dropbox'))

@application.route('/logout')
def logout():
    del session['dropbox_reqtock']
    del session['name']
    del session['access_token']
    global dropbox_sess
    dropbox_sess =  dropbox_session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    return redirect(url_for('index'))

#The first step in the process.
@application.route('/authorize/dropbox/')
def authorize_dropbox():
  	callback =  url_for('dropbox_authorized',_external=True)
	#first step of OAuth
	request_token = dropbox_sess.obtain_request_token()
	#Save the request token. It will be needed to obtain the acess tokens
	#Do not try to save whole OAuthToken object. It will fail ;)
	session['dropbox_reqtock'] = {
		'oauth_token' :request_token.key,
		'oauth_token_secret':request_token.secret
	};
	#Second stept of OAuth

	url = dropbox_sess.build_authorize_url(request_token, oauth_callback=callback)
	return redirect(url)

# After user login and authorization, dropbox will redirect to this url.
@application.route('/authorize/dropbox/oauth-authorized')
def dropbox_authorized():
    next_url = url_for('index')
    if request.args.get('not_approved'):
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    else:
        request_token_dic = session['dropbox_reqtock'];
        request_token = dropbox_session.OAuthToken(request_token_dic.get('oauth_token'),
                                                   request_token_dic.get('oauth_token_secret'))
        #session.pop('dropbox_reqtock', None)
        # Last step of OAuth
        access_token = dropbox_sess.obtain_access_token(request_token);
        # save acess_tokens
        session["access_token"] = {
            #"access_token" : access_token,
            'key': access_token.key,
            'secret': access_token.secret,
        }
        #minha linha
        dropbox_sess.set_token(access_token.key, access_token.secret)
        cliente = client.DropboxClient(dropbox_sess)
        session["name"] = cliente.account_info()
    return redirect(next_url)

@application.route('/images/', methods=['GET', 'POST'])
def search_images():
    #return render_template("resize.html")
    if request.method == 'POST':
        index = request.form['search'].lower()
        search_results = getFromDB(index)
        return render_template("search_results.html", search_results = search_results )
        #return request.form['search']
        #cliente = client.DropboxClient(dropbox_sess)
        #resp = ""
        #d = cliente.account_info()
        #for p in d:
        #    resp += str(d[p])+ '\n'
        #return resp
        #return str(application.config)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['attachmentName']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))

        if request.form.get('index') == 'on':
            imgurResponse = imgurClient.upload_from_path(os.path.join(application.config['UPLOAD_FOLDER'], filename))
            urls = [ imgurResponse['link']]
            # return redirect(url_for('index_images', urls=urls))
            return render_template('index_images.html', urls = urls, filename=filename)

            #return str(response)
        return render_template("resize.html", filename=filename )

@application.route('/index_images', methods = [ 'GET', 'POST'])
def index_images():
    if request.method == 'POST':
        for url in request.form:
            if url != 'filePath':
                addtoDB(request.form[url].lower(), url)
        return render_template("resize.html", filename=request.form['filename'] )

# @application.route('/process_images', methods = ['GET', 'POST'])
# def process_images():
#     if request.method == 'POST':
#         newWidth = int(request.form['width'])
#         newHeigth = int(request.form['height'])
#         currentFileName  = request.form['filename']
#         newFormat = request.form['format']
#         newFileName = ""
#         for i in range(len(currentFileName.split('.'))-1 ):
#             newFileName =  newFileName + currentFileName.split('.')[i] + '.'
#         newFileName = newFileName + newFormat
#         img = Image.open(os.path.join(application.config['UPLOAD_FOLDER'], currentFileName))
#         img = img.resize( (newWidth, newHeigth), Image.ANTIALIAS )
#         img.save(os.path.join(application.config['UPLOAD_FOLDER'], newFileName))
#         return final_upload(newFileName)

@application.route('/process_images', methods = ['GET', 'POST'])
def process_images():
    if request.method == 'POST':
        pass
        #from google.appengime.api import images
        # newWidth = int(request.form['width'])
        # newHeigth = int(request.form['height'])
        # currentFileName  = request.form['filename']
        # newFormat = request.form['format']
        # newFileName = ""
        # for i in range(len(currentFileName.split('.'))-1 ):
        #     newFileName =  newFileName + currentFileName.split('.')[i] + '.'
        # newFileName = newFileName + newFormat
        # img = Image.open(os.path.join(application.config['UPLOAD_FOLDER'], currentFileName))
        # img = img.resize( (newWidth, newHeigth), Image.ANTIALIAS )
        # img.save(os.path.join(application.config['UPLOAD_FOLDER'], newFileName))
        # return final_upload(newFileName)

def final_upload(filename):
    if "access_token" in session:
        cliente = client.DropboxClient(dropbox_sess)
        f = open(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        response = cliente.put_file("/"+filename, f)
        return custom("Finished")

@application.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(application.config['UPLOAD_FOLDER'], filename)


# Using Cookies
# from flask import make_response, request
#
# @application.route('/')
# def index():
#   username = request.cookies.get('username')
# from flask import make_response
#
# @application.route('/')
# def index():
#    resp = make_response(render_template(...))
#    resp.set_cookie('username', 'the username')
#    return resp

# Passing Parameters
# @application.route('/user/<username>')
# def show_user_profile(username):
#    return 'User %s' % username#
#
# @application.route('/post/<int:post_id>')
# def show_post(post_id):
#    return 'Post %d' % post_id

def addtoDB(index, url):
    import json
    file = open('db.json', 'r')
    data = file.read()
    file.close()
    db = json.loads(data)
    if index not in db:
        db[index] = [url]
    else:
        db[index].append(url)
    json_str = json.dumps(db)
    file = open('db.json', 'w')
    file.write(json_str)
    file.close()

def getFromDB(index):
    import json
    file = open('db.json', 'r')
    data = file.read()
    db = json.loads(data)
    file.close()
    if index not in db:
        return []
    else:
        return db[index]

if __name__ == '__main__':
   #application.run(host='0.0.0.0', port=13477)
    application.run()
