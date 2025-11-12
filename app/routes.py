from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, UserForm, ImportForm, TransferForm, LocationForm, EquipmentForm
from app.models import User, Equipment
from flask_login import current_user, login_user, logout_user, login_required
import pandas as pd
from datetime import datetime

@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.is_admin:
        equipments = Equipment.query.all()
    else:
        equipments = Equipment.query.filter_by(responsible_person=current_user.username).all()
    return render_template('index.html', equipments=equipments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    users_list = User.query.all()
    return render_template('users.html', users=users_list)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('add_user'))
        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь уже существует', 'danger')
            return redirect(url_for('add_user'))
        user = User(username=form.username.data, is_admin=(form.is_admin.data == 'True'))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь добавлен', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', form=form, title='Добавить пользователя')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.is_admin.choices = [('False', 'МОЛ'), ('True', 'Администратор')]
    if form.validate_on_submit():
        user.username = form.username.data
        user.is_admin = (form.is_admin.data == 'True')
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Пользователь обновлён', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', form=form, title='Редактировать пользователя')

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя удалить себя', 'danger')
        return redirect(url_for('users'))
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён', 'success')
    return redirect(url_for('users'))

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        try:
            # ЧИТАЕМ С ЗАГОЛОВКАМИ В 1-Й СТРОКЕ (header=0)
            if file.filename.endswith('.xls'):
                df = pd.read_excel(file, engine='xlrd', header=0)
            else:
                df = pd.read_excel(file, engine='openpyxl', header=0)
            
            # ВЫВОДИМ КОЛОНКИ
            print("Колонки:", df.columns.tolist())

            # УДАЛЯЕМ ПРОБЕЛЫ В НАЗВАНИЯХ
            df.columns = df.columns.str.strip()

            # ПРОВЕРЯЕМ НАЛИЧИЕ 'Штрих код'
            if 'Штрих код' not in df.columns:
                flash(f"Колонка 'Штрих код' не найдена! Найдено: {list(df.columns)}", 'danger')
                return redirect(url_for('import_data'))

            # УДАЛЯЕМ ПУСТЫЕ СТРОКИ
            df = df.dropna(subset=['Штрих код'])
            df = df[df['Штрих код'].astype(str).str.strip() != '']
            df = df[df['Штрих код'].astype(str) != 'nan']

            count = 0
            for _, row in df.iterrows():
                barcode = str(row['Штрих код']).strip()
                if not barcode or barcode == 'nan':
                    continue

                mol = str(row.get('МОЛ', '')).strip()
                name = str(row.get('Наименование номенклатуры ИК', '')).strip()
                location = str(row.get('Местонахождение', '')).strip()
                actual_location = str(row.get('Фактическое местоположение', '')).strip()
                status_note = str(row.get('Статус', '')).strip()
                inventory = str(row.get('Инвентарный номер', '')).strip()
                cost = row.get('Стоимость обьекта')

                status = 'списано' if 'списание' in status_note.lower() else 'на балансе'
                final_location = actual_location if actual_location and actual_location != 'nan' else location

                equip = Equipment.query.filter_by(barcode=barcode).first()
                if equip:
                    equip.name = name or equip.name
                    equip.location = final_location or equip.location
                    equip.status = status
                    equip.responsible_person = mol or equip.responsible_person
                    equip.inventory_number = inventory if inventory != 'nan' else equip.inventory_number
                    equip.cost = float(cost) if pd.notna(cost) else equip.cost
                else:
                    equip = Equipment(
                        name=name or 'Без названия',
                        barcode=barcode,
                        location=final_location or '',
                        status=status,
                        responsible_person=mol or '',
                        inventory_number=inventory if inventory != 'nan' else None,
                        cost=float(cost) if pd.notna(cost) else None
                    )
                    db.session.add(equip)
                count += 1

            db.session.commit()
            flash(f'Успешно импортировано {count} записей!', 'success')
        except Exception as e:
            flash(f'Ошибка импорта: {str(e)}', 'danger')
            print("ОШИБКА:", e)
        
        return redirect(url_for('index'))
    
    return render_template('import.html', form=form)
    
@app.route('/equipment/<barcode>')
@login_required
def equipment(barcode):
    equip = Equipment.query.filter_by(barcode=barcode).first_or_404()
    if not current_user.is_admin and equip.responsible_person != current_user.username:
        flash('Нет доступа', 'danger')
        return redirect(url_for('index'))
    return render_template('equipment.html', equip=equip)

@app.route('/transfer_equipment/<int:equip_id>', methods=['GET', 'POST'])
@login_required
def transfer_equipment(equip_id):
    if current_user.is_admin:
        flash('Администраторы не могут передавать', 'danger')
        return redirect(url_for('index'))
    equip = Equipment.query.get_or_404(equip_id)
    if equip.responsible_person != current_user.username:
        flash('Нет доступа', 'danger')
        return redirect(url_for('index'))
    form = TransferForm()
    if form.validate_on_submit():
        new_mol = User.query.filter_by(username=form.new_mol.data).first()
        if not new_mol:
            flash('Такого МОЛ не существует', 'danger')
            return redirect(url_for('transfer_equipment', equip_id=equip_id))
        equip.responsible_person = form.new_mol.data
        db.session.commit()
        flash('Оборудование передано', 'success')
        return redirect(url_for('index'))
    return render_template('transfer.html', form=form, equip=equip)

@app.route('/move_equipment/<int:equip_id>', methods=['GET', 'POST'])
@login_required
def move_equipment(equip_id):
    equip = Equipment.query.get_or_404(equip_id)
    if not current_user.is_admin and equip.responsible_person != current_user.username:
        flash('Нет доступа', 'danger')
        return redirect(url_for('index'))
    form = LocationForm()
    if form.validate_on_submit():
        equip.location = form.new_location.data
        db.session.commit()
        flash('Местоположение обновлено', 'success')
        return redirect(url_for('index'))
    return render_template('move.html', form=form, equip=equip)

@app.route('/edit_equipment/<int:equip_id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(equip_id):
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    equip = Equipment.query.get_or_404(equip_id)
    form = EquipmentForm(obj=equip)
    if form.validate_on_submit():
        equip.name = form.name.data
        equip.barcode = form.barcode.data
        equip.location = form.location.data
        equip.status = form.status.data
        equip.inventory_number = form.inventory_number.data
        equip.cost = form.cost.data
        db.session.commit()
        flash('Оборудование обновлено', 'success')
        return redirect(url_for('index'))
    return render_template('edit_equipment.html', form=form, equip=equip)

@app.route('/delete_equipment/<int:equip_id>')
@login_required
def delete_equipment(equip_id):
    if not current_user.is_admin:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    equip = Equipment.query.get_or_404(equip_id)
    db.session.delete(equip)
    db.session.commit()
    flash('Оборудование удалено', 'success')
    return redirect(url_for('index'))

@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@app.route('/guest_scan')
def guest_scan():
    return render_template('guest_scan.html')

@app.route('/guest_equipment/<barcode>')
def guest_equipment(barcode):
    equip = Equipment.query.filter_by(barcode=barcode).first()
    if not equip:
        flash('Оборудование не найдено', 'danger')
        return redirect(url_for('guest_scan'))
    return render_template('guest_equipment.html', equip=equip)