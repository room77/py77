print 'gen_makefile hook'

import os

# include makefile templates
src_root = os.environ['R77_SRC_ROOT']
templates_glob = os.path.join(src_root, 'pylib/flash/Makefile.template.*')
datas = [(templates_glob, '.')]
