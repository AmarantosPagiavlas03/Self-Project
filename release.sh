#!/bin/bash
set -e
python djanco_scout/scout_project/manage.py migrate
python djanco_scout/scout_project/manage.py makesuperuser