print('templates hook')

import os

# include templates
hiddenimports = ['jinja2.ext']
src_root = os.environ['R77_SRC_ROOT']
templates_glob = os.path.join(src_root, 'pylib/mail/templates/*')
datas = [(templates_glob, 'templates')]
