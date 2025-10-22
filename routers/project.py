'''coderadi'''

# ? Importing libraries
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from extensions import *
from datetime import date, datetime
import base64
import zipfile

# ! Building project router
project = Blueprint('project', __name__, url_prefix='/projects')

# * socket route to delete zip
@socket.on('delete_zip')
def delete_zip(data):
    zip_path = os.path.join(current_app.root_path, 'static', 'public', f'{data['title']}.zip')
    os.remove(zip_path)

# * socket route to export project
@socket.on('export_project')
def export_project(data):    
    try:
        # | Create a new zip file
        file_path = os.path.join(current_app.root_path, 'static', 'public', f'{data['project']['title']}.zip')
        return_path = f"/static/public/{data['project']['title']}.zip"
        project_zip = zipfile.ZipFile(file_path, 'w')

        # | Add content to zip file
        with project_zip as zipf:
            # | Add charts
            for title, encoded_image in data['charts'].items():
                image_data = base64.b64decode(encoded_image.split('base64,')[1])
                zipf.writestr(f'charts/{title}.png', image_data)

            # | Add objectives
            objectives = "\n".join(data['objectives'])
            zipf.writestr('objectives.txt', objectives)

            # | Add tags
            tags = "\n".join(data['tags'])
            zipf.writestr('tags.txt', tags)

            # | Add redirection urls
            urls = "\n".join(data['urls'])
            zipf.writestr('urls.txt', urls)

            # | Add images
            for image in data['images']:
                image_url = image.replace(os.getenv('BASE_URI'), current_app.root_path)
                if (os.path.exists(image_url)):
                    zip_url = os.path.basename(image_url)
                    zipf.write(image_url, f'images/{zip_url}')

            # | Add docs
            for doc in data['docs']:
                doc_url = doc.replace(os.getenv('BASE_URI'), current_app.root_path)
                if (os.path.exists(doc_url)):
                    zip_url = os.path.basename(doc_url)
                    zipf.write(doc_url, f'documents/{zip_url}')

            # | Add README
            readme_content = f"""# {data['project']['title']}
{data['project']['desc']}
---"""
            zipf.writestr('README.md', readme_content)

        # | Get size of zip file
        raw_zip_size = os.path.getsize(file_path)
        zip_size = raw_zip_size / (1024 * 1024)
        return_size = str(round(zip_size, 2)) + " MB"

        socket.emit('export_project_callback', {
            'status': 200,
            'file': return_path,
            'size': return_size
        })

    except:
        socket.emit('exprot_project_callback', {
            'status': 500,
            'file': None,
            'size': "Can't fetch size!"
        })

# * socket route to mark objectives
@socket.on('mark-obj')
def mark_objective(data):
    obj = Objective.query.filter_by(id=data['obj_id']).first()
    project = Project.query.filter_by(id=data['route']).first()
    team = Team.query.filter_by(id=data['team_id']).first()
    total_objectives = Objective.query.filter_by(project_id=project.id).count()

    if not team:
        obj.isdone = True
        db.session.commit()
        update_project_status(project)
        socket.emit('mark-obj-callback', {'status': 200})
        return

    member = Member.query.filter_by(
        mem_id=data['user_id'],
        team_id=team.id
    ).first()

    obj.isdone = True
    obj.doneby = member.id
    db.session.commit()
    update_project_status(project)

    done_objectives = Objective.query.filter_by(
        project_id=project.id,
        doneby=member.id
    ).count()

    member.contribution = round(
        done_objectives / total_objectives * 100,
        1
    )
    db.session.commit()

    socket.emit('mark-obj-callback', {'status': 200})

# * socket route to delete objectives
@socket.on('delete-obj')
def delete_objectives(data):
    obj = Objective.query.filter_by(id=data['obj_id']).first()
    db.session.delete(obj)
    db.session.commit()
    update_project_status(obj.project_id)

    socket.emit('del-obj-callback', {'status': 200})

# * socket route to update project visibility
@socket.on('project-settings')
def update_project_visibility(data):
    project = Project.query.filter_by(id=data['projectId']).first()

    if not project:
        socket.emit('project-settings-callback', {'status': 404})

    project.private = data['private']
    db.session.commit()
    socket.emit('project-settings-callback', {'status': 200})

# | Context Processor
@project.context_processor
def inject_common_vars():
    projects = Project.query.filter_by(created_by=current_user.id)
    all_teams = Team.query.all()
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    teams = []

    active_projects = projects.filter_by(status='active').count()
    completed_projects = projects.filter_by(status='completed').count()
    pending_projects = projects.filter_by(status='pending').count()
    failed_projects = projects.filter_by(status='failed').count()

    notifications = Notification.query.filter(
        or_(
            Notification.recv == 0,
            Notification.recv == current_user.id
        )
    ).all()

    if all_teams:
        for team in all_teams:
            for mem in Member.query.filter_by(team_id=team.id).all():
                if mem.mem_id == current_user.id:
                    teams.append(team)
                    break

    return {
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'pending_projects': pending_projects,
        'failed_projects': failed_projects,
        'total_projects': projects.count(),
        'allteams': teams,
        'notification_count': len(notifications),
        'notifications': notifications,
        'settings': settings,
        'CURRENT_VERSION': CURRENT_VERSION,
        'base_url': os.getenv('BASE_URI')
    }

# & Project route
@project.route('/<int:id>/')
@login_required
def show_project(id):
    project = Project.query.filter_by(id=id).first()
    assets = Asset.query.filter_by(id=id).first()
    docs = Document.query.filter_by(project_id=id).all()

    docs = None if (len(docs) == 0) else docs

    filter = request.args.get('filter')
    refresh_contribution(project)

    if project.team_id:
        team = Team.query.filter_by(id=project.team_id).first()
        member = Member.query.filter_by(
            mem_id=current_user.id,
            team_id=team.id
        ).first() 

        if (not member) and (project.private):
            flash("You can't see this project as it's private.", "error")
            return redirect(url_for('router.dashboard'))

        access = True if (member) else False
        admin = Member.query.filter_by(
            admin=True,
            team_id=team.id
        ).first()

    else:
        admin = User.query.filter_by(id=project.created_by).first()
        
        if (not current_user.id == admin.id) and (project.private):
            flash("You can't see this project as it's private.", "error")
            return redirect(url_for('router.dashboard'))

        team = None
        access = True if (current_user.id == admin.id) else False
        
    adminid = admin.id if (admin != None) else 0
    isadmin = True if current_user.id == admin.id else False
    done_only = (filter == 'done') if (filter) else None
    
    if (done_only in [True, False]):
        objectives = Objective.query.filter_by(
            project_id=project.id,
            isdone=done_only
        ).all()
    
    else:
        objectives = Objective.query.filter_by(
            project_id=project.id,
        ).all()

    completed_obj = Objective.query.filter_by(
        project_id=project.id,
        isdone=True
    ).count()
    
    incomplete_obj = Objective.query.filter_by(
        project_id=project.id,
        isdone=False
    ).count()

    return render_template('pages/project.html', data={
        'project': project,
        'team': team,
        'objectives': objectives,
        'assets': {
            'images': assets,
            'docs': docs
        },
        'objectives_overview': {
            'completed': completed_obj if completed_obj > 0 else 0,
            'incomplete': incomplete_obj if incomplete_obj > 0 else 0,
        },
        'admin': {
            'id': adminid,
            'is_admin': isadmin,
        },
        'access': access,
        'size': 10
    })

# & Project settings route
@project.route('/<int:id>/settings/')
@login_required
def project_settings(id):
    project = Project.query.filter_by(id=id).first()
    assets = Asset.query.filter_by(id=id).first()
    docs = Document.query.filter_by(project_id=id).all()
    
    if (len(docs) == 0): docs = None
    if (not current_user.id == project.created_by):
        abort(404)

    memberships = Member.query.filter_by(mem_id=current_user.id).all()
    selected_team = None

    teams_ids = [
        Team.query.filter_by(id=membership.team_id).first().id 
        for membership in memberships
    ]

    if project.team_id:
        selected_team = Team.query.filter_by(id=project.team_id).first()
        teams_ids.remove(selected_team.id)

    teams = [
        Team.query.filter_by(id=team_id).first() 
        for team_id in teams_ids
    ]

    return render_template('pages/project-settings.html', data={
        'project': project,
        'teams': teams,
        'selected_team': selected_team,
        'assets': assets,
        'docs': docs 
    })

# & Update project settings route
@project.route('/<int:id>/settings/update/<category>', methods=['POST'])
@login_required
def update_project_settings(id, category):
    project = Project.query.filter_by(id=id).first()

    if (category == 'basic'):
        project.title = request.form.get('title')
        project.desc = request.form.get('desc', "")
        project.start_date = datetime.strptime(request.form.get('st'), "%Y-%m-%d").date()
        project.end_date = datetime.strptime(request.form.get('en'), "%Y-%m-%d").date()

    elif (category == 'team'):
        project.team_id = int(request.form.get('current_team', 0))

    elif (category == 'assets'):
        assets = Asset.query.filter_by(id=id).first()

        print(request.files.get('cover').filename)

        files = [
            request.files.get('cover'),
            request.files.get('other1'),
            request.files.get('other2'),
            request.files.get('other3'),
            request.files.get('other4'),
        ]

        data_storage = ['cover', 'other1', 'other2', 'other3', 'other4']

        for i, file in enumerate(files):
            if (file):
                path = f'{id}-asset-{i}.png'
                file.save(os.path.join(current_app.root_path, 'static', 'public', path))
                setattr(assets, data_storage[i], f'/static/public/{path}')
                db.session.commit()

    elif (category == 'documents'):
        files = request.files.getlist('files[]')
        app_root = os.path.join(current_app.root_path, 'static', 'public')

        old_files = [file for file in os.listdir(app_root) if file.startswith(f'{id}-doc')]
        i = len(old_files)
        for file in files:
            if (file.filename == ''): continue
            ext = file.filename.split('.')[-1]
            path = f'{id}-doc-{i}.{ext}'
            file.save(os.path.join(app_root, path))

            new_doc = Document(
                project_id=id,
                url=f'/static/public/{path}',
                category=filetype(f".{ext}")
            )

            db.session.add(new_doc)
            db.session.commit()
            i += 1

    elif (category == 'links'):
        url1 = request.form.get('url1', '')
        url2 = request.form.get('url2', '')
        url3 = request.form.get('url3', '')

        project.urls = [url1, url2, url3]

    elif (category == 'icon'):
        icon = request.files.get('icon')

        if (icon):
            path = f'{project.id}-icon.png'
            icon.save(os.path.join(current_app.root_path, 'static', 'public', path))
            project.icon = f"/static/public/{path}"

    elif (category == 'tags'):
        tag1 = request.form.get('tag1', '')
        tag2 = request.form.get('tag2', '')
        tag3 = request.form.get('tag3', '')

        project.tags = [tag1, tag2, tag3]

    db.session.commit()
    flash("Project settings has been updated.", 'success')
    return redirect(url_for('project.project_settings', id=id))

# & New project route
@project.route('/new', methods=['POST'])
@login_required
def add_new_project():
    title = request.form.get('title', 'Untitled project')
    desc = request.form.get('desc', "")
    team = request.form.get('team')
    st = datetime.strptime(request.form.get('st'), "%Y-%m-%d").date()
    en = datetime.strptime(request.form.get('en'), "%Y-%m-%d").date()

    team = int(team) if team else None

    new_project = Project(
        created_by=current_user.id,
        title=title,
        desc=desc,
        team_id=team,
        start_date=st,
        end_date=en,
    )

    db.session.add(new_project)
    db.session.commit()
    new_asset = Asset(id=new_project.id)
    db.session.add(new_asset)
    db.session.commit()

    update_project_status(new_project)
    flash("New project has been created.", "success")
    return redirect(url_for('project.show_project', id=new_project.id))

# & Delete project route
@project.route('/delete')
@login_required
def delete_project():
    project_id = int(request.args.get('project-id', 0))
    
    try:
        # Delete project objectives
        for objective in Objective.query.filter_by(project_id=project_id).all():
            db.session.delete(objective)
            db.session.commit()

        # Delete project assets
        asset = Asset.query.filter_by(id=id).first()
        db.session.delete(asset)
        db.session.commit()

        # Delete project docuements
        for doc in Document.query.filter_by(project_id=id).all():
            db.session.delete(doc)
            os.remove(doc.url)
            db.session.commit()

        # Delete project data
        project = Project.query.filter_by(id=project_id).first()
        db.session.delete(project)
        db.session.commit()
        
        flash("The project has been deleted.", "success")
        return redirect(url_for('router.dashboard'))
    
    except:
        flash("Something went wrong.", "error")
        return redirect(url_for('router.dashboard'))

# & New objective route
@project.route('/<int:id>/objectives/new', methods=['POST'])
@login_required
def new_objective(id):
    current_project = Project.query.filter_by(id=id).first()
    current_project.status = 'active'
    obj = request.form.get('obj')
    obj_file = request.files.get('obj-file')

    for task in obj.split("\n"):
        if (task):
            db.session.add(Objective(
                project_id=id,
                task=task.removesuffix('\r')
            ))
            db.session.commit()

    file_tasks = obj_file.read().decode('utf-8')
    for task in file_tasks.split("\n"):
        if (task):
            db.session.add(Objective(
                project_id=id,
                task=task.removesuffix('\r')
            ))
            db.session.commit()
    
    update_project_status(current_project)
    flash("Objectives have been added to your project.", "success")
    return redirect(url_for('project.show_project', id=id))