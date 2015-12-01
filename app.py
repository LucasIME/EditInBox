from flask import Flask, request, session, url_for, render_template, redirect, send_from_directory, flash
from flask_oauth import OAuth
from werkzeug import secure_filename
from dropbox import session as dropbox_session, client
import os
from config import *
from imgurpython import ImgurClient

dropbox_sess = dropbox_session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
imgurClient = ImgurClient(IMGUR_KEY, IMGUR_SECRET)

app = Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = "SaltySalt"


# Landing Page
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/FAQ')
def faq():
    return render_template('faq.html')


@app.route('/About')
def about():
    return render_template('about.html')

@app.route('/custom/<text>')
def custom(text):
    return render_template('custom.html', text = text)

@app.route('/login')
def login():
    return  redirect(url_for('authorize_dropbox'))

@app.route('/logout')
def logout():
    del session['dropbox_reqtock']
    del session['name']
    del session['access_token']
    global dropbox_sess
    dropbox_sess =  dropbox_session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    return redirect(url_for('index'))

#The first step in the process.
@app.route('/authorize/dropbox/')
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
@app.route('/authorize/dropbox/oauth-authorized')
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

@app.route('/images/', methods=['GET', 'POST'])
def search_images():
    if request.method == 'POST':
        index = request.form['search']
        search_results = getFromDB(index)
        return render_template("search_results.html", search_results = search_results )
        #return request.form['search']
        #cliente = client.DropboxClient(dropbox_sess)
        #resp = ""
        #d = cliente.account_info()
        #for p in d:
        #    resp += str(d[p])+ '\n'
        #return resp
        #return str(app.config)


@app.route('/index_images')
def index_images():
    pass


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['attachmentName']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

     #        config = {
	# 	'name':  'Catastrophe!',
	# 	'title': 'Catastrophe!',
	# 	'description': 'Cute kitten being cute'
	# }
            #imgurResponse = imgurClient.upload_from_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #addtoDB(index, imgurResponse['link'])
            #return str(imgurResponse)
            if session["access_token"]:
                cliente = client.DropboxClient(dropbox_sess)
                f = open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                response = cliente.put_file("/"+filename, f)
                #return str(response)

        if request.form.get('index') == 'on':
            filenames = [filename]
            return redirect(url_for('index_images', filenames=filenames))
        else:
            return custom('Finished')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Using Cookies
# from flask import make_response, request
#
# @app.route('/')
# def index():
#   username = request.cookies.get('username')
# from flask import make_response
#
# @app.route('/')
# def index():
#    resp = make_response(render_template(...))
#    resp.set_cookie('username', 'the username')
#    return resp

# Passing Parameters
# @app.route('/user/<username>')
# def show_user_profile(username):
#    return 'User %s' % username#
#
# @app.route('/post/<int:post_id>')
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
    app.run(host='0.0.0.0', port=13477)
