"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

import os, datetime
from .settings import APP_FOLDER
from py4web import action, request, abort, redirect, URL, response
from yatl.helpers import A, TAG, XML
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from .wf_functions import splitter, splitter_urlify, MARKMIN
from pydal._compat import to_native, to_bytes, to_unicode


FORCE_RENDER = False
TIME_EXPIRE = -1
FORCE_RENDER = True


def get_folders(dummy=None):
    folder = os.path.join(APP_FOLDER, 'content')
    print(folder)
    return folder, [f for f in os.listdir(folder)
                    if os.path.isdir(os.path.join(folder, f))]


FOLDER, FOLDERS = get_folders()

def get_subfolder(book_id):
    if not book_id:
        redirect(URL('index'))
    for f in FOLDERS:
        if f.startswith(book_id):
            return f
    redirect(URL('index'))


def get_info(subfolder):
    infofile = os.path.join(FOLDER, subfolder, 'info.txt')
    if os.path.exists(infofile):
        info = dict(splitter(line)
                    for line in open(infofile, 'rt',  encoding='utf-8').readlines()
                    if ':' in line)
        return info
    return {}


def get_chapters(subfolder):
    filename = os.path.join(FOLDER, subfolder, 'chapters.txt')
    print(filename)
    chapters = [splitter_urlify(line)
                for line in open(filename, 'rt',  encoding='utf-8').readlines()
                if ':' in line]
    print(chapters)
    return chapters



def build_menu(dummy=None):
    menu = []
    submenu = []
    for subfolder in FOLDERS:
        info = get_info(subfolder)
        book_id = subfolder.split('-')[0]
        submenu.append((info['title'] + ' ' + info['language'], None, URL('chapter', args=book_id)))
    menu.append(('Books', None, '#', submenu))
    menu.append(('Contribute', None, 'https://github.com/web2py/web2py-book'))
    return menu

# Below doesn't work think web2py dependency
#response.menu = build_menu()


def convert2html(book_id, text):
    extra = {}

    def url2(*a, **b):
        b['args'] = [book_id] + b.get('args', [])
        return URL(*a, **b)

    #def truncate(x):
    #    return x[:70] + '...' if len(x) > 70 else x

    extra['verbatim'] = lambda code: to_native(cgi.escape(code))
    extra['cite'] = lambda key: to_native(TAG.sup(
        '[', A(key, _href=URL('reference', args=(book_id, key)),
               _target='_blank'), ']').xml())
    extra['inxx'] = lambda code: to_native('<div class="inxx">' + code + '</div>')
    extra['ref'] = lambda code: to_native('[ref:' + code + ']')
    # extra['code'] = lambda code: CODE(code, language='web2py').xml()
    #try:
    from .hladapter import hladapter
    #except ImportError:
    #    redirect(URL('index', vars=dict(FLASH_MSG = 'ImportError')))
    extra['code'] = hladapter

    # NOTE: pass id_prefix='' to preserve anchor names in urls,
    #       is there any reason to have the insane 'markmin_' default value ?
    rtn = MARKMIN(text.replace('\r', ''), extra=extra, url=url2, id_prefix='')
    return rtn





def calc_date(now=datetime.datetime.utcnow()):
    # if you are changing sources often remove the
    # comment from the next 2 lines
    # import datetime
    # now = now + datetime.timedelta(days=1)
    format = '%a, %d %b %Y 23:59:59 GMT'
    return now.strftime(format)



@action("chapter", method=['GET', 'POST'])
@action("chapter/<book_id>", method=['GET', 'POST'])
@action("chapter/<book_id>/<chapter_id>", method=['GET', 'POST'])
@action.uses("chapter.html")
def chapter(book_id=None, chapter_id="1"):
    chapter_id = int(chapter_id) if chapter_id and chapter_id.isnumeric() else 1
    subfolder = get_subfolder(book_id)
    #info = cache.ram('info_%s' % subfolder, lambda: get_info(subfolder), time_expire=TIME_EXPIRE)
    info = ('info_%s' % subfolder, get_info(subfolder))
    #chapters = cache.ram('chapters_%s' % subfolder, lambda: get_chapters(subfolder), time_expire=TIME_EXPIRE)
    chapters = ('chapters_%s' % subfolder, get_chapters(subfolder))
    print(chapters)
    print('id', chapter_id)
    chapter_title = chapters[1][chapter_id-1][1]
    title = '%s - %s' % (info[1]['title'], to_unicode(chapter_title))
    filename = os.path.join(FOLDER, subfolder, '%.2i.markmin' % chapter_id)
    print(filename)
    dest = os.path.join(FOLDER, 'static_chaps', subfolder, '%.2i.html' % chapter_id)
    print('got here')
    if not FORCE_RENDER:
        response.headers['Cache-Control'] = 'public, must-revalidate'
        response.headers['Expires'] = calc_date()
        response.headers['Pragma'] = None
    #if (not os.path.isfile(dest)) or FORCE_RENDER:
    if FORCE_RENDER:
        try:
            content = open(filename, 'rt', encoding='utf-8').read()
        except FileNotFoundError:
            redirect(URL('index', vars=dict(FLASH_MSG = 'FileNotFoundError')))
        content = convert2html(book_id, content).xml()
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        open(dest, 'wb').write(content)
        content = XML(content)
    else:
        content = XML(open(dest, 'rt', encoding='utf-8').read())
    return dict(title=title, chapter_title=chapter_title, chapters=chapters, content=content, book_id=book_id)



@action("index")
@action.uses("index.html")
def index():
    books={}
    for subfolder in FOLDERS:
        print(subfolder)
        books[subfolder] = ('info_%s' % subfolder,  get_info(subfolder) )

    return dict(books=books, message='hello')


