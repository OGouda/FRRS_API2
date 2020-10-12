import os

try:
    os.system('python manage.py db upgrade')
    os.system('python manage.py db init')
    os.system('python manage.py db migrate')
except:
    pass
os.system('python manage.py runserver')


