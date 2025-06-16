from starlette.templating import Jinja2Templates

# make sure this lives in template_env.py
templates = Jinja2Templates(directory="app/templates")