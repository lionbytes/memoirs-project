import sys, os
INTERP = os.path.expanduser("/home/dh_skehbp/venv/bin/python3") ### In terminal, with the environment `venv` activated, type "which python3". The result would be used here.
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())
sys.path.append('public')
from public.app import app as application

if __name__ == '__main__':
    application.run(debug=False)
