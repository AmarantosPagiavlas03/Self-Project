#!/bin/bash
set -e
python django_scout/scout_project/manage.py migrate
python django_scout/scout_project/manage.py makesuperuser