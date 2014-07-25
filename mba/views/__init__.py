
def includeme(config):
    #be first?
    config.include('mba.views.view')

    config.include('mba.views.form')

    config.include('mba.views.index')
    config.include('mba.views.home')


    config.include('mba.views.meetups')
    config.include('mba.views.meetup')
    config.include('mba.views.review')

    config.include('mba.views.login')
    #config.include('mba.views.logout')

    config.include('mba.views.register')
    config.include('mba.views.col_test')
    config.include('mba.views.resume')
    config.include('mba.views.job')
    config.include('mba.views.resume_edit')
    config.include('mba.views.resume_preview')
    config.include('mba.views.activity')
    #reimplement the content templates
    config.include('mba.views.content')
    config.include('mba.views.image')

    config.include('mba.views.admin')
