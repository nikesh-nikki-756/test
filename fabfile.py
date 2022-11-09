# -*- coding: utf-8 -*-
import uuid
import getpass
from os import path, listdir
from distutils.util import strtobool

import yaml
from fabric.context_managers import lcd, cd
from fabric.contrib import console, files
from fabric.operations import local, put, sudo, run
from fabric.state import env
from fabric.colors import green
from fabric.api import task

CUR_DIR = path.dirname(path.abspath(__file__))
PROJECT_ROOT = path.dirname(CUR_DIR)
SETTINGS = dict()
# DIR name should endswith '/'
REMOTE_PROJECT_DIR = "/opt/"
REMOTE_VIRENV = "/home/ubuntu/af-env/"
REMOTE_USER = "ubuntu"
LOG_PATH = "/var/log/jp_new/"
env.project_name = "jp_new"


@task
def dep(name="test", version="baowan"):
    """choose env name, for example: aliyun
    """
    print("init")
    print(name)
    print(version)
    global SETTINGS
    if version == "vn":
        file_name = "%s/deploy_vn.yaml"
    else:
        file_name = "%s/deploy.yaml"

    setting_file = path.join(CUR_DIR, file_name % name)
    with open(setting_file) as f:
        SETTINGS.update(yaml.safe_load(f))

    env.warn_only = True
    env.colorize_errors = True
    env.key_filename = path.expanduser(SETTINGS["default"].get("key_filename", ""))
    env.need_confirm = SETTINGS["default"].get("need_confirm", True)
    if not env.key_filename and "password" in SETTINGS["default"]:
        env.password = SETTINGS["default"]["password"]


@task
def pro(e, u, p=22):
    """choose project name, for example: ua_new
    """
    if not SETTINGS:
        # load default env
        dep()
    # login_names = SETTINGS.get('default', {})
    # user = login_names.get(getpass.getuser()) if login_names.get(
    #     getpass.getuser()) else login_names.get('user')
    env.service_name = e

    for host in SETTINGS["env"][e]:
        env.hosts.append(u + "@" + host + ":%s" % p)


@task
# @parallel
def deploy(is_restart=True):
    # if not confirm("deploy"):
    #     return

    is_restart = bool(strtobool(str(is_restart)))
    temp_folder = "/tmp/" + str(uuid.uuid4())
    r_temp_folder = "/tmp/" + str(uuid.uuid4())
    local("mkdir %s" % temp_folder)
    project_path = find_path("jp")
    local("cp -r {} {}".format(project_path, temp_folder))

    package_dir = path.join(temp_folder, env.project_name)
    with lcd(package_dir):
        special_env_dct = SETTINGS["env"].get(env.service_name, {}).get(env.host)
        print("special_env_dct", special_env_dct)
        for binfile, commands in special_env_dct.items():
            for command in commands:
                if binfile == "bash" or binfile == "shell":
                    local(command)
                else:
                    local("{} {}".format(binfile, command))

    with lcd(temp_folder):
        local(
            'tar cf {0}.tar.gz --exclude "*.pyc" --exclude=".git" {0}'.format(
                env.project_name
            )
        )
        run("mkdir -p %s" % r_temp_folder)
        put("%s.tar.gz" % package_dir, r_temp_folder)

    get_remote_project_dir = REMOTE_PROJECT_DIR + env.service_name
    with cd(r_temp_folder):
        run("tar xf %s.tar.gz" % env.project_name)
        sudo("rm -r {}/{}-backup".format(get_remote_project_dir, env.project_name))
        sudo(
            "mv {0}/{1} {0}/{1}-backup".format(get_remote_project_dir, env.project_name)
        )
        sudo("mv {} {}".format(env.project_name, get_remote_project_dir))
        sudo("chown -R {} {}".format(REMOTE_USER, get_remote_project_dir))
    sudo("rm -r %s" % r_temp_folder)
    local("rm -rf %s" % temp_folder)
    # restart(env.project_name, is_restart)
    print(env.project_name)

    install_requirements(env.service_name)
    if is_restart:
        print("restarting uwsgi")
        restart(env.service_name)
        print("restarted uwsgi")
    print(green("deploy {}@{} done".format(env.service_name, env.host)))


@task
# @parallel
def restore():
    sudo("rm -r {}/{}".format(REMOTE_PROJECT_DIR, env.project_name))
    sudo("mv {0}/{1}-backup {0}/{1}".format(REMOTE_PROJECT_DIR, env.project_name))
    restart(env.project_name)
    print(green("restore done"))


def confirm(task_name):
    if env.need_confirm:
        if not console.confirm("Are you sure you want to %s" % task_name, default=True):
            return False
    return True


def find_path(project_name):
    current_dir = PROJECT_ROOT
    while current_dir != "/":
        for f in listdir(current_dir):
            if f == project_name and path.isdir(path.join(current_dir, f)):
                return path.dirname(path.join(current_dir, f))
        current_dir = path.dirname(current_dir)
    raise Exception("source folder not found!")


def install_requirements(service_name):
    # sudo("sudo su ubuntu")
    # sudo("pyenv activate ua_new")
    # sudo(
    #     "/home/ubuntu/.pyenv/versions/3.6.2/envs/ua_new/bin/pip install -r /opt/%s/ua_new/jp/requirements.txt" % service_name)

    sudo(
        "/home/ubuntu/.pyenv/versions/3.6.2/envs/jp_new/bin/pip install -r /opt/%s/jp_new/jp/requirements.txt"
        % service_name
    )


def restart(service_name, is_restart=True):
    sudo("kill `ps -ef|grep %s |grep -v grep|awk '{print $2}' `" % (service_name))
    if service_name == "jp_new_admin":
        sudo(
            "kill `ps -ef|grep %s |grep -v grep|awk '{print $2}' `"
            % ("start_timer_task")
        )

        sudo(
            "kill `ps -ef|grep %s |grep -v grep|awk '{print $2}' `"
            % ("start_report_task")
        )
