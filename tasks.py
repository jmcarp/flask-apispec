# -*- coding: utf-8 -*-

from invoke import task, run

@task
def clean():
    run('rm -rf dist')
    run('rm -rf build')
    run('rm -rf flask_apispec.egg-info')

@task
def install():
    run('npm install')
    run('rm -rf flask_apispec/static')
    run('cp -r node_modules/swagger-ui/dist flask_apispec/static')

@task
def publish(test=False):
    """Publish to the cheeseshop."""
    clean()
    install()
    if test:
        run('python setup.py register -r test sdist bdist_wheel', echo=True)
        run('twine upload dist/* -r test', echo=True)
    else:
        run('python setup.py register sdist bdist_wheel', echo=True)
        run('twine upload dist/*', echo=True)
