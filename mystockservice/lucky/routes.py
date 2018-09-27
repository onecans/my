def setup_routes(app, handler, project_root):

    router = app.router
    h = handler
    m = h.mw
    t = h.test
    router.add_get('/mw', m, name='mv')
    router.add_post('/mw', m, name='mv')
    router.add_post('/test', t, name='test')
    # router.add_static('/static/', path=str(project_root / 'static'),
    #                   name='static')
