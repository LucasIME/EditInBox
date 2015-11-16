from flask import Flask, request, url_for, render_template

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('a.html')



@app.route('/hello', methods = ['GET', 'POST'])
def hello():
    if request.method =="GET":
        return "Hello GET World"
    else:
        request.
        #return "Hello POST World"


@app.route('/user/<username>')
def show_user_profile(username):
    return 'User %s' % username


@app.route('/post/<int:post_id>')
def show_post(post_id):
    return 'Post %d' % post_id


@app.route('/login/')
@app.route('/login/<name>')
def login(name=None):
    return render_template('a.html', name=name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=13477)
