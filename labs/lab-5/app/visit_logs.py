import csv, io, sys

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import current_user

visit_logs_bp = Blueprint('visit_logs', __name__, url_prefix='/logs')


def _get_app_module():
    """Возвращает главный модуль приложения."""
    for name in ('__main__', 'app'):
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, 'db'):
            return mod
    raise RuntimeError('Не удалось найти модуль приложения в sys.modules')


def _require_auth():
    if not current_user.is_authenticated:
        flash('У вас недостаточно прав для доступа к данной странице.', 'warning')
        return redirect(url_for('index'))
    return None


def _require_admin():
    redirect_response = _require_auth()
    if redirect_response:
        return redirect_response
    role_name = current_user.role.name if current_user.role else None
    if role_name != 'Администратор':
        flash('У вас недостаточно прав для доступа к данной странице.', 'warning')
        return redirect(url_for('index'))
    return None


def _get_role_name():
    if current_user.is_authenticated and current_user.role:
        return current_user.role.name
    return None


@visit_logs_bp.route('/')
def index():
    redirect_response = _require_auth()
    if redirect_response:
        return redirect_response

    role_name = _get_role_name()
    if role_name not in ('Администратор', 'Пользователь'):
        flash('У вас недостаточно прав для доступа к данной странице.', 'warning')
        return redirect(url_for('index'))

    m = _get_app_module()
    db, VisitLog = m.db, m.VisitLog

    page = request.args.get('page', 1, type=int)
    per_page = 10

    if role_name == 'Администратор':
        query = VisitLog.query.order_by(VisitLog.created_at.desc())
    else:
        query = VisitLog.query.filter_by(
            user_id=current_user.id
        ).order_by(VisitLog.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'visit_logs/index.html',
        title='Журнал посещений',
        logs=pagination.items,
        pagination=pagination,
        is_admin=(role_name == 'Администратор')
    )


@visit_logs_bp.route('/pages')
def pages_report():
    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    m = _get_app_module()
    db, VisitLog = m.db, m.VisitLog

    stats = db.session.query(
        VisitLog.path,
        db.func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(
        db.func.count(VisitLog.id).desc()
    ).all()

    return render_template(
        'visit_logs/pages.html',
        title='Отчёт по страницам',
        stats=stats
    )


@visit_logs_bp.route('/pages/export')
def pages_export():
    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    m = _get_app_module()
    db, VisitLog = m.db, m.VisitLog

    stats = db.session.query(
        VisitLog.path,
        db.func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(
        db.func.count(VisitLog.id).desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    for i, row in enumerate(stats, 1):
        writer.writerow([i, row.path, row.count])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=pages_report.csv'
    return response


@visit_logs_bp.route('/users')
def users_report():
    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    m = _get_app_module()
    db, VisitLog, User = m.db, m.VisitLog, m.User

    stats = db.session.query(
        User.last_name,
        User.first_name,
        User.middle_name,
        db.func.count(VisitLog.id).label('count')
    ).outerjoin(User, VisitLog.user_id == User.id).group_by(
        VisitLog.user_id
    ).order_by(
        db.func.count(VisitLog.id).desc()
    ).all()

    return render_template(
        'visit_logs/users.html',
        title='Отчёт по пользователям',
        stats=stats
    )


@visit_logs_bp.route('/users/export')
def users_export():
    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    m = _get_app_module()
    db, VisitLog, User = m.db, m.VisitLog, m.User

    stats = db.session.query(
        User.last_name,
        User.first_name,
        User.middle_name,
        db.func.count(VisitLog.id).label('count')
    ).outerjoin(User, VisitLog.user_id == User.id).group_by(
        VisitLog.user_id
    ).order_by(
        db.func.count(VisitLog.id).desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])
    for i, row in enumerate(stats, 1):
        parts = [row.last_name, row.first_name, row.middle_name]
        full_name = ' '.join(p for p in parts if p) or 'Неаутентифицированный пользователь'
        writer.writerow([i, full_name, row.count])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=users_report.csv'
    return response
