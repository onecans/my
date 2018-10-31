from .views import routes


def setup_routes(app, project_root):
    router = app.router

    router.add_routes(routes)
